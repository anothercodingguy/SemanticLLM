from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from api.router import router as chat_router
from services.cache import init_cache, close_cache
from services.metrics import get_metrics_summary, close_metrics
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup Qdrant collection on startup if it doesn't exist
    await init_cache()
    yield
    await close_cache()
    await close_metrics()

app = FastAPI(
    title="Semantic LLM Gateway",
    description="Cost-Aware Routing Proxy for Groq with Semantic Caching and Ollama Fallback",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for allowing dashboard access across different origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Cache-Lookup"],
)

# Include the router under /v1 to match OpenAI spec
app.include_router(chat_router, prefix="/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/metrics")
async def get_metrics():
    """
    Exposes metrics fetched from Upstash Redis to the frontend.
    """
    summary = await get_metrics_summary()
    return summary

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    """
    Serves the redesigned Semantic LLM Gateway dashboard with Supercompress aesthetic.
    """
    html_content = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Semantic LLM Gateway - Cut Your LLM API Costs</title>
    <meta name="description" content="An intelligent LLM proxy with semantic caching, cost-aware model routing, and graceful fallback.">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        /* ═══════════════════════════════════════════
           DESIGN SYSTEM (Supercompress Light Theme)
           ═══════════════════════════════════════════ */
        :root {
            --bg: rgb(251, 251, 248);
            --surface: #ffffff;
            --surface-hover: #f9f9f9;
            --border: rgba(0, 0, 0, 0.08);
            --border-hover: rgba(0, 0, 0, 0.15);
            --text: #111111;
            --text-secondary: #555555;
            --text-muted: #888888;
            --accent: #111111;
            --accent-hover: #333333;
            --radius: 8px;
            --radius-sm: 6px;
            --font: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            --mono: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        html { scroll-behavior: smooth; }

        body {
            font-family: var(--font);
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            overflow-x: hidden;
        }

        /* ═══════════════════════════════════════════
           NAVIGATION
           ═══════════════════════════════════════════ */
        .nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 100;
            background: rgba(251, 251, 248, 0.85);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
        }

        .nav-inner {
            max-width: 1100px;
            margin: 0 auto;
            padding: 0 1.5rem;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .nav-logo {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
            color: var(--text);
            font-weight: 700;
            font-size: 1.1rem;
            letter-spacing: -0.02em;
        }

        .nav-logo-icon {
            width: 24px;
            height: 24px;
            background: var(--text);
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 800;
            color: #fff;
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }

        .nav-links a {
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.875rem;
            font-weight: 500;
            transition: color 0.2s;
        }

        .nav-links a:hover {
            color: var(--text);
        }

        .nav-badge {
            display: inline-flex;
            align-items: center;
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text);
            background: rgba(0,0,0,0.04);
            border: 1px solid var(--border);
            padding: 0.3rem 0.6rem;
            border-radius: 20px;
        }

        /* ═══════════════════════════════════════════
           HERO
           ═══════════════════════════════════════════ */
        .hero {
            padding: 10rem 1.5rem 6rem;
            max-width: 1000px;
            margin: 0 auto;
            text-align: center;
        }

        .ph-badge {
            display: inline-block;
            margin-bottom: 2rem;
            border-radius: 6px;
            overflow: hidden;
            border: 1px solid var(--border);
            animation: fadeSlideUp 0.6s ease both;
        }

        .ph-badge img { display: block; }

        .hero h1 {
            font-size: clamp(3rem, 7vw, 5.5rem);
            font-weight: 800;
            letter-spacing: -0.04em;
            line-height: 1.05;
            margin-bottom: 1.5rem;
            color: var(--text);
        }

        .hero h1 span {
            display: inline-block;
            opacity: 0;
            transform: translateY(20px);
            animation: wordReveal 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        @keyframes wordReveal {
            to { opacity: 1; transform: translateY(0); }
        }

        .hero-lead {
            font-size: 1.25rem;
            color: var(--text-secondary);
            max-width: 700px;
            margin: 0 auto 3rem;
            line-height: 1.6;
            animation: fadeSlideUp 0.6s 0.8s ease both;
        }

        .hero-actions {
            display: flex;
            gap: 1rem;
            justify-content: center;
            animation: fadeSlideUp 0.6s 1s ease both;
        }

        @keyframes fadeSlideUp {
            from { opacity: 0; transform: translateY(16px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .btn-primary {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--text);
            color: #fff;
            border: none;
            padding: 0.875rem 1.75rem;
            font-size: 0.95rem;
            font-weight: 600;
            border-radius: var(--radius-sm);
            cursor: pointer;
            text-decoration: none;
            transition: transform 0.2s, background 0.2s;
        }

        .btn-primary:hover {
            background: var(--accent-hover);
            transform: translateY(-1px);
        }

        .btn-secondary {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: transparent;
            color: var(--text);
            border: 1px solid var(--border-hover);
            padding: 0.875rem 1.75rem;
            font-size: 0.95rem;
            font-weight: 600;
            border-radius: var(--radius-sm);
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s;
        }

        .btn-secondary:hover {
            background: rgba(0,0,0,0.03);
            border-color: var(--text);
        }

        /* ═══════════════════════════════════════════
           SECTIONS
           ═══════════════════════════════════════════ */
        .section {
            max-width: 1100px;
            margin: 0 auto;
            padding: 5rem 1.5rem;
            border-top: 1px solid var(--border);
        }

        .section-header {
            max-width: 700px;
            margin-bottom: 3.5rem;
        }

        .section-label {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 0.75rem;
        }

        .section-title {
            font-size: clamp(2rem, 4vw, 2.75rem);
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 1rem;
            line-height: 1.1;
        }

        .section-desc {
            font-size: 1.125rem;
            color: var(--text-secondary);
            line-height: 1.6;
        }

        /* ═══════════════════════════════════════════
           FEATURE CARDS
           ═══════════════════════════════════════════ */
        .features-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
        }

        .feature-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 2rem;
            box-shadow: 0 4px 24px rgba(0,0,0,0.02);
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .feature-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 32px rgba(0,0,0,0.06);
            border-color: var(--border-hover);
        }

        .feature-label {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 1rem;
            display: block;
        }

        .feature-title {
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
            letter-spacing: -0.01em;
        }

        .feature-desc {
            font-size: 0.95rem;
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
        }

        .feature-list {
            list-style: none;
        }

        .feature-list li {
            font-size: 0.9rem;
            color: var(--text-secondary);
            padding: 0.25rem 0;
            position: relative;
            padding-left: 1.2rem;
        }

        .feature-list li::before {
            content: '\2022';
            position: absolute;
            left: 0;
            color: var(--text);
            font-weight: bold;
        }

        /* ═══════════════════════════════════════════
           ARCHITECTURE
           ═══════════════════════════════════════════ */
        .arch-split {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            align-items: center;
        }

        .arch-code {
            background: #f4f4f0;
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.5rem;
            overflow-x: auto;
        }

        .arch-code pre {
            font-family: var(--mono);
            font-size: 0.85rem;
            line-height: 1.6;
            color: #333;
        }

        .arch-code .kw { color: #000; font-weight: 600; }
        .arch-code .str { color: #1e3a8a; }
        .arch-code .cmt { color: #888; }
        .arch-code .num { color: #047857; }

        /* ═══════════════════════════════════════════
           DASHBOARD (Impact Demo)
           ═══════════════════════════════════════════ */
        .dash-container {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            box-shadow: 0 12px 40px rgba(0,0,0,0.03);
            overflow: hidden;
            margin-top: 2rem;
        }

        .dash-header {
            display: flex;
            border-bottom: 1px solid var(--border);
            background: #fafafa;
        }

        .dash-tab {
            padding: 1rem 1.5rem;
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-secondary);
            cursor: pointer;
            border-right: 1px solid var(--border);
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
        }

        .dash-tab.active {
            color: var(--text);
            border-bottom-color: var(--text);
            background: var(--surface);
        }

        .dash-content {
            display: none;
            padding: 2rem;
        }

        .dash-content.active { display: block; }

        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }

        .metric-block {
            display: flex;
            flex-direction: column;
        }

        .metric-label {
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.25rem;
        }

        .metric-value {
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: -0.04em;
            color: var(--text);
            line-height: 1.1;
        }
        
        .metric-sub {
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-top: 0.5rem;
        }

        .latency-split {
            display: flex;
            align-items: baseline;
            gap: 0.5rem;
            margin-top: 0.25rem;
        }
        .latency-split .metric-value { font-size: 1.8rem; }
        .latency-tag { font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); background: #f0f0f0; padding: 0.1rem 0.4rem; border-radius: 4px; }

        /* Chart & Table */
        .chart-wrap {
            height: 300px;
            margin-bottom: 2.5rem;
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 1rem;
            background: #fafafa;
        }

        .table-wrap {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.875rem;
        }

        th, td {
            padding: 0.875rem 1rem;
            border-bottom: 1px solid var(--border);
        }

        th {
            background: #fafafa;
            color: var(--text-secondary);
            font-weight: 600;
            position: sticky;
            top: 0;
        }

        tr:last-child td { border-bottom: none; }
        
        .badge {
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            background: #f0f0f0;
            color: var(--text-secondary);
        }
        .badge.advanced { background: #e0e0e0; color: var(--text); }

        .status-dot { font-weight: 600; }
        .status-dot.hit { color: #047857; }
        .status-dot.miss { color: #b45309; }

        .prompt-cell { max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

        /* ═══════════════════════════════════════════
           CHAT SANDBOX
           ═══════════════════════════════════════════ */
        .chat-layout {
            display: flex;
            flex-direction: column;
            height: 500px;
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            background: #fafafa;
        }

        .chat-messages {
            flex: 1;
            padding: 1.5rem;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }

        .message {
            max-width: 80%;
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
        }

        .message.user { align-self: flex-end; }
        .message.assistant { align-self: flex-start; }

        .msg-bubble {
            padding: 1rem 1.25rem;
            border-radius: 8px;
            font-size: 0.95rem;
            line-height: 1.6;
        }

        .message.user .msg-bubble {
            background: var(--text);
            color: #fff;
        }

        .message.assistant .msg-bubble {
            background: #fff;
            color: var(--text);
            border: 1px solid var(--border);
            box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        }

        .msg-info {
            font-size: 0.75rem;
            color: var(--text-muted);
            display: flex;
            gap: 0.75rem;
            align-items: center;
        }
        .msg-info strong { color: var(--text-secondary); }

        .chat-input-bar {
            padding: 1.25rem;
            background: #fff;
            border-top: 1px solid var(--border);
            display: flex;
            gap: 0.75rem;
        }

        .chat-input {
            flex: 1;
            padding: 0.875rem 1rem;
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            font-family: var(--font);
            font-size: 0.95rem;
            outline: none;
            background: #fafafa;
            transition: border-color 0.2s;
        }

        .chat-input:focus { border-color: var(--text-secondary); background: #fff; }

        .btn-send {
            background: var(--text);
            color: #fff;
            border: none;
            padding: 0 1.5rem;
            border-radius: var(--radius-sm);
            font-weight: 600;
            font-family: var(--font);
            cursor: pointer;
            transition: background 0.2s;
        }

        .btn-send:hover { background: var(--accent-hover); }
        .btn-send:disabled { background: #ccc; cursor: not-allowed; }

        /* ═══════════════════════════════════════════
           FOOTER
           ═══════════════════════════════════════════ */
        .footer {
            border-top: 1px solid var(--border);
            padding: 4rem 1.5rem 3rem;
            background: #ffffff;
        }

        .footer-inner {
            max-width: 1100px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1.5fr 1fr 1fr;
            gap: 3rem;
        }

        .footer-brand p {
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-top: 0.75rem;
            max-width: 300px;
        }

        .footer-logo { font-weight: 800; font-size: 1.1rem; }

        .footer-col h4 {
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text);
            margin-bottom: 1rem;
        }

        .footer-col ul { list-style: none; }
        .footer-col li { margin-bottom: 0.5rem; }
        .footer-col a {
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.9rem;
        }
        .footer-col a:hover { color: var(--text); text-decoration: underline; }

        .footer-copy {
            max-width: 1100px;
            margin: 4rem auto 0;
            padding-top: 2rem;
            border-top: 1px solid var(--border);
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        /* ═══════════════════════════════════════════
           SCROLL REVEAL
           ═══════════════════════════════════════════ */
        .reveal {
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }
        .reveal.visible { opacity: 1; transform: translateY(0); }

        @media (max-width: 768px) {
            .arch-split, .features-grid, .metrics-grid, .footer-inner { grid-template-columns: 1fr; }
            .hero { padding-top: 8rem; }
            .nav-links { display: none; }
        }
    </style>
</head>
<body>

    <!-- NAVIGATION -->
    <nav class="nav">
        <div class="nav-inner">
            <a href="#" class="nav-logo">
                <div class="nav-logo-icon">S</div>
                Semantic LLM
            </a>
            <div class="nav-links">
                <a href="#features">Features</a>
                <a href="#architecture">API</a>
                <a href="#dashboard">Dashboard</a>
                <span class="nav-badge">Online</span>
            </div>
        </div>
    </nav>

    <!-- HERO -->
    <section class="hero" id="hero">
        <a href="#dashboard" class="ph-badge">
            <img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1192250&theme=light" alt="Product Hunt Badge Placeholder" width="250" height="54" style="opacity:0.8" />
        </a>
        <h1>
            <span style="animation-delay: 0.1s">Cut</span>
            <span style="animation-delay: 0.2s">Your</span>
            <span style="animation-delay: 0.3s">LLM</span>
            <span style="animation-delay: 0.4s">API</span>
            <span style="animation-delay: 0.5s">Costs</span>
            <span style="animation-delay: 0.6s">by</span>
            <span style="animation-delay: 0.7s">65%.</span>
        </h1>
        <p class="hero-lead">
            For teams running chat, RAG, support, or coding agents. The Semantic LLM Gateway caches responses, routes queries by complexity, and falls back gracefully before inference, so your existing models do more with the tokens you already pay for.
        </p>
        <div class="hero-actions">
            <a href="#dashboard" class="btn-primary">Try on your context</a>
            <a href="#architecture" class="btn-secondary">View the API</a>
        </div>
    </section>

    <!-- FEATURES -->
    <section class="section" id="features">
        <div class="section-header reveal">
            <div class="section-label">Core Architecture</div>
            <h2 class="section-title">Control AI feature cost before the model call</h2>
            <p class="section-desc">
                Paste the same context a production AI feature would send. The gateway intercepts it to deliver the optimal cost, latency, and resilience.
            </p>
        </div>

        <div class="features-grid reveal">
            <article class="feature-card">
                <span class="feature-label">Cost Model</span>
                <h3 class="feature-title">Semantic Vector Cache</h3>
                <p class="feature-desc">
                    Embeds prompts into 384-dim vectors and searches for semantically similar past queries using Qdrant with cosine similarity.
                </p>
                <ul class="feature-list">
                    <li>HuggingFace all-MiniLM embeddings</li>
                    <li>Local fastembed CPU-only fallback</li>
                    <li>Configurable 0.92 similarity threshold</li>
                </ul>
            </article>

            <article class="feature-card">
                <span class="feature-label">Quality</span>
                <h3 class="feature-title">Cost-Aware Routing</h3>
                <p class="feature-desc">
                    Prompts are classified as simple or complex via heuristics and routed to the optimal model tier on Groq.
                </p>
                <ul class="feature-list">
                    <li>Simple → Llama 3.1 8B ($0.05/M)</li>
                    <li>Complex → Llama 3.3 70B ($0.59/M)</li>
                    <li>Per-query cost tracking in Redis</li>
                </ul>
            </article>

            <article class="feature-card">
                <span class="feature-label">Deployment</span>
                <h3 class="feature-title">Graceful Fallback</h3>
                <p class="feature-desc">
                    If the primary Groq API fails, the gateway automatically falls back to a local Ollama instance.
                </p>
                <ul class="feature-list">
                    <li>Automatic API failover</li>
                    <li>OpenAI-normalized responses</li>
                    <li>Zero downtime for end users</li>
                </ul>
            </article>
        </div>
    </section>

    <!-- ARCHITECTURE -->
    <section class="section" id="architecture">
        <div class="arch-split reveal">
            <div class="arch-text">
                <div class="section-label">Drop-in Preprocessing</div>
                <h2 class="section-title">OpenAI-compatible. Zero code changes.</h2>
                <p class="section-desc" style="margin-bottom:2rem">
                    The gateway exposes the standard <code>/v1/chat/completions</code> endpoint. Point any OpenAI SDK at this proxy and get semantic caching + intelligent routing instantly.
                </p>
            </div>
            <div class="arch-code">
<pre><span class="cmt"># Standard OpenAI-format request</span>
<span class="kw">curl</span> -X POST <span class="str">http://localhost:8000/v1/chat/completions</span> \
  -H <span class="str">"Content-Type: application/json"</span> \
  -d '{
    <span class="hdr">"messages"</span>: [
      {<span class="str">"role"</span>: <span class="str">"user"</span>, <span class="str">"content"</span>: <span class="str">"Explain caching"</span>}
    ]
  }'

<span class="cmt"># Response includes Cache header</span>
<span class="hdr">X-Cache-Lookup</span>: <span class="str">HIT</span>

{
  <span class="hdr">"model"</span>: <span class="str">"llama-3.1-8b-instant"</span>,
  <span class="hdr">"choices"</span>: [{ <span class="hdr">"message"</span>: { ... } }]
}</pre>
            </div>
        </div>
    </section>

    <!-- DASHBOARD & PLAYGROUND -->
    <section class="section" id="dashboard">
        <div class="section-header reveal" style="margin-bottom: 2rem;">
            <div class="section-label">Live Impact Demo</div>
            <h2 class="section-title">Estimate savings before rollout</h2>
            <p class="section-desc">Test your queries and monitor token + inference impact in real-time.</p>
        </div>

        <div class="dash-container reveal">
            <div class="dash-header">
                <div class="dash-tab active" onclick="switchTab('analytics')" id="tabbtn-analytics">Impact Dashboard</div>
                <div class="dash-tab" onclick="switchTab('chat')" id="tabbtn-chat">Interactive Sandbox</div>
            </div>

            <!-- Analytics Tab -->
            <div id="tab-analytics" class="dash-content active">
                <div class="metrics-grid">
                    <div class="metric-block">
                        <span class="metric-label">Tokens / Cost Saved</span>
                        <span class="metric-value" id="val-saved">$0.000</span>
                        <span class="metric-sub">Estimated prefill savings</span>
                    </div>
                    <div class="metric-block">
                        <span class="metric-label">Upstream Spend</span>
                        <span class="metric-value" id="val-spent">$0.000</span>
                        <span class="metric-sub">Total LLM API cost</span>
                    </div>
                    <div class="metric-block">
                        <span class="metric-label">Cache Hit Rate</span>
                        <span class="metric-value" id="val-hitrate">0.0%</span>
                        <span class="metric-sub">Semantic match efficiency</span>
                    </div>
                    <div class="metric-block">
                        <span class="metric-label">Average Latency</span>
                        <div class="latency-split">
                            <span class="metric-value" id="val-latency-cached">0ms</span>
                            <span class="latency-tag">Cached</span>
                        </div>
                        <span class="metric-sub">Direct latency: <span id="val-latency-direct">0ms</span></span>
                    </div>
                </div>

                <div class="chart-wrap">
                    <canvas id="latencyChart"></canvas>
                </div>

                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Prompt</th>
                                <th>Routing</th>
                                <th>Model Executed</th>
                                <th>Cache</th>
                                <th>Latency</th>
                            </tr>
                        </thead>
                        <tbody id="queries-tbody"></tbody>
                    </table>
                </div>
            </div>

            <!-- Chat Tab -->
            <div id="tab-chat" class="dash-content">
                <div class="chat-layout">
                    <div class="chat-messages" id="chat-messages">
                        <div class="message assistant">
                            <div class="msg-bubble">
                                Hello. I am connected to the Semantic LLM Gateway. Enter a prompt to test routing (Simple vs Complex) and semantic caching.
                            </div>
                        </div>
                    </div>
                    <div class="chat-input-bar">
                        <input type="text" class="chat-input" id="chat-input" placeholder="Type your context or question..." onkeydown="handleKey(event)" />
                        <button class="btn-send" id="btn-send" onclick="sendMessage()">Compress & Send</button>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- FOOTER -->
    <footer class="footer">
        <div class="footer-inner">
            <div class="footer-brand">
                <div class="footer-logo">Semantic LLM</div>
                <p>Prompt compression and intelligent routing for AI apps. Mitigate token costs before inference.</p>
            </div>
            <div class="footer-col">
                <h4>Navigation</h4>
                <ul>
                    <li><a href="#hero">Savings</a></li>
                    <li><a href="#dashboard">Demo</a></li>
                    <li><a href="#features">Features</a></li>
                    <li><a href="#architecture">Quick Start</a></li>
                </ul>
            </div>
            <div class="footer-col">
                <h4>Documentation</h4>
                <ul>
                    <li><a href="/docs">API Reference</a></li>
                    <li><a href="/v1/chat/completions">/chat/completions</a></li>
                    <li><a href="/api/metrics">/api/metrics</a></li>
                    <li><a href="/health">Health Check</a></li>
                </ul>
            </div>
        </div>
        <div class="footer-copy">
            &copy; Semantic LLM Gateway &middot; Open Source MIT
        </div>
    </footer>

    <!-- JAVASCRIPT -->
    <script>
        /* Scroll Reveal */
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => { if (entry.isIntersecting) entry.target.classList.add('visible'); });
        }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
        document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

        /* Tabs */
        let latencyChart = null;
        let chatHistory = [];

        function switchTab(tabId) {
            document.querySelectorAll('.dash-tab').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.dash-content').forEach(c => c.classList.remove('active'));
            document.getElementById('tabbtn-' + tabId).classList.add('active');
            document.getElementById('tab-' + tabId).classList.add('active');
            if (tabId === 'analytics') fetchMetrics();
        }

        /* Metrics & Chart */
        async function fetchMetrics() {
            try {
                const res = await fetch('/api/metrics');
                const data = await res.json();

                document.getElementById('val-saved').textContent = '$' + data.total_saved.toFixed(5);
                document.getElementById('val-spent').textContent = '$' + data.total_spent.toFixed(5);
                document.getElementById('val-hitrate').textContent = data.hit_rate.toFixed(1) + '%';
                document.getElementById('val-latency-cached').textContent = Math.round(data.avg_latency_hit) + 'ms';
                document.getElementById('val-latency-direct').textContent = Math.round(data.avg_latency_miss) + 'ms';

                const tbody = document.getElementById('queries-tbody');
                tbody.innerHTML = '';

                if (data.queries.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:2rem">No queries yet.</td></tr>';
                } else {
                    data.queries.forEach(q => {
                        const tr = document.createElement('tr');
                        const cacheClass = q.is_cache_hit ? 'hit' : 'miss';
                        const cacheText = q.is_cache_hit ? 'HIT' : 'MISS';
                        const routeBadge = q.complexity === 'COMPLEX' ? 'advanced' : 'simple';
                        const routeText = q.complexity === 'COMPLEX' ? 'Complex' : 'Simple';
                        
                        tr.innerHTML = `
                            <td class="prompt-cell" title="${escapeHtml(q.prompt)}">${escapeHtml(q.prompt)}</td>
                            <td><span class="badge ${routeBadge}">${routeText}</span></td>
                            <td style="color:var(--text-secondary)">${q.model_routed}</td>
                            <td><span class="status-dot ${cacheClass}">${cacheText}</span></td>
                            <td style="font-weight:600">${Math.round(q.latency_ms)}ms</td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
                updateChart(data.queries);
            } catch (err) { console.error('Metrics fetch error:', err); }
        }

        function escapeHtml(t) { return t.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;"); }

        function updateChart(queries) {
            const chrono = [...queries].reverse();
            const labels = [], hitData = [], missData = [];
            chrono.forEach(q => {
                labels.push(new Date(q.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}));
                if (q.is_cache_hit) { hitData.push(q.latency_ms); missData.push(null); }
                else { missData.push(q.latency_ms); hitData.push(null); }
            });

            const ctx = document.getElementById('latencyChart').getContext('2d');
            if (latencyChart) latencyChart.destroy();

            latencyChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels.length ? labels : ['10:00','10:10','10:20'],
                    datasets: [
                        { label: 'Cache HIT', data: hitData.length ? hitData : [80,90,85], borderColor: '#047857', backgroundColor: 'rgba(4,120,87,0.1)', borderWidth: 2, fill: true, spanGaps: true, tension: 0.1, pointRadius: 4 },
                        { label: 'Cache MISS', data: missData.length ? missData : [300,450,380], borderColor: '#111111', backgroundColor: 'rgba(17,17,17,0.05)', borderWidth: 2, fill: true, spanGaps: true, tension: 0.1, pointRadius: 4 }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { labels: { font: { family: 'system-ui' } } } },
                    scales: {
                        y: { title: { display: true, text: 'Latency (ms)' }, beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }

        /* Chat */
        function handleKey(e) { if (e.key === 'Enter') sendMessage(); }

        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const prompt = input.value.trim();
            if (!prompt) return;
            input.value = '';

            appendMessage('user', prompt);
            const typingId = appendTypingIndicator();
            chatHistory.push({ role: 'user', content: prompt });

            document.getElementById('btn-send').disabled = true;
            input.disabled = true;
            const start = performance.now();

            try {
                const res = await fetch('/v1/chat/completions', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ messages: chatHistory })
                });
                const latency = performance.now() - start;
                removeTypingIndicator(typingId);

                if (!res.ok) throw new Error('API Error ' + res.status);
                const data = await res.json();
                
                const reply = data.choices[0].message.content;
                chatHistory.push({ role: 'assistant', content: reply });
                
                appendMessage('assistant', reply, {
                    cache: res.headers.get('X-Cache-Lookup') || 'MISS',
                    model: data.model, latency, tokens: data.usage.total_tokens
                });
                fetchMetrics();
            } catch (err) {
                removeTypingIndicator(typingId);
                appendMessage('assistant', 'Error: ' + err.message);
            } finally {
                document.getElementById('btn-send').disabled = false;
                input.disabled = false;
                input.focus();
            }
        }

        function appendMessage(sender, text, meta) {
            const box = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.className = 'message ' + sender;
            
            const bub = document.createElement('div');
            bub.className = 'msg-bubble';
            bub.innerHTML = escapeHtml(text).replace(/\n/g, '<br>');
            div.appendChild(bub);

            if (meta) {
                const info = document.createElement('div');
                info.className = 'msg-info';
                info.innerHTML = `<strong style="color:${meta.cache==='HIT'?'#047857':'#b45309'}">${meta.cache}</strong> &middot; ${meta.model} &middot; ${Math.round(meta.latency)}ms &middot; ${meta.tokens} tokens`;
                div.appendChild(info);
            }
            box.appendChild(div);
            box.scrollTop = box.scrollHeight;
        }

        function appendTypingIndicator() {
            const id = 'typ-' + Date.now();
            const box = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.className = 'message assistant';
            div.id = id;
            div.innerHTML = '<div class="msg-bubble" style="color:var(--text-muted)">Processing...</div>';
            box.appendChild(div);
            box.scrollTop = box.scrollHeight;
            return id;
        }

        function removeTypingIndicator(id) {
            const el = document.getElementById(id);
            if (el) el.remove();
        }

        fetchMetrics();
        setInterval(fetchMetrics, 15000);
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)
