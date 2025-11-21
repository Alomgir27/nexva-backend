import httpx
from typing import List, Dict, AsyncGenerator
from app.services.search import search_chatbot_content
from app.core.config import settings

class ChatService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def get_context(self, chatbot_id: int, query: str, max_results: int = 5) -> str:
        print(f"[ChatService] Searching for context with query: '{query}' (top_k={max_results})")
        results = await search_chatbot_content(chatbot_id, query, max_results=max_results)
        
        if not results:
            print(f"[ChatService] No context found for query: '{query}'")
            return ""
        
        print(f"[ChatService] Found {len(results)} context chunks")
        context_parts = []
        for i, result in enumerate(results):
            content = result.get('content', '')
            title = result.get('title', 'Untitled')
            url = result.get('url', '')
            score = result.get('_search_score', 0)
            
            print(f"[ChatService] Result {i+1}: '{title}' (score: {score:.2f})")
            context_parts.append(f"[{title}]\nSource: {url}\n{content}")
        
        return "\n\n---\n\n".join(context_parts)
    
    async def stream_chat(
        self,
        chatbot_id: int,
        message: str,
        history: List[Dict[str, str]],
        top_k: int = 5,
        short_answer: bool = False
    ) -> AsyncGenerator[str, None]:
        context = await self.get_context(chatbot_id, message, max_results=top_k)
        
        length_instruction = "Keep your answer very short and concise." if short_answer else "Provide clear, concise answers."
        
        if context:
            system_prompt = f"""You are a helpful AI assistant. You must answer questions strictly using ONLY the context provided below.
            
Guidelines:
- {length_instruction}
- Do NOT use outside knowledge.
- If the exact answer is not in the context, say you don't know, or summarize what IS available related to the topic.
- If the question is vague (e.g. "price"), mention any pricing details found in the context or ask for clarification.
- When relevant information includes URLs or links, always include them in your response.
- Format your responses with markdown for better readability (use **bold**, lists, code blocks when appropriate).
- Never mention "context", "information provided", or "according to" - just answer confidently based on the data.

Context:
{context}"""
        else:
            system_prompt = """You are a helpful AI assistant.
            
Guidelines:
- {length_instruction}
- Since no specific context was found, answer generally but be honest if you don't know.
- Format your responses with markdown for better readability.
- Be conversational and friendly."""
        
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

