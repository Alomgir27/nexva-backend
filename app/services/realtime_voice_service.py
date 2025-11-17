from fastapi import WebSocket
from starlette.websockets import WebSocketState
import json
import base64
import asyncio
import re
from io import BytesIO
from pydub import AudioSegment
from app.services import search
from app import database
import httpx
from app.services.neural_tts_service import neural_tts

OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

CODE_INDICATORS = ['```', 'function', 'class ', 'def ', 'import ', 'const ', 'return ', 'async ', 'SELECT ']
CODE_KEYWORDS = ['code', 'example', 'how to', 'tutorial', 'syntax', 'implement']

VOICE_SEARCH_RESULT_LIMIT = 4
VOICE_CONTEXT_RESULT_LIMIT = 2
STANDARD_CONTEXT_CHARS = 600
CODE_CONTEXT_CHARS = 1600
TTS_SENTENCE_TRIGGER = 1
TTS_CHAR_TRIGGER = 140
MIN_TTS_TEXT_LENGTH = 40

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

def _limit_text(text: str, limit: int) -> str:
    if limit and len(text) > limit:
        return text[:limit]
    return text

def _should_send_tts(buffer: str) -> bool:
    if not buffer:
        return False
    if buffer.count('. ') >= TTS_SENTENCE_TRIGGER:
        return True
    if '\n\n' in buffer:
        return True
    return len(buffer) >= TTS_CHAR_TRIGGER

async def generate_and_send_audio(ws: WebSocket, text: str, voice_id: str):
    try:
        print(f"🎵 TTS: '{text[:80]}...' ({len(text)} chars)")
        audio_data = await neural_tts.generate_speech_async(text, voice=voice_id, language="en")
        
        audio = AudioSegment.from_wav(BytesIO(audio_data))
        audio = audio.speedup(playback_speed=1.15).set_channels(1)
        
        output = BytesIO()
        audio.export(output, format="wav")
        
        await safe_send_json(ws, {
            "type": "audio_chunk",
            "audio": base64.b64encode(output.getvalue()).decode(),
            "format": "wav"
        })
        print(f"✅ Audio sent: {len(output.getvalue())} bytes")
    except Exception as e:
        print(f"⚠️ TTS error: {e}")

def build_context(results: list, query: str) -> str:
    if not results:
        return ""
    limit = CODE_CONTEXT_CHARS if is_code_related(query, results) else STANDARD_CONTEXT_CHARS
    parts = []
    for i, result in enumerate(results[:VOICE_CONTEXT_RESULT_LIMIT]):
        content = result.get('content', '')
        content = _limit_text(content, limit)
        parts.append(f"Source {i+1}:\n{content}")
    return "\n\n".join(parts)

def create_system_prompt(chatbot_name: str, context: str) -> str:
    return f"""You are a helpful AI assistant for {chatbot_name}.
Only answer with information from the knowledge base context.
If nothing relevant is provided, clearly say that the knowledge base does not contain that information.
Keep responses under 60 words (ideally 1-2 sentences) so they sound natural in voice.

Context from knowledge base:
{context if context else "No relevant context found in the knowledge base."}"""

async def handle_tts_chunk(ws: WebSocket, buffer: str, voice_id: str):
    text = clean_text_for_tts(buffer.strip())
    if text and len(text) > 5:
        await generate_and_send_audio(ws, text, voice_id)

async def handle_voice_chat(websocket: WebSocket, api_key: str):
    await websocket.accept()
    db = database.SessionLocal()
    interrupt_flag = {"interrupted": False}
    current_task = None
    
    try:
        chatbot = db.query(database.Chatbot).filter(database.Chatbot.api_key == api_key).first()
        if not chatbot:
            await safe_send_json(websocket, {"type": "error", "message": "Invalid API key"})
            await websocket.close()
            return
        
        print(f"🎙️ Voice chat: {chatbot.name} (ID: {chatbot.id})")
        
        domain_ids = [d.id for d in db.query(database.Domain).filter(database.Domain.chatbot_id == chatbot.id).all()]
        
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
        refined_query = await search.extract_search_keywords(text_query)
        search_query = refined_query or text_query
        results = await search.search_chatbot_content(chatbot.id, search_query, max_results=VOICE_SEARCH_RESULT_LIMIT)
        print(f"🔍 Found {len(results) if results else 0} results")
        
        context = build_context(results or [], text_query)
        prompt = create_system_prompt(chatbot.name, context)
        
        await safe_send_json(websocket, {"type": "response_start"})
        
        buffer = ""
        voice_id = getattr(chatbot, 'voice_id', 'female-1')
        print(f"🎤 Using voice: {voice_id}")
        
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
                    
                    if not await safe_send_json(websocket, {"type": "text_chunk", "text": chunk}):
                        return
                    
                    if _should_send_tts(buffer) and len(buffer.strip()) > MIN_TTS_TEXT_LENGTH:
                        if interrupt_flag["interrupted"]:
                            print("🛑 Processing interrupted before TTS")
                            return
                        print(f"🎯 Sending TTS chunk ({len(buffer)} chars, sentences: {buffer.count('. ')})")
                        await handle_tts_chunk(websocket, buffer, voice_id)
                        buffer = ""
        
        if not interrupt_flag["interrupted"] and len(buffer.strip()) > MIN_TTS_TEXT_LENGTH:
            text = clean_text_for_tts(buffer.strip())
            if text and len(text) > MIN_TTS_TEXT_LENGTH:
                await generate_and_send_audio(websocket, text, voice_id)
        
        if not interrupt_flag["interrupted"]:
            await safe_send_json(websocket, {"type": "response_end"})
            print("✅ Response complete\n")
        else:
            print("🛑 Response cancelled by interrupt\n")
    
    except Exception as e:
        if "disconnect" not in str(e).lower():
            print(f"❌ Error: {e}")
        await safe_send_json(websocket, {"type": "error", "message": f"Processing error: {str(e)}"})

