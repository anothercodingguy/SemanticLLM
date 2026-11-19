from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from api.router import router as chat_router
from services.cache import init_cache, close_cache
from services.metrics import get_metrics_summary, close_metrics
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# The landing page + dashboard lives in static/index.html. The path is built
# from this file's location (not the working directory) so it resolves the same
# way under `uvicorn main:app`, Docker, and Vercel (where api/index.py imports
# this module from a different cwd).
INDEX_HTML_PATH = Path(__file__).resolve().parent / "static" / "index.html"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup Qdrant collection on startup if it doesn't exist
    await init_cache()
    yield
    await close_cache()
    await close_metrics()

app = FastAPI(
    title="Semantic Gateway",
    description="Rule-based, query-aware context compression, semantic vector caching and complexity routing gateway for Groq-hosted Llama models",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Cache-Lookup", "X-Cache-Similarity", "X-Model-Route", "X-Tokens-Saved",
        "X-Tokens-Saved-Pct", "X-Latency-Ms", "X-Original-Tokens", "X-Kept-Tokens",
        "X-Compression-Mode", "X-Policy-Name"
    ],
)

# Include router at both root and /v1 for full Semantic LLM + OpenAI API compatibility
app.include_router(chat_router, prefix="/v1")
app.include_router(chat_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0", "service": "Semantic Gateway"}

@app.get("/api/metrics")
async def get_metrics():
    """
    Exposes live metrics derived from gateway requests.
    """
    summary = await get_metrics_summary()
    return summary

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    """
    Serves the landing page and dashboard from static/index.html.
    The file is read on each request (it is small, and the CDN caches the
    response), so edits to the HTML show up without restarting the server.
    """
    # The page is static (live numbers load from /api/metrics in the browser),
    # so let the CDN serve it instead of cold-starting this function on every visit.
    return HTMLResponse(
        content=INDEX_HTML_PATH.read_text(encoding="utf-8"),
        headers={"Cache-Control": "public, max-age=0, s-maxage=3600, stale-while-revalidate=86400"},
    )

def cli():
    """CLI entrypoint for running the semantic-gateway server."""
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    cli()
