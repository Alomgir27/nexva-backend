import httpx
from typing import List, Dict, AsyncGenerator
from app.services.search import search_chatbot_content
from app.core.config import settings

class ChatService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def get_context(self, chatbot_id: int, query: str) -> str:
        results = await search_chatbot_content(chatbot_id, query, max_results=5)
        
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
                f"{settings.OLLAMA_HOST}/api/chat",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "messages": messages,
                    "stream": True
                }
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield f"Error: Ollama API returned {response.status_code}. Response: {error_text.decode()[:200]}"
                    return
                    
                async for line in response.aiter_lines():
                    if line:
                        try:
                            import json
                            data = json.loads(line)
                            if 'message' in data and 'content' in data['message']:
                                yield data['message']['content']
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError as e:
            yield f"Error: Cannot connect to Ollama at {settings.OLLAMA_HOST}. Make sure Ollama is running. Details: {str(e)}"
        except httpx.ReadTimeout as e:
            yield f"Error: Request to Ollama timed out. The model might be loading or overloaded. Details: {str(e)}"
        except Exception as e:
            yield f"Error: Unexpected error occurred: {str(e)}"
    
    async def close(self):
        await self.client.aclose()

chat_service = ChatService()

