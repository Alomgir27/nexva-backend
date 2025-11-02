from fastapi import WebSocket
from starlette.websockets import WebSocketState
import json
import base64
import asyncio
import re
from io import BytesIO
from pydub import AudioSegment
import search
import models
import httpx
from neural_tts_service import neural_tts

OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

CODE_INDICATORS = ['```', 'function', 'class ', 'def ', 'import ', 'const ', 'return ', 'async ', 'SELECT ']
CODE_KEYWORDS = ['code', 'example', 'how to', 'tutorial', 'syntax', 'implement']

async def safe_send_json(ws: WebSocket, data: dict) -> bool:
    if ws.client_state != WebSocketState.CONNECTED:
        return False
    try:
        await ws.send_json(data)
        return True
    except:
        return False

def is_code_related(query: str, results: list) -> bool:
    if any(kw in query.lower() for kw in CODE_KEYWORDS):
        return True
    for result in (results or [])[:2]:
        content = result.get('content', '')[:1000]
        if sum(1 for ind in CODE_INDICATORS if ind in content) >= 3:
            return True
    return False

def clean_text_for_tts(text: str) -> str:
    replacements = [
        (r'```[\s\S]*?```', ' Here is a code example. '),
        (r'`[^`]+`', ' code snippet '),
        (r'https?://[^\s]+', ' link '),
        (r'www\.[^\s]+', ' website '),
        (r'\*\*([^*]+)\*\*', r'\1'),
        (r'\*([^*]+)\*', r'\1'),
        (r'__([^_]+)__', r'\1'),
        (r'_([^_]+)_', r'\1'),
        (r'\s+', ' ')
    ]
    cleaned = text
    for pattern, repl in replacements:
        cleaned = re.sub(pattern, repl, cleaned)
    for char in ['|', '>', '<', '&nbsp;']:
        cleaned = cleaned.replace(char, ' ')
    return cleaned.strip()

async def generate_and_send_audio(ws: WebSocket, text: str, voice_id: str):
    try:
        cleaned_text = clean_text_for_tts(text.strip())
        if not cleaned_text or len(cleaned_text) < 5:
            return
        
        print(f"🎵 TTS: '{cleaned_text[:50]}...' ({len(cleaned_text)} chars)")
        
        audio_data = await neural_tts.generate_speech_async(cleaned_text, voice=voice_id, language="en")
        
        audio = AudioSegment.from_wav(BytesIO(audio_data))
        audio = audio.speedup(playback_speed=1.15).set_channels(1)
        output = BytesIO()
        audio.export(output, format="wav")
        audio_bytes = output.getvalue()
        
        await safe_send_json(ws, {
            "type": "audio_chunk",
            "audio": base64.b64encode(audio_bytes).decode(),
            "format": "wav"
        })
        print(f"✅ Audio sent ({len(audio_bytes)} bytes)")
    except Exception as e:
        print(f"⚠️ TTS error: {e}")

def build_context(results: list, query: str) -> str:
    if not results:
        return ""
    limit = None if is_code_related(query, results) else 1000
    parts = []
    for i, result in enumerate(results[:2]):
        content = result.get('content', '')
        if limit:
            content = content[:limit]
        parts.append(f"Source {i+1}:\n{content}")
    return "\n\n".join(parts)

def create_system_prompt(chatbot_name: str, context: str) -> str:
    return f"""You are a helpful AI assistant for {chatbot_name}. 
Your primary purpose is to answer questions specifically about {chatbot_name} and its related services.
Answer user questions based ONLY on the provided context from the knowledge base.
If the context doesn't contain relevant information, politely say you don't have that information in your knowledge base.
If asked about unrelated topics, politely redirect the conversation back to {chatbot_name}.
Keep responses concise and natural for voice conversation (2-3 sentences max).

Context from knowledge base:
{context if context else "No relevant context found in the knowledge base."}"""

async def handle_tts_chunk(ws: WebSocket, buffer: str, voice_id: str):
    await generate_and_send_audio(ws, buffer, voice_id)

async def handle_voice_chat(websocket: WebSocket, api_key: str):
    await websocket.accept()
    db = models.SessionLocal()
    interrupt_flag = {"interrupted": False}
    current_task = None
    
    try:
        chatbot = db.query(models.Chatbot).filter(models.Chatbot.api_key == api_key).first()
        if not chatbot:
            await safe_send_json(websocket, {"type": "error", "message": "Invalid API key"})
            await websocket.close()
            return
        
        print(f"🎙️ Voice chat: {chatbot.name} (ID: {chatbot.id})")
        
        domain_ids = [d.id for d in db.query(models.Domain).filter(models.Domain.chatbot_id == chatbot.id).all()]
        
        if not domain_ids:
            await safe_send_json(websocket, {
                "type": "error",
                "message": f"No domains found for chatbot '{chatbot.name}'. Please add and scrape domains first."
            })
            print(f"⚠️ No domains for chatbot {chatbot.id}")
        else:
            print(f"📚 Chatbot has {len(domain_ids)} domain(s)")
        
        async for message in websocket.iter_text():
            if websocket.client_state != WebSocketState.CONNECTED:
                break
            data = json.loads(message)
            if data.get("type") == "text_query":
                query = data.get("text", "").strip()
                if query:
                    if current_task and not current_task.done():
                        print("🛑 Cancelling previous task")
                        current_task.cancel()
                        try:
                            await current_task
                        except asyncio.CancelledError:
                            pass
                    
                    interrupt_flag["interrupted"] = False
                    current_task = asyncio.create_task(
                        process_query(websocket, query, chatbot, domain_ids, db, interrupt_flag)
                    )
            elif data.get("type") == "interrupt":
                print("🛑 Interrupt received from frontend")
                interrupt_flag["interrupted"] = True
            elif data.get("type") == "stop":
                break
    
    except Exception as e:
        if "disconnect" not in str(e).lower():
            print(f"❌ Error: {e}")
        await safe_send_json(websocket, {"type": "error", "message": str(e)})
    finally:
        if current_task and not current_task.done():
            current_task.cancel()
        db.close()
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.close()
            except:
                pass

async def process_query(websocket: WebSocket, text_query: str, chatbot, domain_ids: list, db, interrupt_flag: dict):
    if websocket.client_state != WebSocketState.CONNECTED:
        return
    
    try:
        print(f"💬 Query: '{text_query}'")
        
        # Search with async embedding
        results = await search.search_chatbot_content(chatbot.id, text_query, max_results=5)
        print(f"🔍 Found {len(results) if results else 0} results")
        
        context = build_context(results or [], text_query)
        prompt = create_system_prompt(chatbot.name, context)
        
        await safe_send_json(websocket, {"type": "response_start"})
        
        buffer = ""
        display_buffer = ""
        voice_id = getattr(chatbot, 'voice_id', 'female-1')
        print(f"🎤 Using voice: {voice_id}")
        print(f"🤖 Starting LLM stream...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", OLLAMA_API, 
                json={"model": OLLAMA_MODEL, "prompt": f"{prompt}\n\nUser question: {text_query}", "stream": True}
            ) as response:
                async for line in response.aiter_lines():
                    if interrupt_flag["interrupted"]:
                        print("🛑 Processing interrupted by user")
                        return
                    
                    if websocket.client_state != WebSocketState.CONNECTED:
                        return
                    if not line:
                        continue
                    
                    chunk = json.loads(line).get("response", "")
                    buffer += chunk
                    display_buffer += chunk
                    
                    # Send text to UI immediately
                    if not await safe_send_json(websocket, {"type": "text_chunk", "text": chunk}):
                        return
                    
                    has_paragraph = display_buffer.count('. ') >= 2 or '\n\n' in display_buffer
                    is_long = len(display_buffer) > 200
                    
                    if (has_paragraph or is_long) and len(display_buffer.strip()) > 50:
                        if interrupt_flag["interrupted"]:
                            return
                        asyncio.create_task(handle_tts_chunk(websocket, display_buffer, voice_id))
                        display_buffer = ""
        
        if not interrupt_flag["interrupted"] and len(display_buffer.strip()) > 5:
            asyncio.create_task(generate_and_send_audio(websocket, display_buffer, voice_id))
        
        if not interrupt_flag["interrupted"]:
            await safe_send_json(websocket, {"type": "response_end"})
            print("✅ Response complete\n")
        else:
            print("🛑 Response cancelled by interrupt\n")
    
    except Exception as e:
        if "disconnect" not in str(e).lower():
            print(f"❌ Error: {e}")
        await safe_send_json(websocket, {"type": "error", "message": f"Processing error: {str(e)}"})
