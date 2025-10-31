import httpx
import asyncio
import json
from typing import List, Dict, AsyncGenerator
import search

OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:3b"

class ChatService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def get_context(self, chatbot_id: int, query: str) -> str:
        results = await search.search_chatbot_content(chatbot_id, query, max_results=5)
        
        if not results:
            return ""
        
        context_parts = []
        for result in results:
            content = result.get('content', '')
            title = result.get('title', 'Untitled')
            url = result.get('url', '')
            
            context_parts.append(f"[{title}]\nSource: {url}\n{content}")
        
        return "\n\n---\n\n".join(context_parts)
    
    async def stream_chat(
        self,
        chatbot_id: int,
        message: str,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        context = await self.get_context(chatbot_id, message)
        
        if context:
            system_prompt = f"""You are a helpful AI assistant. Answer questions naturally and directly using the context provided below. 

Guidelines:
- Provide clear, concise answers
- When relevant information includes URLs or links, always include them in your response
- Format your responses with markdown for better readability (use **bold**, lists, code blocks when appropriate)
- If the user asks for links or resources, provide them
- Be conversational and friendly
- Never mention "context", "information provided", or "according to" - just answer confidently

Context:
{context}"""
        else:
            system_prompt = """You are a helpful AI assistant. 

Guidelines:
- Provide clear, helpful responses
- Format your responses with markdown for better readability
- If you don't have specific information, be honest and suggest where the user might find it
- Be conversational and friendly
- If appropriate, suggest checking the official website or documentation"""
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": message})
        
        try:
            async with self.client.stream(
                'POST',
                f"{OLLAMA_HOST}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": True
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            import json
                            data = json.loads(line)
                            if 'message' in data and 'content' in data['message']:
                                yield data['message']['content']
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"Error: {str(e)}"
    
    async def close(self):
        await self.client.aclose()

chat_service = ChatService()

