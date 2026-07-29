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
    Serves the redesigned Semantic LLM Gateway dashboard with true editorial aesthetic.
    """
    html_content = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Semantic LLM Gateway</title>
    <meta name="description" content="An intelligent LLM proxy with semantic caching, cost-aware model routing, and graceful fallback.">
    <!-- Import Google Fonts: Inter for sans-serif UI, Lora for editorial serif -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Lora:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        /* ═══════════════════════════════════════════
           DESIGN SYSTEM (True Editorial Aesthetic)
           ═══════════════════════════════════════════ */
        :root {
            --bg: rgb(251, 251, 248);
            --surface-gray: #f5f5f5;
            --border: #eaeaea;
            --border-dark: #d4d4d4;
            --text-primary: #111111;
            --text-secondary: #555555;
            --text-muted: #888888;
            --blue: #2563eb;
            --blue-hover: #1d4ed8;
            --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
            --font-serif: 'Lora', Georgia, 'Times New Roman', serif;
            --mono: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        html { scroll-behavior: smooth; }

        body {
            font-family: var(--font-sans);
            background: var(--bg);
            color: var(--text-primary);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            overflow-x: hidden;
        }

        /* ═══════════════════════════════════════════
           NAVIGATION
           ═══════════════════════════════════════════ */
        .nav {
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(8px);
            border-bottom: 1px solid rgba(0,0,0,0.05);
            padding: 0.75rem 0;
        }

        .nav-inner {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .nav-logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            text-decoration: none;
            color: var(--text-primary);
            font-size: 1.2rem;
        }
        
        .nav-logo-mark {
            width: 24px;
            height: 24px;
            background: var(--blue);
            mask: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>') no-repeat center;
            -webkit-mask: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>') no-repeat center;
        }

        .nav-logo-word {
            font-weight: 500;
            letter-spacing: -0.01em;
        }
        .nav-logo-word em {
            font-style: italic;
            font-family: var(--font-serif);
            color: var(--blue);
        }

        .nav-pill-group {
            display: flex;
            align-items: center;
            background: #ffffff;
            border: 1px solid rgba(0,0,0,0.1);
            border-radius: 6px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.03);
            overflow: hidden;
        }

        .nav-pill-link {
            text-decoration: none;
            color: var(--text-primary);
            font-size: 0.825rem;
            font-weight: 500;
            padding: 0.5rem 1.25rem;
            border-right: 1px solid rgba(0,0,0,0.06);
            transition: background 0.2s;
        }
        .nav-pill-link:last-child {
            border-right: none;
        }

        .nav-pill-link:hover {
            background: var(--surface-gray);
        }

        .nav-pill-solo {
            background: #ffffff;
            border: 1px solid rgba(0,0,0,0.1);
            border-radius: 6px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.03);
            padding: 0.5rem 1.25rem;
            text-decoration: none;
            color: var(--text-primary);
            font-size: 0.825rem;
            font-weight: 500;
            transition: background 0.2s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .nav-pill-solo:hover {
            background: var(--surface-gray);
        }

        /* ═══════════════════════════════════════════
           TYPOGRAPHY & BUTTONS
           ═══════════════════════════════════════════ */
        h1, h2, h3 {
            font-family: var(--font-sans);
            font-weight: 600;
            color: var(--text-primary);
            letter-spacing: -0.03em;
        }

        .btn-blue {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #111111;
            color: #ffffff;
            text-decoration: none;
            font-size: 0.95rem;
            font-weight: 500;
            padding: 0.8rem 1.75rem;
            border-radius: 8px;
            transition: all 0.2s;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 4px 14px 0 rgba(0,0,0,0.1);
            cursor: pointer;
        }
        .btn-blue:hover { background: #333333; transform: translateY(-1px); box-shadow: 0 6px 20px rgba(0,0,0,0.15); }

        .btn-link {
            display: inline-block;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.9rem;
            margin-left: 1rem;
        }
        .btn-link:hover { color: var(--text-primary); text-decoration: underline; }

        /* ═══════════════════════════════════════════
           SECTION 1: HERO
           ═══════════════════════════════════════════ */
        .section-hero {
            padding: 8rem 2rem 6rem;
            max-width: 1000px;
            margin: 0;
            text-align: left;
        }

        .hero-title {
            font-size: clamp(3rem, 7vw, 4.8rem);
            line-height: 1.05;
            font-weight: 600;
            letter-spacing: -0.04em;
            margin-bottom: 1.5rem;
        }

        .hero-subtitle {
            font-size: 1.15rem;
            line-height: 1.6;
            color: var(--text-secondary);
            max-width: 700px;
            margin: 0 0 3rem 0;
        }

        /* ═══════════════════════════════════════════
           SECTION 2: TERMINAL SPLIT
           ═══════════════════════════════════════════ */
        .section-split {
            max-width: 1200px;
            margin: 0 auto;
            padding: 4rem 2rem;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4rem;
            align-items: center;
        }

        .split-eyebrow {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--blue);
            font-weight: 700;
            margin-bottom: 1rem;
        }

        .split-title {
            font-size: 3rem;
            line-height: 1.1;
            margin-bottom: 1.5rem;
        }

        .split-desc {
            font-size: 1rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }

        .terminal-window {
            background: #111111;
            border-radius: 8px;
            box-shadow: 0 24px 48px rgba(0,0,0,0.15);
            overflow: hidden;
            width: 100%;
        }

        .terminal-header {
            background: #1c1c1e;
            padding: 0.75rem 1rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        .terminal-dot { width: 10px; height: 10px; border-radius: 50%; }
        .terminal-dot.r { background: #ff5f56; }
        .terminal-dot.y { background: #ffbd2e; }
        .terminal-dot.g { background: #27c93f; }
        
        .terminal-title {
            margin-left: 1rem;
            color: #888;
            font-size: 0.75rem;
            font-family: var(--mono);
        }

        .terminal-body {
            padding: 1.5rem;
            font-family: var(--mono);
            font-size: 0.85rem;
            color: #fff;
            line-height: 1.8;
        }

        .term-check { color: #27c93f; margin-right: 0.5rem; }
        .term-prompt { color: #888; margin-top: 1rem; }

        /* ═══════════════════════════════════════════
           SECTION 3: EDITORIAL CARDS
           ═══════════════════════════════════════════ */
        .section-cards {
            max-width: 1200px;
            margin: 4rem auto;
            padding: 0 2rem;
        }

        .cards-header {
            text-align: center;
            max-width: 700px;
            margin: 0 auto 3rem;
        }

        .cards-header h2 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }

        .cards-header p {
            color: var(--text-secondary);
        }

        .cards-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
        }

        .ed-card {
            background: var(--surface-gray);
            padding: 2rem;
            border-radius: 6px;
        }

        .ed-card-label {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 1rem;
            display: block;
        }

        .ed-card-title {
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 1rem;
            font-family: var(--font-sans);
        }

        .ed-card p {
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-bottom: 1.5rem;
        }

        .ed-card ul {
            list-style: none;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .ed-card ul li {
            position: relative;
            padding-left: 1rem;
            margin-bottom: 0.5rem;
        }
        .ed-card ul li::before {
            content: '•';
            position: absolute;
            left: 0;
            color: var(--text-muted);
        }

        /* ═══════════════════════════════════════════
           SECTION 4: TABS & DASHBOARD
           ═══════════════════════════════════════════ */
        .section-demo {
            max-width: 1200px;
            margin: 6rem auto;
            padding: 0 2rem;
        }

        .dash-tab-wrap {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 3rem;
            border-bottom: 1px solid var(--border);
        }

        .dash-tab {
            padding: 0.5rem 0.5rem;
            font-size: 0.9rem;
            font-weight: 500;
            color: var(--text-secondary);
            cursor: pointer;
            border-bottom: 2px solid transparent;
            margin-bottom: -1px;
        }

        .dash-tab.active {
            color: var(--blue);
            border-bottom: 2px solid var(--blue);
        }

        .dash-content {
            visibility: hidden;
            position: absolute;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
            width: 100%;
        }

        .dash-content.active {
            visibility: visible;
            position: relative;
            opacity: 1;
            pointer-events: auto;
        }

        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

        /* Split Demo Layout (Sandbox) */
        .demo-split {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4rem;
        }

        .demo-label {
            font-size: 0.7rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 1rem;
            display: block;
        }

        /* Left Side: Chat UI */
        .chat-container {
            border: 1px solid var(--border);
            border-radius: 6px;
            background: #ffffff;
            display: flex;
            flex-direction: column;
            height: 450px;
        }

        .chat-messages {
            flex: 1;
            padding: 1.5rem;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .message {
            display: flex;
            flex-direction: column;
        }
        .message.user { align-items: flex-end; }
        .message.assistant { align-items: flex-start; }

        .msg-bubble {
            max-width: 85%;
            padding: 0.8rem 1rem;
            border-radius: 6px;
            font-size: 0.9rem;
            line-height: 1.5;
        }
        .message.user .msg-bubble {
            background: var(--blue);
            color: #ffffff;
        }
        .message.assistant .msg-bubble {
            background: var(--surface-gray);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }

        .chat-input-bar {
            padding: 1rem;
            border-top: 1px solid var(--border);
            display: flex;
            gap: 0.5rem;
        }

        .chat-input {
            flex: 1;
            padding: 0.8rem 1rem;
            border: 1px solid var(--border);
            border-radius: 6px;
            font-family: var(--font-sans);
            font-size: 0.95rem;
            outline: none;
        }
        .chat-input:focus { border-color: var(--blue); }

        /* Right Side: Stats List */
        .stats-list { list-style: none; margin-top: -0.5rem; }
        .stat-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.25rem 0;
            border-bottom: 1px solid var(--border);
            font-size: 0.9rem;
        }
        .stat-row:last-child { border-bottom: none; }
        .stat-name { color: var(--text-secondary); }
        .stat-value { font-weight: 500; color: var(--text-primary); text-align: right; }
        .stat-value.blue { color: var(--blue); }
        .stat-sub { font-size: 0.7rem; color: var(--text-muted); display: block; }

        /* Analytics Tab Layout */
        .analytics-layout {
            display: flex;
            flex-direction: column;
            gap: 3rem;
        }

        .chart-wrap {
            border: 1px solid var(--border);
            border-radius: 6px;
            background: #ffffff;
            padding: 2rem;
            height: 300px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }
        th, td {
            text-align: left;
            padding: 1rem;
            border-bottom: 1px solid var(--border);
        }
        th { color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 0.7rem; }
        .status-dot {
            display: inline-block;
            width: 8px; height: 8px;
            border-radius: 50%;
            margin-right: 0.5rem;
        }
        .status-dot.hit { background: #10b981; }
        .status-dot.miss { background: #ef4444; }
        
        .badge {
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
        }
        .badge.simple { background: #f1f5f9; color: #475569; }
        .badge.advanced { background: #ede9fe; color: #7c3aed; }

        /* ═══════════════════════════════════════════
           FOOTER
           ═══════════════════════════════════════════ */
        .footer {
            background: #111111;
            color: #ffffff;
            padding: 4rem 2rem;
            margin-top: 4rem;
        }

        .footer-inner {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1fr;
            gap: 3rem;
        }

        .footer-brand h4 { font-family: var(--font-sans); margin-bottom: 1rem; }
        .footer-brand p { font-size: 0.85rem; color: #888; line-height: 1.6; }
        
        .footer-col h5 { font-size: 0.85rem; color: #fff; margin-bottom: 1rem; font-weight: 500;}
        .footer-col ul { list-style: none; }
        .footer-col li { margin-bottom: 0.5rem; }
        .footer-col a { color: #888; text-decoration: none; font-size: 0.85rem; transition: color 0.2s; }
        .footer-col a:hover { color: #fff; }

        /* Mobile */
        @media (max-width: 768px) {
            .section-split, .cards-grid, .demo-split, .footer-inner { grid-template-columns: 1fr; gap: 2rem; }
            .nav-pill-group { display: none; }
            .hero-title, .split-title { font-size: 2.5rem; }
        }
    </style>
</head>
<body>

    <!-- NAVIGATION -->
    <nav class="nav">
        <div class="nav-inner">
            <a href="/" class="nav-logo">
                <div class="nav-logo-mark"></div>
                <span class="nav-logo-word">Semantic<em>Gateway</em></span>
            </a>
            <div class="nav-pill-group">
                <a href="#features" class="nav-pill-link">Guide</a>
                <a href="#demo" class="nav-pill-link">Savings</a>
                <a href="#demo" class="nav-pill-link">Demo</a>
                <a href="#quickstart" class="nav-pill-link">Quick start</a>
            </div>
            <div style="display:flex; gap:0.75rem">
                <a href="/docs" class="nav-pill-solo">Docs</a>
                <a href="#demo" class="nav-pill-solo">Dashboard</a>
                <a href="https://github.com/anothercodingguy/SemanticLLM" target="_blank" class="nav-pill-solo" style="padding: 0.5rem;">
                    <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" class="css-i6dzq1"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
                </a>
            </div>
        </div>
    </nav>

    <!-- HERO -->
    <section class="section-hero" id="hero">
        <h1 class="hero-title">Cut Your LLM API Costs by 65%.</h1>
        <p class="hero-subtitle">
            For teams running chat, RAG, support, or coding agents. Semantic Gateway removes low-value context before inference, so your existing models do more with the tokens you already pay for.
        </p>
        <div style="display:flex; align-items:center; gap: 1rem;">
            <a href="#quickstart" class="btn-blue">Install the agent plugin</a>
            <a href="#demo" class="btn-link" style="margin-left:0; font-size:0.9rem; color:#888; text-decoration:none;">Try it on your context ↗</a>
        </div>
    </section>

    <!-- TERMINAL SPLIT -->
    <section class="section-split" id="quickstart">
        <div>
            <div class="split-eyebrow">INTELLIGENT ROUTING · API-FIRST</div>
            <h2 class="split-title">One endpoint.<br>Every LLM.<br>Fewer tokens.</h2>
            <p class="split-desc">
                Auto-detect context similarity. The gateway intercepts huge context dumps before they burn tokens, routing via Groq Llama 3 or falling back to local Ollama.
            </p>
            <a href="/docs" class="btn-blue">Install the gateway</a>
            <a href="#demo" class="btn-link">See how it works &#8599;</a>
        </div>
        <div class="terminal-window">
            <div class="terminal-header">
                <div class="terminal-dot r"></div>
                <div class="terminal-dot y"></div>
                <div class="terminal-dot g"></div>
                <div class="terminal-title">semantic-gateway status</div>
            </div>
            <div class="terminal-body">
                <div><span class="term-check">✓</span> Detected Groq Llama-3.1-8B Instant</div>
                <div><span class="term-check">✓</span> Detected Groq Llama-3.3-70B Versatile</div>
                <div><span class="term-check">✓</span> Redis metrics connected</div>
                <div><span class="term-check">✓</span> Qdrant vector store loaded</div>
                <br>
                <div class="term-prompt">Listening on http://localhost:8000/v1/chat/completions ▋</div>
            </div>
        </div>
    </section>

    <!-- EDITORIAL CARDS -->
    <section class="section-cards" id="features">
        <div class="cards-header">
            <h2>Control AI feature cost before the model call</h2>
            <p>Paste the same context a production AI feature would send: chat history, retrieval output, support logs. The gateway optimizes it before the request reaches the model.</p>
        </div>
        <div class="cards-grid">
            <article class="ed-card">
                <span class="ed-card-label">Cost model</span>
                <h3 class="ed-card-title">Semantic Vector Cache</h3>
                <p>Instead of blind string matching, the gateway embeds prompts into 384-dim vectors to catch semantically similar queries.</p>
                <ul>
                    <li>HuggingFace embeddings (fastembed)</li>
                    <li>Sub-100ms response on hits</li>
                </ul>
            </article>
            <article class="ed-card">
                <span class="ed-card-label">Quality</span>
                <h3 class="ed-card-title">Complexity Routing</h3>
                <p>Simple queries go to fast, cheap models (Llama 8B). Complex queries scale up to 70B automatically.</p>
                <ul>
                    <li>$0.05/M vs $0.59/M routing</li>
                    <li>Per-query cost tracking</li>
                </ul>
            </article>
            <article class="ed-card">
                <span class="ed-card-label">Deployment</span>
                <h3 class="ed-card-title">Graceful Fallback</h3>
                <p>Run locally or in production. If the primary Groq API fails, the gateway fails over to Ollama instantly.</p>
                <ul>
                    <li>OpenAI-compatible endpoints</li>
                    <li>Zero downtime for end users</li>
                </ul>
            </article>
        </div>
    </section>

    <!-- IMPACT DEMO (TABS) -->
    <section class="section-demo" id="demo">
        <div class="dash-tab-wrap">
            <div class="dash-tab active" id="tabbtn-sandbox" onclick="switchTab('sandbox')">Interactive Sandbox</div>
            <div class="dash-tab" id="tabbtn-analytics" onclick="switchTab('analytics')">Impact Dashboard</div>
        </div>

        <!-- Tab 1: Interactive Sandbox (Split) -->
        <div id="tab-sandbox" class="dash-content active">
            <div class="demo-split">
                <!-- Left: Form -->
                <div>
                    <span class="demo-label">USER REQUEST</span>
                    
                    <div class="chat-container">
                        <div class="chat-messages" id="chat-messages">
                            <div class="message assistant">
                                <div class="msg-bubble">
                                    Hello. I am connected to the Semantic LLM Gateway. Enter a prompt to test routing (Simple vs Complex) and semantic caching.
                                </div>
                            </div>
                        </div>
                        <div class="chat-input-bar">
                            <input type="text" class="chat-input" id="chat-input" placeholder="What does fetch_user return when the row is missing?" onkeydown="handleKey(event)" />
                            <button class="btn-blue" id="btn-send" onclick="sendMessage()">Compress</button>
                        </div>
                    </div>
                    
                    <p style="font-size:0.8rem; color:var(--text-muted); margin-top:1.5rem;">
                        Runs locally with the Semantic Gateway. The user request defines what matters, so duplicate history, irrelevant chunks, and noise are caught via cache or routed cheaply.
                    </p>
                </div>

                <!-- Right: Stats -->
                <div>
                    <span class="demo-label">TOKEN & INFERENCE IMPACT</span>
                    <ul class="stats-list">
                        <li class="stat-row">
                            <span class="stat-name">Total Requests Analyzed</span>
                            <span class="stat-value" id="val-requests">—</span>
                        </li>
                        <li class="stat-row">
                            <span class="stat-name">Cache Hits</span>
                            <span class="stat-value" id="val-hits">—</span>
                        </li>
                        <li class="stat-row">
                            <span class="stat-name">Cache Efficiency</span>
                            <span class="stat-value blue" id="val-hitrate">—</span>
                        </li>
                        <li class="stat-row">
                            <span class="stat-name">API Spend Estimated</span>
                            <span class="stat-value" id="val-spent">—</span>
                        </li>
                        <li class="stat-row">
                            <span class="stat-name">API Cost Saved</span>
                            <span class="stat-value blue" id="val-saved">—</span>
                        </li>
                        <li class="stat-row">
                            <span class="stat-name">Latency (Direct)</span>
                            <div style="text-align:right">
                                <span class="stat-value" id="val-latency-direct">—</span>
                                <span class="stat-sub">avg. upstream</span>
                            </div>
                        </li>
                        <li class="stat-row">
                            <span class="stat-name">Latency (Cached)</span>
                            <div style="text-align:right">
                                <span class="stat-value blue" id="val-latency-cached">—</span>
                                <span class="stat-sub">avg. semantic hit</span>
                            </div>
                        </li>
                        <li class="stat-row">
                            <span class="stat-name">Latest Model Route</span>
                            <span class="stat-value" id="val-latest-route" style="font-family:var(--mono); font-size:0.8rem">—</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- Tab 2: Analytics -->
        <div id="tab-analytics" class="dash-content">
            <div class="analytics-layout">
                <div class="chart-wrap">
                    <canvas id="latencyChart"></canvas>
                </div>
                
                <div style="background:#fff; border: 1px solid var(--border); border-radius:6px; overflow:hidden;">
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
        </div>
    </section>

    <!-- FOOTER -->
    <footer class="footer">
        <div class="footer-inner">
            <div class="footer-brand">
                <h4>Semantic LLM</h4>
                <p>Prompt compression and intelligent routing for AI apps — reduce input tokens before inference.</p>
                <p style="margin-top:1rem; color:#666">Python library · hosted API · open source</p>
            </div>
            <div class="footer-col">
                <h5>Navigation</h5>
                <ul>
                    <li><a href="#demo">Savings</a></li>
                    <li><a href="#demo">Demo</a></li>
                    <li><a href="#features">Features</a></li>
                    <li><a href="#quickstart">Quick start</a></li>
                </ul>
            </div>
            <div class="footer-col">
                <h5>Resources</h5>
                <ul>
                    <li><a href="/docs">Token compression guide</a></li>
                    <li><a href="/docs">Benchmarks</a></li>
                    <li><a href="/api/metrics">Raw Metrics API</a></li>
                </ul>
            </div>
            <div class="footer-col">
                <h5>SEO Guides</h5>
                <ul>
                    <li><a href="/docs">Prompt compression</a></li>
                    <li><a href="/docs">LLM token cost</a></li>
                    <li><a href="/docs">Context limits</a></li>
                </ul>
            </div>
        </div>
    </footer>

    <!-- JAVASCRIPT -->
    <script>
        let chatHistory = [];
        let latencyChart = null;

        function escapeHtml(unsafe) {
            return (unsafe || '').toString()
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        function switchTab(tabId) {
            document.querySelectorAll('.dash-tab').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.dash-content').forEach(el => el.classList.remove('active'));
            document.getElementById('tabbtn-' + tabId).classList.add('active');
            document.getElementById('tab-' + tabId).classList.add('active');
            if(tabId === 'analytics') fetchMetrics();
        }

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
                    labels,
                    datasets: [
                        {
                            label: 'Cache Hit Latency (ms)',
                            data: hitData,
                            borderColor: '#2563eb',
                            backgroundColor: '#2563eb',
                            pointRadius: 5,
                            spanGaps: true
                        },
                        {
                            label: 'Upstream Miss Latency (ms)',
                            data: missData,
                            borderColor: '#ef4444',
                            backgroundColor: '#ef4444',
                            pointRadius: 5,
                            spanGaps: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top', labels: { boxWidth: 10, font: { family: 'Inter' } } }
                    },
                    scales: {
                        y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }

        async function fetchMetrics() {
            try {
                const res = await fetch('/api/metrics');
                if (!res.ok) return;
                const data = await res.json();

                document.getElementById('val-requests').textContent = data.total_requests;
                document.getElementById('val-hits').textContent = data.cache_hits;
                document.getElementById('val-hitrate').textContent = data.hit_rate.toFixed(1) + '%';
                document.getElementById('val-spent').textContent = '$' + data.total_spent.toFixed(5);
                document.getElementById('val-saved').textContent = '$' + data.total_saved.toFixed(5);
                
                document.getElementById('val-latency-direct').textContent = Math.round(data.avg_latency_miss) + 'ms';
                document.getElementById('val-latency-cached').textContent = Math.round(data.avg_latency_hit) + 'ms';

                if (data.queries && data.queries.length > 0) {
                    const latest = data.queries[0];
                    document.getElementById('val-latest-route').textContent = latest.model_routed + (latest.is_cache_hit ? " (CACHE)" : "");
                    
                    // Update table
                    const tbody = document.getElementById('queries-tbody');
                    tbody.innerHTML = '';
                    data.queries.forEach(q => {
                        const tr = document.createElement('tr');
                        const routeBadge = q.complexity === 'COMPLEX' ? 'advanced' : 'simple';
                        const cacheClass = q.is_cache_hit ? 'hit' : 'miss';
                        const cacheText = q.is_cache_hit ? 'Hit' : 'Miss';
                        tr.innerHTML = `
                            <td style="max-width:200px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${escapeHtml(q.prompt)}">${escapeHtml(q.prompt)}</td>
                            <td><span class="badge ${routeBadge}">${escapeHtml(q.complexity)}</span></td>
                            <td style="color:var(--text-secondary)">${escapeHtml(q.model_routed)}</td>
                            <td><span class="status-dot ${cacheClass}"></span>${cacheText}</td>
                            <td style="font-weight:500">${Math.round(q.latency_ms)}ms</td>
                        `;
                        tbody.appendChild(tr);
                    });
                    
                    updateChart(data.queries);
                }
            } catch (err) { console.error('Metrics fetch error:', err); }
        }

        function handleKey(e) { if (e.key === 'Enter') sendMessage(); }
        
        function appendMessage(role, text) {
            const container = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.className = 'message ' + role;
            div.innerHTML = `<div class="msg-bubble">${escapeHtml(text)}</div>`;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }

        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const prompt = input.value.trim();
            if (!prompt) return;
            
            chatHistory.push({ role: 'user', content: prompt });
            appendMessage('user', prompt);
            input.value = '';

            const btn = document.getElementById('btn-send');
            btn.disabled = true;
            btn.textContent = 'Processing...';

            try {
                const res = await fetch('/v1/chat/completions', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ messages: chatHistory })
                });
                
                if (res.ok) {
                    const data = await res.json();
                    const reply = data.choices[0].message.content;
                    chatHistory.push({ role: 'assistant', content: reply });
                    appendMessage('assistant', reply);
                    fetchMetrics();
                } else {
                    appendMessage('assistant', "Error communicating with Gateway.");
                }
            } catch (err) {
                console.error(err);
                appendMessage('assistant', "Network Error.");
            } finally {
                btn.disabled = false;
                btn.textContent = 'Compress';
                input.focus();
            }
        }

        fetchMetrics();
        setInterval(fetchMetrics, 5000);
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)
