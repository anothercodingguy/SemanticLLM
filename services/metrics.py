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
            redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        else:
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
        print(f"Failed to record metrics in Redis: {e}")

async def get_metrics_summary() -> dict:
    """
    Query Redis and return a consolidated dict of metrics.
    """
    client = get_redis_client()
    try:
        # Fetch aggregates
        total_saved = float(await client.get("gateway_metric:total_cost_saved") or 0.0)
        total_spent = float(await client.get("gateway_metric:total_cost_spent") or 0.0)
        total_requests = int(await client.get("gateway_metric:total_requests") or 0)
        cache_hits = int(await client.get("gateway_metric:cache_hits") or 0)
        total_latency = float(await client.get("gateway_metric:total_latency") or 0.0)
        
        # Calculate rates
        hit_rate = (cache_hits / total_requests) * 100 if total_requests > 0 else 0.0
        avg_latency = total_latency / total_requests if total_requests > 0 else 0.0
        
        # Fetch last 20 queries from list
        raw_queries = await client.lrange("gateway_queries", 0, 19)
        queries = [json.loads(q) for q in raw_queries]
        
        return {
            "total_saved": total_saved,
            "total_spent": total_spent,
            "total_requests": total_requests,
            "cache_hits": cache_hits,
            "hit_rate": hit_rate,
            "avg_latency": avg_latency,
            "queries": queries
        }
    except Exception as e:
        print(f"Failed to fetch metrics from Redis: {e}")
        return {
            "total_saved": 0.0,
            "total_spent": 0.0,
            "total_requests": 0,
            "cache_hits": 0,
            "hit_rate": 0.0,
            "avg_latency": 0.0,
            "queries": []
        }
