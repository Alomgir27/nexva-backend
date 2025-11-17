from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import httpx
from app.core.config import settings

ES_HOST = "http://localhost:9200"
es = Elasticsearch([ES_HOST], headers={"accept": "application/json", "content-type": "application/json"})

_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        print("📦 Loading embedding model (all-MiniLM-L6-v2)...")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model loaded")
    return _embedding_model

def init_elasticsearch():
    pass

def get_chatbot_index(chatbot_id: int) -> str:
    return f"chatbot-{chatbot_id}"

def init_chatbot_index(chatbot_id: int):
    index_name = get_chatbot_index(chatbot_id)
    try:
        es.indices.get(index=index_name)
    except:
        es.indices.create(
            index=index_name,
            settings={
                "analysis": {
                    "analyzer": {
                        "english_light": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "english_possessive_stemmer", "light_english_stemmer"]
                        }
                    },
                    "filter": {
                        "english_possessive_stemmer": {
                            "type": "stemmer",
                            "name": "possessive_english"
                        },
                        "light_english_stemmer": {
                            "type": "stemmer",
                            "name": "light_english"
                        }
                    }
                }
            },
            mappings={
                "properties": {
                    "url": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "english_light"
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "english_light"
                    },
                    "chunk_index": {"type": "integer"},
                    "chatbot_id": {"type": "integer"},
                    "tags": {"type": "keyword"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 384,
                        "index": True,
                        "similarity": "cosine"
                    }
                }
            }
        )

def index_chatbot_content(chatbot_id: int, content_data: dict):
    index_name = get_chatbot_index(chatbot_id)
    init_chatbot_index(chatbot_id)
    
    model = get_embedding_model()
    text_to_embed = f"{content_data.get('title', '')} {content_data.get('content', '')}"
    embedding = model.encode(text_to_embed, show_progress_bar=False).tolist()
    
    content_data['embedding'] = embedding
    es.index(index=index_name, document=content_data)

def generate_content_tags(title: str, content: str) -> list:
    try:
        sample = content[:800]
        prompt = f"""Analyze this content and generate 3-5 relevant tags for search categorization.
Tags should be: lowercase, single-word or hyphenated (e.g., "api-docs", "pricing"), relevant for search.

Title: {title}
Content: {sample}

Return ONLY comma-separated tags, nothing else:"""
        
        response = httpx.post(
            f"{settings.OLLAMA_HOST}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 30}
            },
            timeout=8.0
        )
        
        if response.status_code == 200:
            tags_text = response.json().get('response', '').strip()
            tags = [t.strip().lower() for t in tags_text.replace('\n', ',').split(',')]
            tags = [t for t in tags if t and 2 < len(t) < 25 and '-' not in t[0]]
            return tags[:5]
    except Exception as e:
        pass
    return []

async def extract_search_keywords(query: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            prompt = f"""Extract the MAIN TOPIC keywords from this question for searching a knowledge base. Focus on specific nouns and topics, not generic words.

Examples:
- "What is the pricing?" → "pricing plans"
- "How do I customize design?" → "design customization"
- "What payment methods?" → "payment gateway"

Question: {query}

Keywords (2-3 words max):"""
            
            response = await client.post(
                f"{settings.OLLAMA_HOST}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 15
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                keywords = result.get('response', '').strip()
                keywords = keywords.replace('*', '').replace('-', '').replace('"', '').replace('\n', ' ')
                keywords = ' '.join(keywords.split()[:5])
                if keywords and len(keywords) > 2:
                    return keywords
    except Exception as e:
        print(f"Keyword extraction error: {e}")
    
    return query

async def extract_query_tags(query: str) -> list:
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            prompt = f"""Extract 2-3 topic tags from this question. Use lowercase, single words or hyphenated terms.

Examples:
- "What are your pricing plans?" → pricing,plans,subscription
- "How to integrate the API?" → api,integration,setup
- "Do you accept PayPal?" → payment,paypal,checkout

Question: {query}

Tags (comma-separated):"""
            
            response = await client.post(
                f"{settings.OLLAMA_HOST}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 20}
                }
            )
            
            if response.status_code == 200:
                tags_text = response.json().get('response', '').strip()
                tags = [t.strip().lower() for t in tags_text.replace('\n', ',').split(',')]
                return [t for t in tags if t and 2 < len(t) < 20][:3]
    except:
        pass
    return []

async def search_chatbot_content(chatbot_id: int, query: str, max_results: int = 5):
    index_name = get_chatbot_index(chatbot_id)
    
    try:
        model = get_embedding_model()
        query_embedding = model.encode(query, show_progress_bar=False).tolist()
        
        query_tags = await extract_query_tags(query)
        
        search_clauses = [
            {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": query_embedding}
                    },
                    "boost": 0.6
                }
            },
            {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "content"],
                    "fuzziness": "AUTO",
                    "boost": 0.3
                }
            }
        ]
        
        if query_tags:
            search_clauses.append({
                "terms": {"tags": query_tags, "boost": 0.1}
            })
        
        results = es.search(
            index=index_name,
            query={"bool": {"should": search_clauses}},
            size=max_results * 2
        )
        
        seen = set()
        unique_results = []
        for hit in results["hits"]["hits"]:
            source = hit["_source"]
            source.pop('embedding', None)
            
            key = (source.get("url"), source.get("chunk_index"))
            if key not in seen:
                seen.add(key)
                unique_results.append(source)
                if len(unique_results) >= max_results:
                    break
        
        return unique_results
    except Exception as e:
        print(f"Search error: {e}")
        return []

def cleanup_demo_data():
    try:
        es.indices.delete(index="products", ignore=[404])
        print("✅ Removed products index")
    except Exception as e:
        print(f"⚠️  Could not remove products index: {e}")

