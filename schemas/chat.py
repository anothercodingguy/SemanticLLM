from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = "llama-3.1-8b-instant"
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    
    class Config:
        extra = "allow"

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str = "stop"

class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class GatewayCompressionMetadata(BaseModel):
    original_tokens: int = 0
    optimized_tokens: int = 0
    tokens_saved: int = 0
    compression_percent: float = 0.0
    original_text: Optional[str] = None
    optimized_text: Optional[str] = None
    savings_notes: List[str] = []

class GatewayCacheMetadata(BaseModel):
    hit: bool = False
    similarity: float = 0.0
    threshold: float = 0.82

class GatewayRoutingMetadata(BaseModel):
    model: str
    complexity: str
    reason: Optional[str] = None

class GatewayCostMetadata(BaseModel):
    direct_cost: float = 0.0
    actual_spent: float = 0.0
    cost_saved: float = 0.0

class GatewayLatencyMetadata(BaseModel):
    total_ms: float = 0.0
    cache_lookup_ms: float = 0.0
    upstream_inference_ms: float = 0.0

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Optional[Usage] = None
    
    # Semantic Gateway Extension Fields
    gateway_metadata: Optional[Dict[str, Any]] = None
    compression: Optional[GatewayCompressionMetadata] = None
    cache: Optional[GatewayCacheMetadata] = None
    routing: Optional[GatewayRoutingMetadata] = None
    cost: Optional[GatewayCostMetadata] = None
    latency: Optional[GatewayLatencyMetadata] = None
