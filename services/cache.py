import os
import json
import httpx
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from core.config import settings

VECTOR_SIZE = 384
COLLECTION_NAME = "semantic_cache"

QDRANT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "qdrant_data")

# Initialize client
if settings.QDRANT_URL:
    client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
else:
    client = AsyncQdrantClient(location=":memory:")

async def init_cache():
    """
    Ensure the collection exists in Qdrant.
    """
    try:
        exists = await client.collection_exists(COLLECTION_NAME)
        if not exists:
            await client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
    except Exception as e:
        print(f"Failed to initialize Qdrant collection: {e}")

async def get_embedding(text: str) -> list[float]:
    """
    Generate embedding using Hugging Face Serverless Inference API (all-MiniLM-L6-v2).
    """
    if not settings.HF_API_KEY:
        # Fallback dummy vector
        return [0.0] * VECTOR_SIZE

    headers = {"Authorization": f"Bearer {settings.HF_API_KEY}"}
    payload = {"inputs": text}
    url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
    
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            result = response.json()
            
            def extract_vector(res):
                if isinstance(res, list):
                    if len(res) == 0:
                        return [0.0] * VECTOR_SIZE
                    if isinstance(res[0], float):
                        return res
                    if isinstance(res[0], list):
                        return extract_vector(res[0])
                return [0.0] * VECTOR_SIZE
                
            vector = extract_vector(result)
            if len(vector) < VECTOR_SIZE:
                vector += [0.0] * (VECTOR_SIZE - len(vector))
            return vector[:VECTOR_SIZE]
    except Exception as e:
        print(f"Failed to generate embedding: {e}")
        return [0.0] * VECTOR_SIZE

async def get_similar_prompt(prompt: str) -> dict | None:
    """
    Check if the prompt exists in the cache with similarity >= threshold.
    """
    vector = await get_embedding(prompt)
    
    try:
        hits = await client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=1
        )
        
        if hits and hits[0].score >= settings.CACHE_SIMILARITY_THRESHOLD:
            return hits[0].payload
    except Exception as e:
        print(f"Qdrant search error: {e}")
        
    return None

async def store_prompt(prompt: str, response_data: dict):
    """
    Store the prompt and its response in the vector database.
    """
    vector = await get_embedding(prompt)
    point_id = hash(prompt) % ((1<<63)-1)
    
    try:
        await client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=response_data
                )
            ]
        )
    except Exception as e:
        print(f"Qdrant upsert error: {e}")
