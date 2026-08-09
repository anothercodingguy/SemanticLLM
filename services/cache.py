import os
import json
import httpx
import hashlib
import asyncio
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from core.config import settings

VECTOR_SIZE = 384
COLLECTION_NAME = "semantic_cache"

QDRANT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "qdrant_data")

# Initialize client safely
client = None
try:
    if settings.QDRANT_URL:
        client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    else:
        client = AsyncQdrantClient(location=":memory:")
except Exception as e:
    print(f"Qdrant client initialization notice: {e}")
    client = None

# Lazily initialized fastembed model
embedding_model = None

def _run_fastembed(text: str) -> list[float] | None:
    global embedding_model
    try:
        if embedding_model is None:
            from fastembed import TextEmbedding
            embedding_model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        embeddings_generator = embedding_model.embed([text])
        vector = next(embeddings_generator).tolist()
        if vector and len(vector) >= VECTOR_SIZE:
            return vector[:VECTOR_SIZE]
    except Exception as e:
        print(f"Local fastembed fallback unavailable: {e}")
    return None

async def init_cache():
    """
    Ensure the collection exists in Qdrant.
    """
    if not client:
        return
    try:
        exists = await client.collection_exists(COLLECTION_NAME)
        if not exists:
            await client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
    except Exception as e:
        print(f"Failed to initialize Qdrant collection: {e}")

async def close_cache():
    """
    Close Qdrant client connection.
    """
    if not client:
        return
    try:
        await client.close()
    except Exception as e:
        print(f"Failed to close Qdrant client: {e}")

async def get_embedding(text: str) -> list[float] | None:
    """
    Generate embedding using Hugging Face Serverless Inference API, 
    fallback to fastembed local model if HF API fails or is missing.
    Returns None if embedding cannot be generated.
    """
    # Try Hugging Face first if key is present
    if settings.HF_API_KEY:
        headers = {"Authorization": f"Bearer {settings.HF_API_KEY}"}
        payload = {"inputs": text}
        url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
        
        try:
            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(url, headers=headers, json=payload, timeout=5.0)
                response.raise_for_status()
                result = response.json()
                
                def extract_vector(res):
                    if isinstance(res, list):
                        if len(res) == 0:
                            return None
                        if isinstance(res[0], float):
                            return res
                        if isinstance(res[0], list):
                            return extract_vector(res[0])
                    return None
                    
                vector = extract_vector(result)
                if vector and len(vector) >= VECTOR_SIZE:
                    return vector[:VECTOR_SIZE]
        except Exception as e:
            print(f"HF embedding failed, falling back to local: {e}")

    # Fallback to local fastembed (run in thread to prevent blocking event loop)
    try:
        vector = await asyncio.to_thread(_run_fastembed, text)
        if vector:
            return vector
    except Exception as e:
        print(f"Local embedding failed: {e}")
        
    return None

async def get_similar_prompt(prompt: str) -> dict | None:
    """
    Check if the prompt exists in the cache with similarity >= threshold.
    """
    if not client:
        return None
    vector = await get_embedding(prompt)
    if not vector:
        return None
        
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
    if not client:
        return
    vector = await get_embedding(prompt)
    if not vector:
        return
        
    # Deterministic integer point ID derived from SHA-256 hash of prompt
    point_id = int(hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:15], 16)
    
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

