from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

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

# ── SuperCompress API Schemas ───────────────────────────────────────────
class CompressRequest(BaseModel):
    context: Optional[str] = None
    text: Optional[str] = None  # Alias for context
    query: Optional[str] = ""
    user_query: Optional[str] = None  # Alias for query
    mode: Optional[str] = "compiler"  # "compiler", "precision", "fixed"
    budget_ratio: Optional[float] = None  # 0.1 - 1.0 (for fixed mode)
    context_blocks: Optional[List[str]] = None

    class Config:
        extra = "allow"

class BlockReason(BaseModel):
    heading: str
    reason: str
    tokens: int = 0

class SustainabilityImpact(BaseModel):
    co2_kg_avoided: float = 0.0
    watt_hours_saved: float = 0.0
    gpu_seconds_avoided: float = 0.0
    assumptions: Dict[str, Any] = Field(default_factory=lambda: {
        "tokens_per_gpu_sec": 2500,
        "gpu_power_watts": 150,
        "co2_kg_per_kwh": 0.417,
        "context_share_of_prefill": 0.55
    })

class CompressResponse(BaseModel):
    compressed_text: str
    compressed: Optional[str] = None  # Alias for compressed_text
    original_tokens: int = 0
    kept_tokens: int = 0
    tokens_saved: int = 0
    tokens_saved_pct: float = 0.0
    important_kept_pct: float = 1.0
    compression_risk: str = "low"  # "low", "medium", "high"
    kept_blocks: List[BlockReason] = Field(default_factory=list)
    dropped_blocks: List[BlockReason] = Field(default_factory=list)
    policy_name: str = "SemanticGateway-compiler"
    mode: str = "compiler"
    keep_ratio: float = 1.0
    kept_line_ratio: float = 1.0
    sustainability: Optional[SustainabilityImpact] = None

class GatewayCompressionMetadata(BaseModel):
    original_tokens: int = 0
    optimized_tokens: int = 0
    tokens_saved: int = 0
    compression_percent: float = 0.0
    important_kept_pct: float = 1.0
    compression_risk: str = "low"
    original_text: Optional[str] = None
    optimized_text: Optional[str] = None
    savings_notes: List[str] = []
    kept_blocks: List[BlockReason] = Field(default_factory=list)
    dropped_blocks: List[BlockReason] = Field(default_factory=list)
    sustainability: Optional[SustainabilityImpact] = None

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
