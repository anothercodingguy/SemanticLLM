import time
import json
import urllib.parse
from fastapi import APIRouter, Response, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List

from core.config import settings
from schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Message,
    CompressRequest,
    CompressResponse,
    BlockReason,
    SustainabilityImpact
)
from services.compression import (
    compress_context,
    compress_for_turn,
    compress_prompt,
    deduplicate_conversation_history,
    estimate_tokens
)
from services.cache import get_similar_prompt, store_prompt
from services.llm import process_llm_request, evaluate_complexity
from services.metrics import record_metric, calculate_direct_cost, calculate_actual_cost

router = APIRouter()

# ── SuperCompress API Endpoints (POST /v1/compress & POST /compress & GET) ────
@router.post("/compress", response_model=CompressResponse)
@router.post("/v1/compress", response_model=CompressResponse)
@router.get("/compress", response_model=CompressResponse)
@router.get("/v1/compress", response_model=CompressResponse)
async def compress_endpoint(
    request: Request,
    response: Response
):
    """
    SuperCompress-compatible query-aware prompt compression endpoint.
    Supports JSON bodies, form-encoded payloads, and GET query parameters.
    """
    context_text = ""
    query_text = ""
    mode = "compiler"
    budget_ratio = None
    context_blocks = None

    if request.method == "POST":
        try:
            body_bytes = await request.body()
            if body_bytes:
                body_str = body_bytes.decode("utf-8")
                # 1. Try parsing JSON
                try:
                    body_json = json.loads(body_str)
                    if isinstance(body_json, dict):
                        context_text = body_json.get("context") or body_json.get("text") or ""
                        query_text = body_json.get("query") or body_json.get("user_query") or ""
                        mode = body_json.get("mode") or "compiler"
                        budget_ratio = body_json.get("budget_ratio")
                        context_blocks = body_json.get("context_blocks")
                except Exception:
                    pass

                # 2. Try parsing URL-encoded form data
                if not context_text:
                    try:
                        parsed_qs = urllib.parse.parse_qs(body_str)
                        if "context" in parsed_qs:
                            context_text = parsed_qs["context"][0]
                        elif "text" in parsed_qs:
                            context_text = parsed_qs["text"][0]
                        if "query" in parsed_qs:
                            query_text = parsed_qs["query"][0]
                        elif "user_query" in parsed_qs:
                            query_text = parsed_qs["user_query"][0]
                        if "mode" in parsed_qs:
                            mode = parsed_qs["mode"][0]
                        if "budget_ratio" in parsed_qs:
                            budget_ratio = float(parsed_qs["budget_ratio"][0])
                    except Exception:
                        pass
        except Exception:
            pass

    # 3. Fallback to query parameters
    if not context_text:
        params = request.query_params
        context_text = params.get("context") or params.get("text") or ""
        query_text = params.get("query") or params.get("user_query") or ""
        mode = params.get("mode") or mode
        if params.get("budget_ratio"):
            try:
                budget_ratio = float(params.get("budget_ratio"))
            except Exception:
                pass

    if not context_text and not context_blocks:
        raise HTTPException(
            status_code=400,
            detail="Missing required parameter: 'context' (or 'text') must be provided."
        )

    # Execute SuperCompress Query-Aware Compression Engine
    start_time = time.time()
    result = compress_for_turn(
        context=context_text,
        user_query=query_text,
        context_blocks=context_blocks,
        mode=mode,
        budget_ratio=budget_ratio
    )
    latency_ms = (time.time() - start_time) * 1000

    # Set SuperCompress Response Headers
    response.headers["X-Original-Tokens"] = str(result["original_tokens"])
    response.headers["X-Kept-Tokens"] = str(result["kept_tokens"])
    response.headers["X-Tokens-Saved"] = str(result["tokens_saved"])
    response.headers["X-Tokens-Saved-Pct"] = f"{result['tokens_saved_pct']:.2f}"
    response.headers["X-Compression-Mode"] = str(result["mode"])
    response.headers["X-Policy-Name"] = str(result["policy_name"])
    response.headers["X-Latency-Ms"] = f"{latency_ms:.1f}"

    return JSONResponse(
        content=result,
        headers=dict(response.headers)
    )


# ── OpenAI Compatible Chat Completions (POST /v1/chat/completions) ──────
@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest, response: Response):
    """
    OpenAI-compatible drop-in proxy with SuperCompress query-aware context compression,
    sub-50ms semantic vector caching, and model complexity routing.
    """
    user_messages = [m.content for m in request.messages if m.role == "user"]
    raw_prompt = " ".join(user_messages).strip()
    
    if not raw_prompt:
        raise HTTPException(status_code=400, detail="Empty prompt provided.")

    start_total_time = time.time()

    # Extract conversation context (system prompts + history)
    history_messages = [m.content for m in request.messages[:-1]] if len(request.messages) > 1 else []
    last_user_query = user_messages[-1] if user_messages else raw_prompt

    # ── Step 1: SuperCompress Query-Aware Context Optimization ────────────
    compression_result = compress_for_turn(
        context=raw_prompt,
        user_query=last_user_query,
        context_blocks=history_messages if history_messages else None,
        mode="compiler"
    )
    optimized_prompt = compression_result["optimized_text"]
    original_tokens = compression_result["original_tokens"]
    optimized_tokens = compression_result["optimized_tokens"]
    tokens_saved = compression_result["tokens_saved"]
    compression_percent = compression_result["compression_percent"]

    # ── Step 2: Semantic Cache Lookup ──────────────────────────────────────
    cache_start = time.time()
    cached_data, similarity_score = await get_similar_prompt(optimized_prompt)
    cache_lookup_ms = (time.time() - cache_start) * 1000

    threshold_pct = round(settings.CACHE_SIMILARITY_THRESHOLD * 100, 1)

    if cached_data and similarity_score >= settings.CACHE_SIMILARITY_THRESHOLD:
        total_latency_ms = (time.time() - start_total_time) * 1000
        
        # Determine routing classification for cached item
        model_routed, complexity_tier, route_reason = evaluate_complexity(optimized_prompt)
        
        cached_usage = cached_data.get("usage", {})
        completion_tokens = cached_usage.get("completion_tokens", 0)

        # Record metrics asynchronously
        metric_entry = await record_metric(
            prompt=raw_prompt,
            complexity=complexity_tier,
            model_routed=model_routed,
            is_cache_hit=True,
            latency_ms=total_latency_ms,
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            tokens_saved=tokens_saved,
            compression_percent=compression_percent,
            completion_tokens=completion_tokens,
            similarity_score=similarity_score
        )

        response.headers["X-Cache-Lookup"] = "HIT"
        response.headers["X-Cache-Similarity"] = f"{similarity_score:.3f}"
        response.headers["X-Model-Route"] = model_routed
        response.headers["X-Tokens-Saved"] = str(tokens_saved)
        response.headers["X-Latency-Ms"] = f"{total_latency_ms:.1f}"

        # Build comprehensive response payload
        result_payload = {
            **cached_data,
            "compression": compression_result,
            "cache": {
                "hit": True,
                "similarity": round(similarity_score * 100, 1),
                "threshold": threshold_pct
            },
            "routing": {
                "model": model_routed,
                "complexity": complexity_tier,
                "reason": "Retrieved from Semantic Vector Cache"
            },
            "cost": {
                "direct_cost": metric_entry["direct_cost"],
                "actual_spent": 0.0,
                "cost_saved": metric_entry["cost_saved"]
            },
            "latency": {
                "total_ms": round(total_latency_ms, 1),
                "cache_lookup_ms": round(cache_lookup_ms, 1),
                "upstream_inference_ms": 0.0
            }
        }
        return JSONResponse(content=result_payload, headers=dict(response.headers))

    # ── Step 3: Complexity Routing & Upstream Inference ────────────────────
    deduped_msgs_raw = [{"role": m.role, "content": m.content} for m in request.messages]
    deduped_msgs_list, _ = deduplicate_conversation_history(deduped_msgs_raw)
    
    if deduped_msgs_list and deduped_msgs_list[-1]["role"] == "user":
        deduped_msgs_list[-1]["content"] = optimized_prompt

    optimized_request = ChatCompletionRequest(
        model=request.model,
        messages=[Message(**m) for m in deduped_msgs_list],
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stream=False
    )

    try:
        upstream_start = time.time()
        response_data, model_routed, upstream_ms, provider_status = await process_llm_request(optimized_request)
        total_latency_ms = (time.time() - start_total_time) * 1000

        target_model, complexity_tier, route_reason = evaluate_complexity(optimized_prompt)
        
        # ── Step 4: Cache Upsert for Future Hits ───────────────────────────
        try:
            await store_prompt(optimized_prompt, response_data)
        except Exception:
            pass

        # ── Step 5: Metrics & Cost Recording ───────────────────────────────
        usage_data = response_data.get("usage", {})
        completion_tokens = usage_data.get("completion_tokens", 0)

        metric_entry = await record_metric(
            prompt=raw_prompt,
            complexity=complexity_tier,
            model_routed=model_routed,
            is_cache_hit=False,
            latency_ms=total_latency_ms,
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            tokens_saved=tokens_saved,
            compression_percent=compression_percent,
            completion_tokens=completion_tokens,
            similarity_score=similarity_score
        )

        response.headers["X-Cache-Lookup"] = "MISS"
        response.headers["X-Model-Route"] = model_routed
        response.headers["X-Tokens-Saved"] = str(tokens_saved)
        response.headers["X-Latency-Ms"] = f"{total_latency_ms:.1f}"

        # Combine payload with rich gateway and SuperCompress metadata
        result_payload = {
            **response_data,
            "compression": compression_result,
            "cache": {
                "hit": False,
                "similarity": round(similarity_score * 100, 1),
                "threshold": threshold_pct
            },
            "routing": {
                "model": model_routed,
                "complexity": complexity_tier,
                "reason": route_reason
            },
            "cost": {
                "direct_cost": metric_entry["direct_cost"],
                "actual_spent": metric_entry["cost_spent"],
                "cost_saved": metric_entry["cost_saved"]
            },
            "latency": {
                "total_ms": round(total_latency_ms, 1),
                "cache_lookup_ms": round(cache_lookup_ms, 1),
                "upstream_inference_ms": round(upstream_ms, 1)
            }
        }
        return JSONResponse(content=result_payload, headers=dict(response.headers))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gateway processing error: {str(e)}")
