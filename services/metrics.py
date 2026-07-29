import json
import logging
from datetime import datetime
from typing import Optional
from core.config import settings

logger = logging.getLogger(__name__)

# ── In-memory metrics store (always available) ──────────────────────────
_in_memory_metrics = {
    "total_saved": 0.0,
    "total_spent": 0.0,
    "total_requests": 0,
    "cache_hits": 0,
    "total_latency_hit": 0.0,
    "total_latency_miss": 0.0,
    "queries": []
}

# ── Redis client (lazy, optional) ───────────────────────────────────────
_redis_client = None
_redis_available = None  # None = not tested yet, True/False after first check


def _try_get_redis_client():
    """
    Attempt to build a Redis client from REDIS_URL.
    Returns the client object or None. Never raises.
    """
    global _redis_client, _redis_available

    # Once we know Redis is unavailable, stop retrying
    if _redis_available is False:
        return None

    if _redis_client is not None:
        return _redis_client

    try:
        url = (settings.REDIS_URL or "").strip()
        if not url or url.lower() in ("none", "null"):
            logger.info("REDIS_URL not configured — using in-memory metrics.")
            _redis_available = False
            return None

        if not url.startswith(("redis://", "rediss://", "unix://")):
            logger.warning(f"REDIS_URL has invalid scheme — using in-memory metrics. URL: {url[:30]}…")
            _redis_available = False
            return None

        import redis.asyncio as aioredis
        _redis_client = aioredis.from_url(url, decode_responses=True)
        _redis_available = True
        logger.info("Redis client created successfully.")
        return _redis_client

    except Exception as e:
        logger.warning(f"Failed to create Redis client ({e}) — using in-memory metrics.")
        _redis_available = False
        return None


async def close_metrics():
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.close()
        except Exception:
            pass


# ── Cost calculation ────────────────────────────────────────────────────
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


# ── Record a metric ────────────────────────────────────────────────────
async def record_metric(
    prompt: str,
    complexity: str,
    model_routed: str,
    is_cache_hit: bool,
    latency_ms: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0
):
    cost = calculate_cost(model_routed, prompt_tokens, completion_tokens)
    cost_saved = cost if is_cache_hit else 0.0
    cost_spent = 0.0 if is_cache_hit else cost

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

    # Always write to in-memory first (guaranteed to work)
    _in_memory_metrics["queries"].insert(0, query_data)
    _in_memory_metrics["queries"] = _in_memory_metrics["queries"][:100]
    _in_memory_metrics["total_saved"] += cost_saved
    _in_memory_metrics["total_spent"] += cost_spent
    _in_memory_metrics["total_requests"] += 1
    if is_cache_hit:
        _in_memory_metrics["cache_hits"] += 1
        _in_memory_metrics["total_latency_hit"] += latency_ms
    else:
        _in_memory_metrics["total_latency_miss"] += latency_ms

    # Then try Redis as a durable backup (optional)
    client = _try_get_redis_client()
    if client:
        try:
            async with client.pipeline(transaction=True) as pipe:
                pipe.lpush("gateway_queries", json.dumps(query_data))
                pipe.ltrim("gateway_queries", 0, 99)
                pipe.incrbyfloat("gateway_metric:total_cost_saved", cost_saved)
                pipe.incrbyfloat("gateway_metric:total_cost_spent", cost_spent)
                pipe.incrby("gateway_metric:total_requests", 1)
                if is_cache_hit:
                    pipe.incrby("gateway_metric:cache_hits", 1)
                    pipe.incrbyfloat("gateway_metric:total_latency_hit", latency_ms)
                else:
                    pipe.incrbyfloat("gateway_metric:total_latency_miss", latency_ms)
                pipe.incrbyfloat("gateway_metric:total_latency", latency_ms)
                await pipe.execute()
        except Exception as e:
            global _redis_available
            _redis_available = False
            logger.warning(f"Redis write failed ({e}) — metrics saved in-memory only.")


# ── Read metrics summary ───────────────────────────────────────────────
async def get_metrics_summary() -> dict:
    """Return metrics from Redis if available, otherwise from in-memory store."""

    # Try Redis first
    client = _try_get_redis_client()
    if client:
        try:
            total_saved = float(await client.get("gateway_metric:total_cost_saved") or 0.0)
            total_spent = float(await client.get("gateway_metric:total_cost_spent") or 0.0)
            total_requests = int(await client.get("gateway_metric:total_requests") or 0)
            cache_hits = int(await client.get("gateway_metric:cache_hits") or 0)
            total_latency_hit = float(await client.get("gateway_metric:total_latency_hit") or 0.0)
            total_latency_miss = float(await client.get("gateway_metric:total_latency_miss") or 0.0)
            raw_queries = await client.lrange("gateway_queries", 0, 19)
            queries = [json.loads(q) for q in raw_queries]

            cache_misses = total_requests - cache_hits
            hit_rate = (cache_hits / total_requests) * 100 if total_requests > 0 else 0.0
            avg_latency_hit = total_latency_hit / cache_hits if cache_hits > 0 else 0.0
            avg_latency_miss = total_latency_miss / cache_misses if cache_misses > 0 else 0.0

            return {
                "total_saved": total_saved,
                "total_spent": total_spent,
                "total_requests": total_requests,
                "cache_hits": cache_hits,
                "hit_rate": hit_rate,
                "avg_latency_hit": avg_latency_hit,
                "avg_latency_miss": avg_latency_miss,
                "queries": queries
            }
        except Exception as e:
            global _redis_available
            _redis_available = False
            logger.warning(f"Redis read failed ({e}) — serving in-memory metrics.")

    # Fallback: always return in-memory data
    total_requests = _in_memory_metrics["total_requests"]
    cache_hits = _in_memory_metrics["cache_hits"]
    cache_misses = total_requests - cache_hits
    hit_rate = (cache_hits / total_requests) * 100 if total_requests > 0 else 0.0
    avg_latency_hit = _in_memory_metrics["total_latency_hit"] / cache_hits if cache_hits > 0 else 0.0
    avg_latency_miss = _in_memory_metrics["total_latency_miss"] / cache_misses if cache_misses > 0 else 0.0

    return {
        "total_saved": _in_memory_metrics["total_saved"],
        "total_spent": _in_memory_metrics["total_spent"],
        "total_requests": total_requests,
        "cache_hits": cache_hits,
        "hit_rate": hit_rate,
        "avg_latency_hit": avg_latency_hit,
        "avg_latency_miss": avg_latency_miss,
        "queries": _in_memory_metrics["queries"][:20]
    }
