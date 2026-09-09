import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from core.config import settings

logger = logging.getLogger(__name__)

# ── Centralized Pricing Model (USD per 1M tokens) ──────────────────────
PRICING = {
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "default": {"input": 0.05, "output": 0.08}
}

def calculate_direct_cost(original_tokens: int, completion_tokens: int) -> float:
    """
    Calculates the uncompressed baseline cost on a full 70B model.
    """
    rate = PRICING["llama-3.3-70b-versatile"]
    input_cost = (original_tokens / 1_000_000.0) * rate["input"]
    output_cost = (completion_tokens / 1_000_000.0) * rate["output"]
    return input_cost + output_cost

def calculate_actual_cost(model: str, optimized_tokens: int, completion_tokens: int, is_cache_hit: bool) -> float:
    """
    Calculates actual API spend for the request.
    If cached, inference spend is effectively $0.00.
    """
    if is_cache_hit:
        return 0.0

    model_key = model if model in PRICING else "default"
    rate = PRICING[model_key]
    input_cost = (optimized_tokens / 1_000_000.0) * rate["input"]
    output_cost = (completion_tokens / 1_000_000.0) * rate["output"]
    return input_cost + output_cost

# ── In-Memory Metrics Store (Guaranteed Zero Downtime) ──────────────────
_in_memory_metrics: Dict[str, Any] = {
    "total_saved": 0.0,
    "total_spent": 0.0,
    "total_requests": 0,
    "cache_hits": 0,
    "total_tokens_in": 0,
    "total_tokens_optimized": 0,
    "total_tokens_saved": 0,
    "total_latency_hit": 0.0,
    "total_latency_miss": 0.0,
    "latest_model_route": "—",
    "queries": []
}

_redis_client = None
_redis_available = None

def _try_get_redis_client():
    global _redis_client, _redis_available
    if _redis_available is False:
        return None
    if _redis_client is not None:
        return _redis_client

    try:
        url = (settings.REDIS_URL or "").strip()
        if not url or url.lower() in ("none", "null"):
            _redis_available = False
            return None

        if not url.startswith(("redis://", "rediss://", "unix://")):
            _redis_available = False
            return None

        import redis.asyncio as aioredis
        _redis_client = aioredis.from_url(url, decode_responses=True)
        _redis_available = True
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis client init notice ({e}) — using in-memory store.")
        _redis_available = False
        return None

async def close_metrics():
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.close()
        except Exception:
            pass

async def record_metric(
    prompt: str,
    complexity: str,
    model_routed: str,
    is_cache_hit: bool,
    latency_ms: float,
    original_tokens: int = 0,
    optimized_tokens: int = 0,
    tokens_saved: int = 0,
    compression_percent: float = 0.0,
    completion_tokens: int = 0,
    similarity_score: float = 0.0
) -> Dict[str, Any]:
    """
    Record a single transaction and compute cost savings.
    """
    direct_cost = calculate_direct_cost(original_tokens, completion_tokens)
    actual_spent = calculate_actual_cost(model_routed, optimized_tokens, completion_tokens, is_cache_hit)
    cost_saved = max(0.0, direct_cost - actual_spent) if is_cache_hit or (direct_cost > actual_spent) else 0.0

    query_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt,
        "complexity": complexity,
        "model_routed": model_routed,
        "is_cache_hit": 1 if is_cache_hit else 0,
        "similarity_score": round(similarity_score * 100, 1) if is_cache_hit else 0.0,
        "latency_ms": round(latency_ms, 1),
        "original_tokens": original_tokens,
        "optimized_tokens": optimized_tokens,
        "tokens_saved": tokens_saved,
        "compression_percent": compression_percent,
        "completion_tokens": completion_tokens,
        "cost_saved": cost_saved,
        "cost_spent": actual_spent,
        "direct_cost": direct_cost
    }

    # Update in-memory state
    _in_memory_metrics["queries"].insert(0, query_data)
    _in_memory_metrics["queries"] = _in_memory_metrics["queries"][:100]
    _in_memory_metrics["total_saved"] += cost_saved
    _in_memory_metrics["total_spent"] += actual_spent
    _in_memory_metrics["total_requests"] += 1
    _in_memory_metrics["total_tokens_in"] += original_tokens
    _in_memory_metrics["total_tokens_optimized"] += optimized_tokens
    _in_memory_metrics["total_tokens_saved"] += tokens_saved
    _in_memory_metrics["latest_model_route"] = model_routed

    if is_cache_hit:
        _in_memory_metrics["cache_hits"] += 1
        _in_memory_metrics["total_latency_hit"] += latency_ms
    else:
        _in_memory_metrics["total_latency_miss"] += latency_ms

    # Optional Redis persistence
    client = _try_get_redis_client()
    if client:
        try:
            async with client.pipeline(transaction=True) as pipe:
                pipe.lpush("gateway_queries", json.dumps(query_data))
                pipe.ltrim("gateway_queries", 0, 99)
                pipe.incrbyfloat("gateway_metric:total_cost_saved", cost_saved)
                pipe.incrbyfloat("gateway_metric:total_cost_spent", actual_spent)
                pipe.incrby("gateway_metric:total_requests", 1)
                pipe.incrby("gateway_metric:tokens_in", original_tokens)
                pipe.incrby("gateway_metric:tokens_optimized", optimized_tokens)
                pipe.incrby("gateway_metric:tokens_saved", tokens_saved)
                pipe.set("gateway_metric:latest_model_route", model_routed)
                if is_cache_hit:
                    pipe.incrby("gateway_metric:cache_hits", 1)
                    pipe.incrbyfloat("gateway_metric:total_latency_hit", latency_ms)
                else:
                    pipe.incrbyfloat("gateway_metric:total_latency_miss", latency_ms)
                await pipe.execute()
        except Exception:
            pass

    return query_data

async def get_metrics_summary() -> Dict[str, Any]:
    """
    Returns complete metrics summary, derived accurately from transaction history.
    Uses Redis cluster metrics if available, falling back to in-memory store.
    """
    client = _try_get_redis_client()
    if client:
        try:
            pipe = client.pipeline()
            pipe.get("gateway_metric:total_requests")
            pipe.get("gateway_metric:cache_hits")
            pipe.get("gateway_metric:total_cost_saved")
            pipe.get("gateway_metric:total_cost_spent")
            pipe.get("gateway_metric:tokens_in")
            pipe.get("gateway_metric:tokens_optimized")
            pipe.get("gateway_metric:tokens_saved")
            pipe.get("gateway_metric:total_latency_hit")
            pipe.get("gateway_metric:total_latency_miss")
            pipe.get("gateway_metric:latest_model_route")
            pipe.lrange("gateway_queries", 0, 29)
            vals = await pipe.execute()

            tot_req = int(vals[0] or 0)
            if tot_req > 0:
                c_hits = int(vals[1] or 0)
                c_miss = max(0, tot_req - c_hits)
                h_rate = (c_hits / tot_req) * 100.0
                t_in = int(vals[4] or 0)
                t_saved = int(vals[6] or 0)
                lat_hit = float(vals[7] or 0.0)
                lat_miss = float(vals[8] or 0.0)
                raw_queries = vals[10] or []
                queries = []
                for q in raw_queries:
                    try:
                        queries.append(json.loads(q) if isinstance(q, str) else q)
                    except Exception:
                        pass

                return {
                    "total_saved": round(float(vals[2] or 0.0), 5),
                    "total_spent": round(float(vals[3] or 0.0), 5),
                    "total_requests": tot_req,
                    "cache_hits": c_hits,
                    "cache_misses": c_miss,
                    "hit_rate": round(h_rate, 2),
                    "total_tokens_in": t_in,
                    "total_tokens_optimized": int(vals[5] or 0),
                    "total_tokens_saved": t_saved,
                    "token_reduction_rate": round((t_saved / t_in) * 100.0, 2) if t_in > 0 else 0.0,
                    "avg_latency_hit": round(lat_hit / c_hits, 1) if c_hits > 0 else 0.0,
                    "avg_latency_miss": round(lat_miss / c_miss, 1) if c_miss > 0 else 0.0,
                    "latest_model_route": vals[9] or "—",
                    "queries": queries
                }
        except Exception as e:
            logger.warning(f"Redis metrics read notice ({e}) — falling back to local memory.")

    # Fallback: In-memory store
    total_requests = _in_memory_metrics["total_requests"]
    cache_hits = _in_memory_metrics["cache_hits"]
    cache_misses = max(0, total_requests - cache_hits)
    hit_rate = (cache_hits / total_requests) * 100.0 if total_requests > 0 else 0.0
    avg_latency_hit = (_in_memory_metrics["total_latency_hit"] / cache_hits) if cache_hits > 0 else 0.0
    avg_latency_miss = (_in_memory_metrics["total_latency_miss"] / cache_misses) if cache_misses > 0 else 0.0

    total_tokens_in = _in_memory_metrics["total_tokens_in"]
    total_tokens_saved = _in_memory_metrics["total_tokens_saved"]
    token_reduction_rate = (total_tokens_saved / total_tokens_in) * 100.0 if total_tokens_in > 0 else 0.0

    return {
        "total_saved": _in_memory_metrics["total_saved"],
        "total_spent": _in_memory_metrics["total_spent"],
        "total_requests": total_requests,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "hit_rate": hit_rate,
        "total_tokens_in": total_tokens_in,
        "total_tokens_optimized": _in_memory_metrics["total_tokens_optimized"],
        "total_tokens_saved": total_tokens_saved,
        "token_reduction_rate": token_reduction_rate,
        "avg_latency_hit": avg_latency_hit,
        "avg_latency_miss": avg_latency_miss,
        "latest_model_route": _in_memory_metrics["latest_model_route"],
        "queries": _in_memory_metrics["queries"][:30]
    }
