import redis.asyncio as redis
import json
from datetime import datetime
from typing import Optional
from core.config import settings

redis_client = None

def get_redis_client():
    global redis_client
    if redis_client is None:
        if settings.REDIS_URL:
            # Support TLS connections via rediss:// if needed
            redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        else:
            # Fallback for local testing
            redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    return redis_client

# Groq pricing (approximate, per million tokens)
PRICING = {
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
}

def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    if model not in PRICING:
        return 0.0
    input_cost = (prompt_tokens / 1_000_000) * PRICING[model]["input"]
    output_cost = (completion_tokens / 1_000_000) * PRICING[model]["output"]
    return input_cost + output_cost

async def record_metric(
    prompt: str,
    complexity: str,
    model_routed: str,
    is_cache_hit: bool,
    latency_ms: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0
):
    cost_spent = 0.0
    cost_saved = 0.0
    
    cost = calculate_cost(model_routed, prompt_tokens, completion_tokens)
    
    if is_cache_hit:
        cost_saved = cost
    else:
        cost_spent = cost

    query_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "prompt": prompt,
        "complexity": complexity,
        "model_routed": model_routed,
        "is_cache_hit": 1 if is_cache_hit else 0,
        "latency_ms": latency_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_saved": cost_saved,
        "cost_spent": cost_spent
    }

    client = get_redis_client()
    try:
        # Pipeline the Redis commands to execute them in a single round-trip
        async with client.pipeline(transaction=True) as pipe:
            pipe.lpush("gateway_queries", json.dumps(query_data))
            pipe.ltrim("gateway_queries", 0, 99)  # Keep the last 100 queries
            
            # Global aggregates
            pipe.incrbyfloat("gateway_metric:total_cost_saved", cost_saved)
            pipe.incrbyfloat("gateway_metric:total_cost_spent", cost_spent)
            pipe.incrby("gateway_metric:total_requests", 1)
            if is_cache_hit:
                pipe.incrby("gateway_metric:cache_hits", 1)
            pipe.incrbyfloat("gateway_metric:total_latency", latency_ms)
            
            await pipe.execute()
    except Exception as e:
        # Log to stdout for Vercel logs, but do not block the user response
        print(f"Failed to record metrics in Redis: {e}")
