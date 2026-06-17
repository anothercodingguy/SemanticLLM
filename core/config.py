from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    GROQ_API_KEY: str = "dummy_key_for_testing"
    OLLAMA_FALLBACK_URL: str = "http://localhost:11434/api/chat"
    CACHE_SIMILARITY_THRESHOLD: float = 0.92
    
    # Simple heuristic config
    COMPLEXITY_MAX_LENGTH: int = 200
    COMPLEX_KEYWORDS: list[str] = ["code", "analyze", "debug", "explain", "architecture", "complex", "system"]

    # External Serverless DB Configs
    REDIS_URL: Optional[str] = None
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    HF_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore" # Allow extra environment variables in system without failing settings validation

settings = Settings()
