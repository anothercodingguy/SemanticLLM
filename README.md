# Semantic Gateway

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.1%20%7C%203.3-f55036?style=flat)](https://groq.com/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20Cache-dc2626?style=flat&logo=qdrant)](https://qdrant.tech/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

**Semantic Gateway** is an intelligent, high-performance LLM proxy and cost-optimization layer. It intercepts AI feature requests before inference to **deduplicate noisy context**, **serve semantically equivalent queries from a sub-50ms vector cache**, and **route simple vs. complex queries** across different model tiers (`llama-3.1-8b-instant` vs. `llama-3.3-70b-versatile`).

---

## ⚡ Core Architecture

```mermaid
flowchart TD
    User(["User / AI Agent / RAG Pipeline"]) -->|"POST /v1/chat/completions"| Gateway["Semantic Gateway"]
    
    Gateway --> Compress["1. Prompt Compression Engine"]
    Compress -->|"Deduplicate logs, RAG chunks & whitespace"| CacheCheck{"2. Semantic Vector Cache<br/>FastEmbed 384-dim"}
    
    CacheCheck -->|"Similarity >= 0.82 (CACHE HIT)"| HitResp["Return Cached Response<br/>Latency: Sub-50ms · Cost: $0.00"]
    
    CacheCheck -->|"Similarity < 0.82 (CACHE MISS)"| Route["3. Complexity Router"]
    
    Route -->|"Simple Query (Length < 250 chars)"| M8B["Groq Llama-3.1-8B-Instant<br/>$0.05 / 1M input tokens"]
    Route -->|"Complex Query (Code / Architecture)"| M70B["Groq Llama-3.3-70B-Versatile<br/>$0.59 / 1M input tokens"]
    
    M8B --> Inference["Upstream Inference"]
    M70B --> Inference
    
    Inference -.->|"If Groq Unreachable"| Fallback["Ollama / Resilient Fallback"]
    
    Inference --> Store["4. Upsert Semantic Cache & Record Metrics"]
    Fallback --> Store
    
    Store --> ClientResponse["Return Response + Gateway Headers"]
    HitResp --> ClientResponse
```

---

## ✨ Features

### 1. 🎯 Semantic Vector Cache
* **Dense Vector Embeddings**: Embeds queries into 384-dimensional dense vectors using local `fastembed` (`sentence-transformers/all-MiniLM-L6-v2`) or Hugging Face Serverless API.
* **Semantic Paraphrase Matching**: Uses cosine similarity (`threshold = 0.82`) to catch queries with identical meaning even if the wording differs.
* **Zero Spend & Sub-50ms Latency**: Cache hits bypass upstream inference entirely, resulting in **$0.00 API spend** and instantaneous responses.
* **Zero Downtime Storage**: Backed by Qdrant (in-memory or cloud cluster) with thread-safe memory fallback.

### 2. 🧹 Context Compression & Deduplication
* **Log & Stack Trace Cleaning**: Identifies and removes repetitive timestamped log lines and noisy debug outputs.
* **RAG Chunk Deduplication**: Eliminates overlapping sentences across retrieved context chunks.
* **Conversation History Optimization**: Retains chronological integrity while removing duplicate historical prompts.
* **Granular Savings Metadata**: Returns exact counts for `original_tokens`, `optimized_tokens`, `tokens_saved`, and `compression_percent`.

### 3. 🧠 Multi-Signal Complexity Routing
* **Automated Model Selection**: Evaluates query length, code blocks (````...````), SQL/regex syntax, and analytical keywords.
* **Simple Queries**: Routed to **Groq Llama 3.1 8B Instant** ($0.05/M input).
* **Complex Queries**: Scaled up to **Groq Llama 3.3 70B Versatile** ($0.59/M input).
* **Cost Efficiency**: Reduces baseline 70B inference spend by up to **65%–90%**.

### 4. 🛡️ Resilient Fallback & Security
* **Groq SDK Server-Side Integration**: API secrets are never exposed to the client browser.
* **Graceful Failover**: Automatically attempts local/remote Ollama fallback (`http://localhost:11434/api/chat`) if primary upstream providers fail.
* **Sanitized Responses**: No raw exception traces or credentials leaked on network failure.

### 5. 📊 Real-Time Developer Dashboard & Interactive Sandbox
* **Interactive Sandbox**: Test prompts with preset chips, view live character and token counters, and inspect original vs. optimized context diffs.
* **Impact Analytics**: Live Chart.js latency comparison graphs (Direct Upstream Miss vs. Cache Hit) and live query logs.
* **Accurate Financial Tracking**: Computes true cost saved vs. actual spend formatted to 5 decimal places (`$0.00024`).

---

## 🚀 Quick Start

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/anothercodingguy/SemanticLLM.git
cd SemanticLLM

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root (see `.env.example`):

```bash
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Semantic Cache Configuration
CACHE_SIMILARITY_THRESHOLD=0.82

# Optional External Services
OLLAMA_FALLBACK_URL=http://localhost:11434/api/chat
REDIS_URL=rediss://default:password@your-upstash-endpoint.upstash.io:6379
QDRANT_URL=https://your-qdrant-cluster.aws.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here
HF_API_KEY=your_huggingface_api_key_here
```

### 3. Start the Server

```bash
uvicorn main:app --reload --port 8000
```

* **Interactive Sandbox & Dashboard**: Open [http://localhost:8000](http://localhost:8000) in your browser.
* **API Documentation**: Click the **Docs** button in the header or visit `/docs`.
* **Health Check**: [http://localhost:8000/health](http://localhost:8000/health).

---

## 💻 Integration Examples

### Python (OpenAI SDK Drop-In)

Semantic Gateway is 100% drop-in compatible with the official OpenAI Python SDK. Simply change the `base_url`:

```python
from openai import OpenAI

# Point client to Semantic Gateway
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-required"  # Handled server-side by the gateway
)

response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "user", "content": "What does fetch_user return when the row is missing?"}
    ]
)

print("Assistant:", response.choices[0].message.content)
```

### Node.js / TypeScript (OpenAI SDK)

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://localhost:8000/v1",
  apiKey: "not-required"
});

async function main() {
  const response = await client.chat.completions.create({
    model: "llama-3.1-8b-instant",
    messages: [{ role: "user", content: "Explain microservice circuit breakers." }]
  });

  console.log(response.choices[0].message.content);
}

main();
```

### cURL

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What happens if fetch_user cannot find the database row?"}
    ]
  }'
```

---

## 📡 API Reference

### `POST /v1/chat/completions`
Standard OpenAI chat completions endpoint with gateway optimization.

#### Response Headers:
* `X-Cache-Lookup`: `HIT` | `MISS`
* `X-Cache-Similarity`: Cosine similarity score (e.g. `0.839`)
* `X-Model-Route`: Routed model (e.g. `llama-3.1-8b-instant` or `llama-3.3-70b-versatile`)
* `X-Tokens-Saved`: Total tokens eliminated via compression
* `X-Latency-Ms`: Total gateway processing time in milliseconds

#### Response Body:
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1786689533,
  "model": "llama-3.1-8b-instant",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "When the requested row is missing, fetch_user returns None..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 11,
    "completion_tokens": 37,
    "total_tokens": 48
  },
  "compression": {
    "original_tokens": 61,
    "optimized_tokens": 42,
    "tokens_saved": 19,
    "compression_percent": 31.1,
    "savings_notes": ["Deduplicated 2 redundant context line(s)"]
  },
  "cache": {
    "hit": true,
    "similarity": 83.9,
    "threshold": 82.0
  },
  "routing": {
    "model": "llama-3.1-8b-instant",
    "complexity": "SIMPLE",
    "reason": "Direct standard query suitable for instant model"
  },
  "cost": {
    "direct_cost": 0.0000369,
    "actual_spent": 0.0,
    "cost_saved": 0.0000369
  },
  "latency": {
    "total_ms": 38.2,
    "cache_lookup_ms": 38.2,
    "upstream_inference_ms": 0.0
  }
}
```

### `GET /api/metrics`
Returns aggregate performance and cost metrics.

```json
{
  "total_saved": 0.00142,
  "total_spent": 0.00038,
  "total_requests": 14,
  "cache_hits": 6,
  "cache_misses": 8,
  "hit_rate": 42.8,
  "total_tokens_in": 1250,
  "total_tokens_optimized": 890,
  "total_tokens_saved": 360,
  "token_reduction_rate": 28.8,
  "avg_latency_hit": 34.5,
  "avg_latency_miss": 182.1,
  "latest_model_route": "llama-3.1-8b-instant",
  "queries": [...]
}
```

### `GET /health`
Returns `{"status": "ok"}` for container and load balancer health checks.

---

## 🧪 Automated Testing

Run the full end-to-end unit and integration test suite:

```bash
python test_all.py
```

Output:
```text
✅ /health check passed
✅ Dashboard HTML page test passed
✅ Prompt compression engine tests passed
✅ Model complexity routing classification test passed
✅ Cost calculation and pricing formulas passed
✅ Empty prompt validation test passed
✅ End-to-end Gateway, Semantic Cache & Metrics flow passed

🎉 ALL AUDIT & INTEGRATION TESTS PASSED SUCCESSFULLY!
```

---

## ⚙️ Environment Variables Reference

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `GROQ_API_KEY` | `string` | `""` | Primary Groq API key for Llama 3 inference |
| `CACHE_SIMILARITY_THRESHOLD` | `float` | `0.82` | Cosine similarity threshold for semantic cache hits |
| `OLLAMA_FALLBACK_URL` | `string` | `http://localhost:11434/api/chat` | Fallback endpoint if Groq is unreachable |
| `REDIS_URL` | `string` | `None` | Optional Upstash / Redis URI for durable metrics persistence |
| `QDRANT_URL` | `string` | `None` | Optional Qdrant Cloud cluster endpoint (defaults to `:memory:`) |
| `QDRANT_API_KEY` | `string` | `None` | API key for authenticated Qdrant Cloud clusters |
| `HF_API_KEY` | `string` | `None` | Optional Hugging Face Inference token for remote embeddings |

---

## 📄 License

This project is licensed under the Apache 2.0 License.
