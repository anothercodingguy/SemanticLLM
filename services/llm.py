import time
import httpx
from groq import AsyncGroq
from core.config import settings
from schemas.chat import ChatCompletionRequest
import logging

logger = logging.getLogger(__name__)

# Initialize Groq client with a default timeout of 8.0 seconds to prevent exceeding Vercel limits
groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY, timeout=8.0)

def evaluate_complexity(prompt: str) -> str:
    """
    Determine if a prompt is SIMPLE or COMPLEX based on length and keywords.
    Returns the appropriate model name.
    """
    prompt_lower = prompt.lower()
    
    is_complex = False
    if len(prompt) > settings.COMPLEXITY_MAX_LENGTH:
        is_complex = True
    else:
        for keyword in settings.COMPLEX_KEYWORDS:
            if keyword in prompt_lower:
                is_complex = True
                break
                
    if is_complex:
        return "llama-3.3-70b-versatile"
    else:
        return "llama-3.1-8b-instant"

async def call_groq(request: ChatCompletionRequest, target_model: str) -> dict:
    """
    Call Groq API.
    """
    messages_dict = [{"role": m.role, "content": m.content} for m in request.messages]
    
    chat_completion = await groq_client.chat.completions.create(
        messages=messages_dict,
        model=target_model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    
    return chat_completion.model_dump()

async def call_ollama_fallback(request: ChatCompletionRequest, target_model: str) -> dict:
    """
    Fallback to a local Ollama instance (or a remote endpoint) if Groq fails.
    Limit timeout to 5.0 seconds.
    """
    logger.warning(f"Falling back to Ollama due to Groq error for model {target_model}")
    
    messages_dict = [{"role": m.role, "content": m.content} for m in request.messages]
    ollama_model = "llama3"
    
    payload = {
        "model": ollama_model,
        "messages": messages_dict,
        "stream": False,
        "options": {
            "temperature": request.temperature
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            settings.OLLAMA_FALLBACK_URL,
            json=payload,
            timeout=5.0  # Fast timeout for fallback
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "id": "chatcmpl-fallback",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "ollama-" + ollama_model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": data.get("message", {}).get("content", "")
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
            }
        }

async def process_llm_request(request: ChatCompletionRequest) -> tuple[dict, str, float]:
    """
    Evaluates complexity, attempts Groq, handles fallback, and calculates latency.
    Returns (response_dict, model_routed, latency_ms)
    """
    full_prompt = " ".join([m.content for m in request.messages if m.role == "user"])
    target_model = evaluate_complexity(full_prompt)
    
    start_time = time.time()
    try:
        response_data = await call_groq(request, target_model)
        latency_ms = (time.time() - start_time) * 1000
        return response_data, target_model, latency_ms
    except Exception as e:
        logger.error(f"Groq API Error: {str(e)}")
        try:
            response_data = await call_ollama_fallback(request, target_model)
            latency_ms = (time.time() - start_time) * 1000
            return response_data, "ollama-fallback", latency_ms
        except Exception as fallback_e:
            logger.error(f"Ollama Fallback Error: {str(fallback_e)}")
            raise fallback_e
