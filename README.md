# Semantic LLM Gateway

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.1%20%7C%203.3-f55036?style=flat)](https://groq.com/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20Cache-dc2626?style=flat&logo=qdrant)](https://qdrant.tech/)

A FastAPI gateway that sits between an application and Groq-hosted Llama models. It trims prompt context, answers repeated questions from a semantic cache, and sends each request to a small or a large model depending on the prompt.

Live demo: https://semantic-llm.vercel.app

## What it does

- **Context compression.** `POST /compress` splits the context into blocks (markdown sections, code fences, log runs, paragraphs), removes duplicate lines, scores each block by keyword overlap with the query, and drops the low-scoring blocks. The scoring is rule-based and makes no model call. The response lists every kept and dropped block with a reason.
- **Semantic cache.** Prompts are embedded with `all-MiniLM-L6-v2` (384 dimensions, via fastembed) and stored in Qdrant. A new prompt with cosine similarity of 0.82 or higher to a stored one gets the stored response and skips the model call. If Qdrant is unavailable, an in-process list of the last 200 entries is searched instead.
- **Model routing.** Prompts that contain code markers, are longer than 250 characters, or include a keyword such as `debug` or `architecture` go to `llama-3.3-70b-versatile`. Everything else goes to `llama-3.1-8b-instant`.
- **Provider fallback.** Groq is called first. If that fails, the gateway tries an Ollama server (`llama3`). If both fail, it returns a canned placeholder answer so the request still completes. The response says which of the three answered in `provider.status` (`groq`, `ollama` or `fallback`), and `provider.simulated` is `true` for the placeholder.
- **Metrics and dashboard.** Each request records token counts, cache hit or miss, latency, and an estimated cost from a price table in `services/metrics.py`. Metrics are kept in memory and also written to Redis when `REDIS_URL` is set. `GET /api/metrics` returns them, and `/` serves a dashboard with a playground.

## How a request flows

```text
POST /v1/chat/completions                           api/router.py
  1. drop repeated messages from the history        services/compression.py
  2. compress the context against the question      services/compression.py
  3. cache lookup: exact match, then vector search  services/cache.py
       similarity >= 0.82  -> return the cached response (X-Cache-Lookup: HIT)
       otherwise           -> continue
  4. pick the 8B or 70B model from the prompt       services/llm.py
  5. call Groq, then Ollama, then the placeholder   services/llm.py
  6. write the response to the cache                services/cache.py
  7. record metrics and return                      services/metrics.py
```

`POST /v1/compress` runs step 2 on its own. Both endpoints are served with and without the `/v1` prefix.

## Example

Compress a context for a question:

```bash
curl -X POST http://localhost:8000/v1/compress \
  -H "Content-Type: application/json" \
  -d '{
    "context": "## Deploy log\n2026-01-01 10:00:00 INFO health probe ok\n2026-01-01 10:00:05 INFO health probe ok\n\n## Refund policy\nRefunds above $500 need supervisor approval.",
    "query": "What is the refund policy?"
  }'
```

Response from the code in this repo, with some fields left out:

```json
{
  "compressed_text": "## Refund policy\nRefunds above $500 need supervisor approval.",
  "original_tokens": 39,
  "kept_tokens": 15,
  "tokens_saved_pct": 61.54,
  "kept_blocks": [{"heading": "Refund policy", "reason": "Matches query topic in 'Refund policy'", "tokens": 15}],
  "dropped_blocks": [{"heading": "Deploy log", "reason": "Irrelevant passage to the specific query question", "tokens": 13}]
}
```

This is one small input. The repo has no benchmark script, so there is no measured average. Optional request fields: `mode` (`compiler` by default, `precision` for a stricter cutoff, `fixed` with a `budget_ratio` between 0.1 and 1.0) and `context_blocks` (a list of strings). The same logic can be imported in Python: `from services.compression import compress_context`.

Send a chat request:

```bash
curl -i -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What is the capital of France?"}]}'
```

The body has the usual chat completion fields (`id`, `choices`, `usage`) plus `compression`, `cache`, `routing`, `cost`, `latency`, and `provider`. The headers include `X-Cache-Lookup`, `X-Model-Route`, `X-Tokens-Saved`, and `X-Latency-Ms`. Send the same request again and `X-Cache-Lookup` changes from `MISS` to `HIT`.

## Tech stack

- Python 3.10+, FastAPI, Uvicorn, Pydantic v2 with pydantic-settings
- Groq Python SDK (`AsyncGroq`) for inference, httpx for the Ollama and Hugging Face calls
- Qdrant (`qdrant-client`) and fastembed for the vector cache
- Redis (`redis.asyncio`) as an optional metrics store
- Dashboard: one HTML page (`static/index.html`) served by FastAPI, with Chart.js
- Dockerfile and `docker-compose.yml` (gateway, Qdrant, Redis); `vercel.json` and `render.yaml` for hosting

## Run locally

```bash
git clone https://github.com/anothercodingguy/SemanticLLM.git
cd SemanticLLM
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "GROQ_API_KEY=<your Groq key>" > .env
uvicorn main:app --reload --port 8000
```

Then open http://localhost:8000 (dashboard), http://localhost:8000/docs (OpenAPI docs), or http://localhost:8000/health.

Settings are read from the environment or from `.env` (see `core/config.py`):

| Variable | Default | Effect |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | empty | Needed for real model answers. Without it the fallback chain runs. |
| `OLLAMA_FALLBACK_URL` | `http://localhost:11434/api/chat` | Ollama endpoint tried when Groq fails. |
| `CACHE_SIMILARITY_THRESHOLD` | `0.82` | Minimum cosine similarity for a cache hit. |
| `QDRANT_URL`, `QDRANT_API_KEY` | unset | Remote Qdrant. When unset, Qdrant runs in its in-process `:memory:` mode. |
| `REDIS_URL` | unset | When set, metrics are also written to Redis. |
| `HF_API_KEY` | unset | When set, embeddings come from the Hugging Face Inference API. Otherwise fastembed runs locally. |

`.env.example` lists the same variables. Its Qdrant, Redis, and Hugging Face values are placeholders, so delete those lines unless you fill them in. `MODEL_SIMPLE`, `MODEL_COMPLEX`, and `COMPLEXITY_MAX_LENGTH` can be overridden the same way.

With Docker, `docker compose up --build` starts the gateway together with Qdrant and Redis containers. It reads `GROQ_API_KEY` from your shell or from `.env`.

## Tests

```bash
python test_all.py
```

`test_all.py` runs 10 checks through FastAPI's `TestClient`: health, dashboard, the compression functions and HTTP endpoints, routing, cost math, input validation, a cache miss followed by a hit on a rephrased question, and system-prompt compression. No API key is needed, because the placeholder fallback answers when Groq and Ollama are unreachable. The cache check needs the embedding model, which fastembed downloads on first use.

`test_dashboard.py` is a small script that prints the `/api/metrics` output.

## Limits

- Streaming is not implemented, and the `model` field in the request is ignored because the gateway chooses the model.
- Token counts are estimates (`max(words * 1.3, chars / 4)`), so they will differ from a real tokenizer.
- The endpoints have no authentication.
- Without `QDRANT_URL` and `REDIS_URL`, the cache and metrics live in the server process and are lost on restart.

## License

Apache-2.0, as declared in `pyproject.toml`.
