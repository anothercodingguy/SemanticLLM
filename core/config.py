from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    OLLAMA_FALLBACK_URL: str = "http://localhost:11434/api/chat"
    CACHE_SIMILARITY_THRESHOLD: float = 0.82
    
    # Model configuration
    MODEL_SIMPLE: str = "llama-3.1-8b-instant"
    MODEL_COMPLEX: str = "llama-3.3-70b-versatile"
    
    # Complexity heuristics
    COMPLEXITY_MAX_LENGTH: int = 250
    COMPLEX_KEYWORDS: List[str] = [
        "code", "analyze", "debug", "explain", "architecture", 
        "complex", "system", "algorithm", "refactor", "optimize", 
        "security", "database", "schema", "benchmark", "concurrency",
        "kubernetes", "docker", "pipeline", "async", "traceback"
    ]

    # External Serverless DB Configs
    REDIS_URL: Optional[str] = None
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    HF_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore" # Allow extra environment variables without failing validation

settings = Settings()
