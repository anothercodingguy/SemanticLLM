import time
from fastapi import APIRouter, Response, HTTPException
from fastapi.responses import JSONResponse

from schemas.chat import ChatCompletionRequest, ChatCompletionResponse, Message
from services.compression import compress_prompt, deduplicate_conversation_history
from services.cache import get_similar_prompt, store_prompt
from services.llm import process_llm_request, evaluate_complexity
from services.metrics import record_metric, calculate_direct_cost, calculate_actual_cost

router = APIRouter()

@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest, response: Response):
    # Extract user input prompt
    user_messages = [m.content for m in request.messages if m.role == "user"]
    raw_prompt = " ".join(user_messages).strip()
    
    if not raw_prompt:
        raise HTTPException(status_code=400, detail="Empty prompt provided.")

    start_total_time = time.time()

    # ── Step 1: Prompt Compression & Context Optimization ──────────────────
    compression_result = compress_prompt(raw_prompt)
    optimized_prompt = compression_result["optimized_text"]
    original_tokens = compression_result["original_tokens"]
    optimized_tokens = compression_result["optimized_tokens"]
    tokens_saved = compression_result["tokens_saved"]
    compression_percent = compression_result["compression_percent"]

    # ── Step 2: Semantic Cache Lookup ──────────────────────────────────────
    cache_start = time.time()
    cached_data, similarity_score = await get_similar_prompt(optimized_prompt)
    cache_lookup_ms = (time.time() - cache_start) * 1000

    if cached_data and similarity_score >= 0.82:
        total_latency_ms = (time.time() - start_total_time) * 1000
        
        # Determine routing classification for cached item
        model_routed, complexity_tier, route_reason = evaluate_complexity(optimized_prompt)
        
        # Extract token usage from cached payload
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

        # Build comprehensive response
        result_payload = {
            **cached_data,
            "compression": compression_result,
            "cache": {
                "hit": True,
                "similarity": round(similarity_score * 100, 1),
                "threshold": 82.0
            },
            "routing": {
                "model": model_routed,
                "complexity": complexity_tier,
                "reason": "Retrieved from Semantic Cache"
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
    # Prepare optimized request with clean conversation history
    deduped_msgs_raw = [{"role": m.role, "content": m.content} for m in request.messages]
    deduped_msgs_list, _ = deduplicate_conversation_history(deduped_msgs_raw)
    
    # Replace the last user prompt with the optimized text
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
            similarity_score=0.0
        )

        response.headers["X-Cache-Lookup"] = "MISS"
        response.headers["X-Model-Route"] = model_routed
        response.headers["X-Tokens-Saved"] = str(tokens_saved)
        response.headers["X-Latency-Ms"] = f"{total_latency_ms:.1f}"

        # Combine payload with rich gateway metadata
        result_payload = {
            **response_data,
            "compression": compression_result,
            "cache": {
                "hit": False,
                "similarity": round(similarity_score * 100, 1),
                "threshold": 82.0
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
