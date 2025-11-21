from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import httpx
from app.core.config import settings

ES_HOST = "http://localhost:9200"
es = Elasticsearch([ES_HOST], headers={"accept": "application/json", "content-type": "application/json"})

import threading

_embedding_model = None
_model_lock = threading.Lock()

def get_embedding_model():
    global _embedding_model
    
    if _embedding_model is not None:
        return _embedding_model
        
    with _model_lock:
        # Double-check pattern
        if _embedding_model is None:
            print("📦 Loading embedding model (BAAI/bge-small-en-v1.5)... This may take a moment.")
            try:
                # Set a specific cache folder if needed, or rely on default
                _embedding_model = SentenceTransformer('BAAI/bge-small-en-v1.5')
                print("✅ Embedding model loaded successfully")
            except Exception as e:
                print(f"❌ Failed to load embedding model: {e}")
                raise e
                
    return _embedding_model
def init_elasticsearch():
    try:
        if es.ping():
            print(f"✅ Connected to Elasticsearch at {ES_HOST}")
        else:
            print(f"⚠️  Could not connect to Elasticsearch at {ES_HOST}")
    except Exception as e:
        print(f"❌ Elasticsearch connection error: {e}")


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
    # print(f"✅ Indexed: {content_data.get('title', 'Untitled')} (chatbot {chatbot_id})")

def generate_content_tags(title: str, content: str) -> list:
    """Generate simple keyword tags from title and content"""
    # Simple keyword extraction - just get important words
    import re
    
    # Combine title and content
    text = f"{title} {content}".lower()
    
    # Remove special characters
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    # Common words to filter out
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'}
    
    # Get words
    words = text.split()
    
    # Filter and count
    word_freq = {}
    for word in words:
        if word and len(word) > 2 and word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and get top 10
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    tags = [word for word, freq in sorted_words[:10]]
    
    return tags

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



async def search_chatbot_content(chatbot_id: int, query: str, max_results: int = 5):
    index_name = get_chatbot_index(chatbot_id)
    
    try:
        model = get_embedding_model()
        query_embedding = model.encode(query, show_progress_bar=False).tolist()
        
        # Generic multi-strategy search that works for ALL queries
        search_clauses = [
            # 1. Semantic vector search - understands meaning regardless of exact words
            {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": query_embedding}
                    },
                    "boost": 0.7  # Primary search method
                }
            },
            # 2. Best fields match - finds documents where query terms appear together
            {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "content"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                    "boost": 0.2
                }
            },
            # 3. Cross fields match - finds query terms across title and content
            {
                "multi_match": {
                    "query": query,
                    "fields": ["title", "content"],
                    "type": "cross_fields",
                    "operator": "or",
                    "boost": 0.1
                }
            }
        ]
        
        results = es.search(
            index=index_name,
            query={
                "bool": {
                    "should": search_clauses,
                    "minimum_should_match": 1
                }
            },
            size=max_results * 3  # Get more to filter duplicates
        )
        
        # Remove duplicates and prepare results
        seen = set()
        unique_results = []
        
        for hit in results["hits"]["hits"]:
            source = hit["_source"]
            source.pop('embedding', None)
            
            # Add score for debugging
            source['_search_score'] = hit['_score']
            
            key = (source.get("url"), source.get("chunk_index"))
            if key not in seen:
                seen.add(key)
                unique_results.append(source)
                if len(unique_results) >= max_results:
                    break
        
        # Log search results for debugging
        if unique_results:
            scores = [round(r.get('_search_score', 0), 2) for r in unique_results[:3]]
            print(f"🔍 Search '{query}' → Found {len(unique_results)} results (scores: {scores})")
        else:
            print(f"⚠️  Search '{query}' → No results found in index '{index_name}'")
            # Check if index has any data
            try:
                count = es.count(index=index_name)
                print(f"📊 Index '{index_name}' has {count['count']} total documents")
            except:
                pass
        
        return unique_results
    except Exception as e:
        print(f"❌ Search error: {e}")
        import traceback
        traceback.print_exc()
        return []

def cleanup_demo_data():
    try:
        es.indices.delete(index="products", ignore=[404])
        print("✅ Removed products index")
    except Exception as e:
        print(f"⚠️  Could not remove products index: {e}")

