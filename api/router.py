from fastapi import APIRouter, Header, Response, HTTPException
from fastapi.responses import JSONResponse
import time

from schemas.chat import ChatCompletionRequest, ChatCompletionResponse
from services.cache import get_similar_prompt, store_prompt
from services.llm import process_llm_request, evaluate_complexity
from services.metrics import record_metric

router = APIRouter()

@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest, response: Response):
    # Combine user prompts for the cache key
    full_prompt = " ".join([m.content for m in request.messages if m.role == "user"])
    
    if not full_prompt.strip():
        raise HTTPException(status_code=400, detail="Empty prompt provided.")

    start_time = time.time()
    
    # 1. Check Semantic Cache
    cached_data = await get_similar_prompt(full_prompt)
    if cached_data:
        latency_ms = (time.time() - start_time) * 1000
        
        # Determine complexity to properly log the metric (for consistency)
        complexity = "COMPLEX" if evaluate_complexity(full_prompt) == "llama-3.3-70b-versatile" else "SIMPLE"
        model_routed = evaluate_complexity(full_prompt)
        
        # Extract token usage from cached response
        prompt_tokens = cached_data.get("usage", {}).get("prompt_tokens", 0)
        completion_tokens = cached_data.get("usage", {}).get("completion_tokens", 0)
        
        # Log metrics
        await record_metric(
            prompt=full_prompt,
            complexity=complexity,
            model_routed=model_routed,
            is_cache_hit=True,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        response.headers["X-Cache-Lookup"] = "HIT"
        return JSONResponse(content=cached_data, headers=dict(response.headers))
    
    # 2. Process via Groq/Ollama
    try:
        response_data, model_routed, latency_ms = await process_llm_request(request)
        
        complexity = "COMPLEX" if model_routed == "llama-3.3-70b-versatile" else "SIMPLE"
        if "ollama" in model_routed:
            # Re-evaluate just for metric logging if fallback happened
            complexity = "COMPLEX" if evaluate_complexity(full_prompt) == "llama-3.3-70b-versatile" else "SIMPLE"
            
        # 3. Store in Semantic Cache for future hits
        await store_prompt(full_prompt, response_data)
        
        # 4. Log metrics
        prompt_tokens = response_data.get("usage", {}).get("prompt_tokens", 0)
        completion_tokens = response_data.get("usage", {}).get("completion_tokens", 0)
        
        await record_metric(
            prompt=full_prompt,
            complexity=complexity,
            model_routed=model_routed,
            is_cache_hit=False,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        response.headers["X-Cache-Lookup"] = "MISS"
        return JSONResponse(content=response_data, headers=dict(response.headers))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
