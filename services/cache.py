import os
import json
import httpx
import hashlib
import asyncio
import logging
from typing import Optional, Tuple, Dict, Any
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from core.config import settings

logger = logging.getLogger(__name__)

VECTOR_SIZE = 384
COLLECTION_NAME = "semantic_cache"

# Initialize Qdrant client
client: Optional[AsyncQdrantClient] = None
try:
    if settings.QDRANT_URL:
        client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    else:
        client = AsyncQdrantClient(location=":memory:")
except Exception as e:
    logger.warning(f"Qdrant client initialization notice: {e}")
    client = None

# In-memory fast cache and vector fallback
_in_memory_exact_cache: Dict[str, Dict[str, Any]] = {}
_in_memory_vector_cache: list[Dict[str, Any]] = []

# Lazily initialized fastembed model
embedding_model = None

def _run_fastembed(text: str) -> Optional[list[float]]:
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
        logger.warning(f"Local fastembed fallback notice: {e}")
    return None

def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = sum(a * a for a in v1) ** 0.5
    norm_b = sum(b * b for b in v2) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

_collection_initialized = False

async def init_cache():
    """
    Ensure the collection exists in Qdrant.
    """
    global _collection_initialized
    if not client:
        return
    try:
        exists = await client.collection_exists(COLLECTION_NAME)
        if not exists:
            await client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            logger.info("Qdrant collection 'semantic_cache' initialized.")
        _collection_initialized = True
    except Exception as e:
        logger.warning(f"Qdrant collection init notice: {e}")

async def _ensure_cache_ready():
    global _collection_initialized
    if not _collection_initialized and client:
        await init_cache()

async def close_cache():
    """
    Close Qdrant client connection.
    """
    if not client:
        return
    try:
        await client.close()
    except Exception as e:
        logger.warning(f"Failed to close Qdrant client: {e}")

async def get_embedding(text: str) -> Optional[list[float]]:
    """
    Generate 384-dimensional embedding using Hugging Face Inference API or local fastembed.
    """
    if not text or not text.strip():
        return None

    # Try Hugging Face API if HF_API_KEY is present
    if settings.HF_API_KEY:
        headers = {"Authorization": f"Bearer {settings.HF_API_KEY}"}
        payload = {"inputs": text}
        url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
        
        try:
            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(url, headers=headers, json=payload, timeout=4.0)
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
            logger.warning(f"HF embedding API notice, using fastembed: {e}")

    # Fallback to local fastembed (non-blocking thread pool)
    try:
        vector = await asyncio.to_thread(_run_fastembed, text)
        if vector:
            return vector
    except Exception as e:
        logger.warning(f"Local embedding notice: {e}")
        
    return None

async def get_similar_prompt(prompt: str) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    Check if the prompt exists in cache with similarity >= threshold.
    Returns (cached_payload, similarity_score).
    """
    norm_prompt = prompt.strip().lower()

    # 1. Instant exact match check
    if norm_prompt in _in_memory_exact_cache:
        return _in_memory_exact_cache[norm_prompt], 1.0

    # 2. Semantic vector lookup
    vector = await get_embedding(prompt)
    if not vector:
        return None, 0.0

    # Try Qdrant query_points
    if client:
        try:
            await _ensure_cache_ready()
            results = await client.query_points(
                collection_name=COLLECTION_NAME,
                query=vector,
                limit=1
            )
            if results and results.points:
                top_hit = results.points[0]
                score = float(top_hit.score)
                if score >= settings.CACHE_SIMILARITY_THRESHOLD:
                    return top_hit.payload, score
        except Exception as e:
            logger.warning(f"Qdrant query_points notice: {e}")

    # Fallback: in-memory vector cache scan
    best_score = 0.0
    best_payload = None
    for entry in _in_memory_vector_cache:
        sim = _cosine_similarity(vector, entry["vector"])
        if sim > best_score:
            best_score = sim
            best_payload = entry["payload"]

    if best_score >= settings.CACHE_SIMILARITY_THRESHOLD and best_payload is not None:
        return best_payload, best_score

    return None, best_score

async def store_prompt(prompt: str, response_data: Dict[str, Any]):
    """
    Store the prompt and response in vector database and in-memory caches.
    """
    norm_prompt = prompt.strip().lower()
    _in_memory_exact_cache[norm_prompt] = response_data

    vector = await get_embedding(prompt)
    if not vector:
        return

    # In-memory vector backup
    _in_memory_vector_cache.insert(0, {
        "prompt": prompt,
        "vector": vector,
        "payload": response_data
    })
    if len(_in_memory_vector_cache) > 200:
        _in_memory_vector_cache.pop()

    # Qdrant upsert
    if client:
        point_id = int(hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:15], 16)
        try:
            await _ensure_cache_ready()
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
            logger.warning(f"Qdrant upsert notice: {e}")
