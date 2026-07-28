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
    Serves the redesigned Semantic LLM Gateway dashboard and landing page.
    """
    html_content = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Semantic LLM Gateway — Cost-Aware Routing & Semantic Caching</title>
    <meta name="description" content="An intelligent LLM proxy with semantic caching, cost-aware model routing, and graceful fallback. OpenAI-compatible API that cuts costs and latency.">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        /* ═══════════════════════════════════════════
           DESIGN SYSTEM
           ═══════════════════════════════════════════ */
        :root {
            --bg: #050507;
            --bg-elevated: #0c0c10;
            --surface: #111116;
            --surface-hover: #18181e;
            --border: #1e1e26;
            --border-hover: #2a2a35;
            --text: #eeeef0;
            --text-secondary: #8a8a9a;
            --text-muted: #55556a;
            --accent: #7c5cfc;
            --accent-hover: #9070ff;
            --accent-glow: rgba(124, 92, 252, 0.15);
            --emerald: #34d399;
            --emerald-dim: rgba(52, 211, 153, 0.12);
            --amber: #fbbf24;
            --amber-dim: rgba(251, 191, 36, 0.12);
            --rose: #fb7185;
            --rose-dim: rgba(251, 113, 133, 0.12);
            --cyan: #22d3ee;
            --cyan-dim: rgba(34, 211, 238, 0.12);
            --radius: 14px;
            --radius-sm: 8px;
            --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
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
            backdrop-filter: blur(20px) saturate(1.4);
            -webkit-backdrop-filter: blur(20px) saturate(1.4);
            background: rgba(5, 5, 7, 0.78);
            border-bottom: 1px solid var(--border);
        }

        .nav-inner {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .nav-logo {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            text-decoration: none;
            color: var(--text);
            font-weight: 700;
            font-size: 1.05rem;
            letter-spacing: -0.02em;
        }

        .nav-logo-icon {
            width: 28px;
            height: 28px;
            background: linear-gradient(135deg, var(--accent), #a78bfa);
            border-radius: 7px;
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
            gap: 0.25rem;
        }

        .nav-links a {
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.8rem;
            font-weight: 500;
            padding: 0.4rem 0.85rem;
            border-radius: 6px;
            transition: all 0.2s;
        }

        .nav-links a:hover {
            color: var(--text);
            background: rgba(255,255,255,0.04);
        }

        .nav-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--emerald);
            background: var(--emerald-dim);
            border: 1px solid rgba(52, 211, 153, 0.2);
            padding: 0.3rem 0.7rem;
            border-radius: 20px;
            margin-left: 0.5rem;
        }

        .nav-badge::before {
            content: '';
            width: 6px;
            height: 6px;
            background: var(--emerald);
            border-radius: 50%;
            animation: pulse-dot 2s ease-in-out infinite;
        }

        @keyframes pulse-dot {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        /* ═══════════════════════════════════════════
           HERO
           ═══════════════════════════════════════════ */
        .hero {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 8rem 2rem 6rem;
            position: relative;
            overflow: hidden;
        }

        .hero::before {
            content: '';
            position: absolute;
            top: -40%;
            left: 50%;
            transform: translateX(-50%);
            width: 900px;
            height: 900px;
            background: radial-gradient(circle, rgba(124, 92, 252, 0.08) 0%, transparent 70%);
            pointer-events: none;
        }

        .hero::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 200px;
            background: linear-gradient(to top, var(--bg), transparent);
            pointer-events: none;
        }

        .hero-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--accent);
            background: var(--accent-glow);
            border: 1px solid rgba(124, 92, 252, 0.2);
            padding: 0.4rem 1rem;
            border-radius: 24px;
            margin-bottom: 2rem;
            animation: fadeSlideUp 0.6s ease both;
        }

        .hero h1 {
            font-size: clamp(2.8rem, 6vw, 5rem);
            font-weight: 800;
            letter-spacing: -0.04em;
            line-height: 1.05;
            max-width: 900px;
            margin-bottom: 1.5rem;
        }

        .hero h1 span {
            display: inline-block;
            opacity: 0;
            transform: translateY(30px);
            animation: wordReveal 0.5s ease forwards;
        }

        @keyframes wordReveal {
            to { opacity: 1; transform: translateY(0); }
        }

        .hero-gradient-text {
            background: linear-gradient(135deg, var(--accent), #a78bfa, var(--cyan));
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero-lead {
            font-size: 1.15rem;
            color: var(--text-secondary);
            max-width: 620px;
            margin: 0 auto 2.5rem;
            line-height: 1.7;
            animation: fadeSlideUp 0.6s 0.8s ease both;
        }

        .hero-actions {
            display: flex;
            gap: 1rem;
            justify-content: center;
            flex-wrap: wrap;
            animation: fadeSlideUp 0.6s 1s ease both;
        }

        @keyframes fadeSlideUp {
            from { opacity: 0; transform: translateY(16px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .btn-primary {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--accent);
            color: #fff;
            border: none;
            padding: 0.75rem 1.6rem;
            font-size: 0.875rem;
            font-weight: 600;
            font-family: var(--font);
            border-radius: var(--radius-sm);
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s;
        }

        .btn-primary:hover {
            background: var(--accent-hover);
            transform: translateY(-1px);
            box-shadow: 0 8px 30px rgba(124, 92, 252, 0.3);
        }

        .btn-secondary {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: transparent;
            color: var(--text-secondary);
            border: 1px solid var(--border);
            padding: 0.75rem 1.6rem;
            font-size: 0.875rem;
            font-weight: 500;
            font-family: var(--font);
            border-radius: var(--radius-sm);
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s;
        }

        .btn-secondary:hover {
            color: var(--text);
            border-color: var(--border-hover);
            background: rgba(255,255,255,0.03);
        }

        /* ═══════════════════════════════════════════
           STATS BAR
           ═══════════════════════════════════════════ */
        .stats-bar {
            max-width: 1200px;
            margin: -2rem auto 0;
            padding: 0 2rem;
            position: relative;
            z-index: 2;
        }

        .stats-bar-inner {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1px;
            background: var(--border);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            overflow: hidden;
        }

        .stat-item {
            background: var(--surface);
            padding: 1.5rem 1.75rem;
            text-align: center;
            transition: background 0.2s;
        }

        .stat-item:hover {
            background: var(--surface-hover);
        }

        .stat-value {
            font-size: 1.8rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 0.25rem;
        }

        .stat-value.accent { color: var(--accent); }
        .stat-value.emerald { color: var(--emerald); }
        .stat-value.amber { color: var(--amber); }
        .stat-value.cyan { color: var(--cyan); }

        .stat-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        /* ═══════════════════════════════════════════
           SECTIONS
           ═══════════════════════════════════════════ */
        .section {
            max-width: 1200px;
            margin: 0 auto;
            padding: 6rem 2rem;
        }

        .section-header {
            text-align: center;
            margin-bottom: 4rem;
        }

        .section-label {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--accent);
            margin-bottom: 1rem;
        }

        .section-title {
            font-size: clamp(1.8rem, 3.5vw, 2.6rem);
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 1rem;
        }

        .section-desc {
            font-size: 1.05rem;
            color: var(--text-secondary);
            max-width: 600px;
            margin: 0 auto;
            line-height: 1.7;
        }

        /* ═══════════════════════════════════════════
           HOW IT WORKS PIPELINE
           ═══════════════════════════════════════════ */
        .pipeline {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0;
            position: relative;
        }

        .pipeline::before {
            content: '';
            position: absolute;
            top: 44px;
            left: 12.5%;
            right: 12.5%;
            height: 2px;
            background: linear-gradient(90deg, var(--accent), var(--emerald), var(--amber), var(--cyan));
            opacity: 0.3;
        }

        .pipe-step {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            padding: 0 1rem;
            position: relative;
        }

        .pipe-icon {
            width: 88px;
            height: 88px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            margin-bottom: 1.25rem;
            position: relative;
            z-index: 2;
            border: 2px solid var(--border);
            transition: all 0.3s;
        }

        .pipe-step:hover .pipe-icon {
            transform: translateY(-4px);
            border-color: var(--border-hover);
        }

        .pipe-icon.i1 { background: linear-gradient(135deg, rgba(124,92,252,0.12), rgba(124,92,252,0.04)); color: var(--accent); }
        .pipe-icon.i2 { background: linear-gradient(135deg, rgba(52,211,153,0.12), rgba(52,211,153,0.04)); color: var(--emerald); }
        .pipe-icon.i3 { background: linear-gradient(135deg, rgba(251,191,36,0.12), rgba(251,191,36,0.04)); color: var(--amber); }
        .pipe-icon.i4 { background: linear-gradient(135deg, rgba(34,211,238,0.12), rgba(34,211,238,0.04)); color: var(--cyan); }

        .pipe-num {
            font-size: 0.65rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.5rem;
        }

        .pipe-title {
            font-size: 0.95rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .pipe-desc {
            font-size: 0.8rem;
            color: var(--text-secondary);
            line-height: 1.6;
        }

        /* ═══════════════════════════════════════════
           FEATURE CARDS
           ═══════════════════════════════════════════ */
        .features-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.25rem;
        }

        .feature-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 2rem;
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }

        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            opacity: 0;
            transition: opacity 0.3s;
        }

        .feature-card:hover {
            border-color: var(--border-hover);
            transform: translateY(-3px);
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }

        .feature-card:hover::before { opacity: 1; }

        .feature-card:nth-child(1)::before { background: linear-gradient(90deg, var(--accent), transparent); }
        .feature-card:nth-child(2)::before { background: linear-gradient(90deg, var(--emerald), transparent); }
        .feature-card:nth-child(3)::before { background: linear-gradient(90deg, var(--amber), transparent); }

        .feature-label {
            display: inline-flex;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            padding: 0.3rem 0.65rem;
            border-radius: 4px;
            margin-bottom: 1.25rem;
        }

        .feature-label.l-accent { color: var(--accent); background: var(--accent-glow); }
        .feature-label.l-emerald { color: var(--emerald); background: var(--emerald-dim); }
        .feature-label.l-amber { color: var(--amber); background: var(--amber-dim); }

        .feature-title {
            font-size: 1.15rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
            letter-spacing: -0.01em;
        }

        .feature-desc {
            font-size: 0.875rem;
            color: var(--text-secondary);
            line-height: 1.7;
            margin-bottom: 1.25rem;
        }

        .feature-list {
            list-style: none;
        }

        .feature-list li {
            font-size: 0.8rem;
            color: var(--text-secondary);
            padding: 0.35rem 0;
            padding-left: 1.2rem;
            position: relative;
        }

        .feature-list li::before {
            content: '\2192';
            position: absolute;
            left: 0;
            color: var(--text-muted);
        }

        /* ═══════════════════════════════════════════
           ARCHITECTURE / CODE BLOCK
           ═══════════════════════════════════════════ */
        .arch-section {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            overflow: hidden;
        }

        .arch-split {
            display: grid;
            grid-template-columns: 1fr 1fr;
        }

        .arch-text {
            padding: 3rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .arch-text h3 {
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 1rem;
            letter-spacing: -0.02em;
        }

        .arch-text p {
            font-size: 0.9rem;
            color: var(--text-secondary);
            line-height: 1.7;
            margin-bottom: 1.5rem;
        }

        .arch-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .arch-tag {
            font-size: 0.7rem;
            font-weight: 600;
            padding: 0.3rem 0.6rem;
            border-radius: 4px;
            background: rgba(255,255,255,0.04);
            border: 1px solid var(--border);
            color: var(--text-secondary);
        }

        .arch-code {
            background: #08080c;
            padding: 2.5rem;
            border-left: 1px solid var(--border);
            overflow-x: auto;
        }

        .arch-code pre {
            font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
            font-size: 0.78rem;
            line-height: 1.8;
            color: var(--text-secondary);
            white-space: pre;
        }

        .arch-code .kw { color: var(--accent); }
        .arch-code .str { color: var(--emerald); }
        .arch-code .cmt { color: var(--text-muted); font-style: italic; }
        .arch-code .num { color: var(--amber); }
        .arch-code .hdr { color: var(--cyan); }

        /* ═══════════════════════════════════════════
           DASHBOARD TABS
           ═══════════════════════════════════════════ */
        .dash-section {
            background: var(--bg-elevated);
            border-top: 1px solid var(--border);
            border-bottom: 1px solid var(--border);
        }

        .tabs-nav {
            display: flex;
            gap: 0.25rem;
            margin-bottom: 2rem;
            background: var(--surface);
            padding: 4px;
            border-radius: var(--radius-sm);
            border: 1px solid var(--border);
            width: fit-content;
        }

        .tab-btn {
            background: none;
            border: none;
            color: var(--text-muted);
            font-family: var(--font);
            font-size: 0.825rem;
            font-weight: 500;
            padding: 0.5rem 1.25rem;
            cursor: pointer;
            border-radius: 6px;
            transition: all 0.2s;
        }

        .tab-btn.active {
            color: #fff;
            background: var(--accent);
        }

        .tab-btn:hover:not(.active) {
            color: var(--text-secondary);
            background: rgba(255,255,255,0.03);
        }

        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* ═══════════════════════════════════════════
           METRICS GRID
           ═══════════════════════════════════════════ */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .metric-card {
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 1.25rem 1.5rem;
            border-radius: var(--radius);
            transition: all 0.25s;
        }

        .metric-card:hover {
            border-color: var(--border-hover);
            transform: translateY(-2px);
        }

        .metric-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }

        .metric-label {
            font-size: 0.7rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 600;
        }

        .metric-value {
            font-size: 1.75rem;
            font-weight: 800;
            letter-spacing: -0.03em;
        }

        .metric-sub {
            font-size: 0.72rem;
            color: var(--text-muted);
            margin-top: 0.35rem;
        }

        /* Latency split display */
        .latency-split {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .latency-split .metric-value {
            font-size: 1.3rem;
        }

        .latency-tag {
            font-size: 0.65rem;
            font-weight: 700;
            padding: 0.15rem 0.4rem;
            border-radius: 3px;
        }

        .latency-tag.cached {
            color: var(--emerald);
            background: var(--emerald-dim);
        }

        .latency-tag.direct {
            color: var(--text-muted);
            background: rgba(255,255,255,0.04);
        }

        /* Circular progress */
        .circ-prog {
            width: 30px;
            height: 30px;
        }

        .circ-prog svg { transform: rotate(-90deg); width: 100%; height: 100%; }
        .circ-bg { fill: none; stroke: rgba(255,255,255,0.04); stroke-width: 4; }
        .circ-fill { fill: none; stroke: var(--accent); stroke-width: 4; stroke-linecap: round; transition: stroke-dasharray 0.5s ease; }

        /* ═══════════════════════════════════════════
           DASHBOARD BODY (Chart + Table)
           ═══════════════════════════════════════════ */
        .dash-body {
            display: grid;
            grid-template-columns: 1.1fr 1fr;
            gap: 1.25rem;
        }

        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.5rem;
        }

        .card-title {
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 1.25rem;
            padding-left: 0.75rem;
            border-left: 2px solid var(--accent);
        }

        .chart-container {
            position: relative;
            height: 290px;
        }

        /* Table */
        .table-wrap { max-height: 370px; overflow-y: auto; }

        table { width: 100%; border-collapse: collapse; text-align: left; }

        th, td {
            padding: 0.7rem 0.6rem;
            border-bottom: 1px solid var(--border);
            font-size: 0.8rem;
        }

        th {
            color: var(--text-muted);
            font-weight: 600;
            background: var(--surface);
            position: sticky;
            top: 0;
            z-index: 5;
        }

        tr:hover { background: rgba(255,255,255,0.01); }

        .badge {
            display: inline-block;
            padding: 0.15rem 0.45rem;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 700;
        }

        .badge.simple { color: var(--text-secondary); background: rgba(255,255,255,0.04); }
        .badge.advanced { color: #a78bfa; background: rgba(124,92,252,0.1); border: 1px solid rgba(124,92,252,0.15); }

        .status-dot {
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            font-weight: 700;
            font-size: 0.72rem;
        }

        .status-dot::before {
            content: '';
            width: 5px;
            height: 5px;
            border-radius: 50%;
        }

        .status-dot.hit { color: var(--emerald); }
        .status-dot.hit::before { background: var(--emerald); }
        .status-dot.miss { color: var(--amber); }
        .status-dot.miss::before { background: var(--amber); }

        .prompt-text {
            max-width: 150px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* ═══════════════════════════════════════════
           CHAT SANDBOX
           ═══════════════════════════════════════════ */
        .chat-layout {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            height: 580px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
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
            max-width: 78%;
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
        }

        .message.user { align-self: flex-end; }
        .message.assistant { align-self: flex-start; }

        .msg-bubble {
            padding: 0.75rem 1.1rem;
            border-radius: var(--radius-sm);
            line-height: 1.6;
            font-size: 0.875rem;
        }

        .message.user .msg-bubble {
            background: var(--accent);
            color: #fff;
        }

        .message.assistant .msg-bubble {
            background: var(--bg);
            color: var(--text);
            border: 1px solid var(--border);
        }

        .message.system-message { align-self: stretch; max-width: 100%; }

        .message.system-message .msg-bubble {
            background: transparent;
            border: 1px dashed var(--border);
            color: var(--text-muted);
            font-size: 0.825rem;
            text-align: center;
        }

        .msg-info {
            font-size: 0.7rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        }

        .chat-input-bar {
            display: flex;
            gap: 0.65rem;
            padding: 1.15rem;
            background: rgba(0,0,0,0.2);
            border-top: 1px solid var(--border);
        }

        .chat-input {
            flex: 1;
            background: var(--bg);
            border: 1px solid var(--border);
            color: var(--text);
            border-radius: var(--radius-sm);
            padding: 0.75rem 1rem;
            font-family: var(--font);
            font-size: 0.875rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .chat-input:focus { border-color: var(--accent); }

        .btn-send {
            background: var(--accent);
            color: #fff;
            border: none;
            padding: 0.75rem 1.4rem;
            border-radius: var(--radius-sm);
            font-family: var(--font);
            font-weight: 600;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-send:hover {
            background: var(--accent-hover);
        }

        .btn-send:disabled {
            background: var(--surface);
            color: var(--text-muted);
            cursor: not-allowed;
        }

        /* ═══════════════════════════════════════════
           FOOTER
           ═══════════════════════════════════════════ */
        .footer {
            border-top: 1px solid var(--border);
            padding: 4rem 2rem 3rem;
        }

        .footer-inner {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 3rem;
        }

        .footer-brand p {
            font-size: 0.825rem;
            color: var(--text-secondary);
            margin-top: 0.5rem;
            max-width: 320px;
            line-height: 1.6;
        }

        .footer-brand .footer-logo {
            font-weight: 700;
            font-size: 1rem;
            color: var(--text);
            margin-bottom: 0.25rem;
        }

        .footer-stack {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }

        .footer-stack span {
            font-size: 0.7rem;
            font-weight: 600;
            padding: 0.25rem 0.55rem;
            border-radius: 4px;
            background: rgba(255,255,255,0.04);
            border: 1px solid var(--border);
            color: var(--text-muted);
        }

        .footer-links-group {
            display: flex;
            gap: 3.5rem;
        }

        .footer-col h4 {
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--text-muted);
            margin-bottom: 0.75rem;
        }

        .footer-col ul { list-style: none; }

        .footer-col li { margin-bottom: 0.45rem; }

        .footer-col a {
            font-size: 0.825rem;
            color: var(--text-secondary);
            text-decoration: none;
            transition: color 0.2s;
        }

        .footer-col a:hover { color: var(--text); }

        .footer-copy {
            text-align: center;
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border);
            max-width: 1200px;
            margin-left: auto;
            margin-right: auto;
        }

        /* ═══════════════════════════════════════════
           SCROLL REVEAL
           ═══════════════════════════════════════════ */
        .reveal {
            opacity: 0;
            transform: translateY(28px);
            transition: opacity 0.7s ease, transform 0.7s ease;
        }

        .reveal.visible {
            opacity: 1;
            transform: translateY(0);
        }

        /* ═══════════════════════════════════════════
           SCROLLBAR
           ═══════════════════════════════════════════ */
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.06); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.12); }

        /* ═══════════════════════════════════════════
           RESPONSIVE
           ═══════════════════════════════════════════ */
        @media (max-width: 1024px) {
            .pipeline { grid-template-columns: repeat(2, 1fr); gap: 2.5rem; }
            .pipeline::before { display: none; }
            .features-grid { grid-template-columns: 1fr; }
            .arch-split { grid-template-columns: 1fr; }
            .arch-code { border-left: none; border-top: 1px solid var(--border); }
            .dash-body { grid-template-columns: 1fr; }
            .stats-bar-inner { grid-template-columns: repeat(2, 1fr); }
            .metrics-grid { grid-template-columns: repeat(2, 1fr); }
        }

        @media (max-width: 640px) {
            .nav-links { display: none; }
            .pipeline { grid-template-columns: 1fr; }
            .stats-bar-inner { grid-template-columns: 1fr; }
            .metrics-grid { grid-template-columns: 1fr; }
            .footer-links-group { flex-direction: column; gap: 2rem; }
            .hero { padding: 7rem 1.25rem 4rem; }
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
                <a href="#how-it-works">How It Works</a>
                <a href="#architecture">API</a>
                <a href="#dashboard">Dashboard</a>
                <a href="#sandbox">Sandbox</a>
                <span class="nav-badge">Online</span>
            </div>
        </div>
    </nav>

    <!-- HERO -->
    <section class="hero" id="hero">
        <div class="hero-eyebrow">&#9889; OpenAI-Compatible API &middot; Groq-Powered Inference</div>
        <h1>
            <span style="animation-delay: 0.15s">Intelligent </span>
            <span style="animation-delay: 0.25s">LLM </span>
            <span style="animation-delay: 0.35s">Routing</span><br>
            <span class="hero-gradient-text" style="animation-delay: 0.45s">with </span>
            <span class="hero-gradient-text" style="animation-delay: 0.55s">Semantic </span>
            <span class="hero-gradient-text" style="animation-delay: 0.65s">Caching.</span>
        </h1>
        <p class="hero-lead">
            A cost-aware proxy that sits between your app and LLM providers. It semantically caches responses, routes queries by complexity, and falls back gracefully &mdash; cutting costs and latency without changing your code.
        </p>
        <div class="hero-actions">
            <a href="#sandbox" class="btn-primary">Try the Sandbox &#8594;</a>
            <a href="#dashboard" class="btn-secondary">View Analytics</a>
        </div>
    </section>

    <!-- STATS BAR -->
    <div class="stats-bar reveal">
        <div class="stats-bar-inner">
            <div class="stat-item">
                <div class="stat-value accent">92%</div>
                <div class="stat-label">Similarity Threshold</div>
            </div>
            <div class="stat-item">
                <div class="stat-value emerald">2</div>
                <div class="stat-label">Model Tiers</div>
            </div>
            <div class="stat-item">
                <div class="stat-value amber">&lt;100ms</div>
                <div class="stat-label">Cache Hit Latency</div>
            </div>
            <div class="stat-item">
                <div class="stat-value cyan">384-dim</div>
                <div class="stat-label">Embedding Vectors</div>
            </div>
        </div>
    </div>

    <!-- HOW IT WORKS -->
    <section class="section" id="how-it-works">
        <div class="section-header reveal">
            <div class="section-label">How It Works</div>
            <h2 class="section-title">Every request flows through four stages.</h2>
            <p class="section-desc">
                The gateway intercepts your OpenAI-format request, checks for semantically similar cached responses, evaluates complexity, and routes to the optimal model.
            </p>
        </div>

        <div class="pipeline reveal">
            <div class="pipe-step">
                <div class="pipe-icon i1">&#128232;</div>
                <div class="pipe-num">Step 1</div>
                <div class="pipe-title">Receive Request</div>
                <div class="pipe-desc">Accepts any OpenAI-compatible chat completion request at /v1/chat/completions.</div>
            </div>
            <div class="pipe-step">
                <div class="pipe-icon i2">&#129504;</div>
                <div class="pipe-num">Step 2</div>
                <div class="pipe-title">Semantic Cache Lookup</div>
                <div class="pipe-desc">Generates a 384-dim embedding and searches Qdrant for a cached response above the similarity threshold.</div>
            </div>
            <div class="pipe-step">
                <div class="pipe-icon i3">&#9878;&#65039;</div>
                <div class="pipe-num">Step 3</div>
                <div class="pipe-title">Complexity Routing</div>
                <div class="pipe-desc">On cache miss, evaluates prompt complexity via heuristics and routes to 8B (fast) or 70B (powerful) model.</div>
            </div>
            <div class="pipe-step">
                <div class="pipe-icon i4">&#9989;</div>
                <div class="pipe-num">Step 4</div>
                <div class="pipe-title">Response &amp; Cache</div>
                <div class="pipe-desc">Returns the response, stores it in the vector cache, and logs cost + latency metrics to Redis.</div>
            </div>
        </div>
    </section>

    <!-- FEATURES -->
    <section class="section" id="features">
        <div class="section-header reveal">
            <div class="section-label">Core Features</div>
            <h2 class="section-title">Built for production LLM workloads.</h2>
            <p class="section-desc">
                Three layers of intelligence between your application and upstream LLM providers.
            </p>
        </div>

        <div class="features-grid reveal">
            <article class="feature-card">
                <div class="feature-label l-accent">Caching</div>
                <h3 class="feature-title">Semantic Vector Cache</h3>
                <p class="feature-desc">
                    Instead of exact-match string caching, the gateway embeds prompts into 384-dim vectors and searches for semantically similar past queries using Qdrant with cosine similarity.
                </p>
                <ul class="feature-list">
                    <li>HuggingFace all-MiniLM-L6-v2 embeddings</li>
                    <li>Local fastembed fallback if HF is unavailable</li>
                    <li>Configurable similarity threshold (default 0.92)</li>
                    <li>Sub-100ms cached responses</li>
                </ul>
            </article>

            <article class="feature-card">
                <div class="feature-label l-emerald">Routing</div>
                <h3 class="feature-title">Cost-Aware Model Selection</h3>
                <p class="feature-desc">
                    Prompts are classified as SIMPLE or COMPLEX using keyword analysis and length heuristics, then routed to the optimal model tier on Groq for the best cost/quality tradeoff.
                </p>
                <ul class="feature-list">
                    <li>Simple: Llama 3.1 8B Instant ($0.05/M input)</li>
                    <li>Complex: Llama 3.3 70B Versatile ($0.59/M input)</li>
                    <li>Keyword + length heuristic classification</li>
                    <li>Per-query cost tracking in Redis</li>
                </ul>
            </article>

            <article class="feature-card">
                <div class="feature-label l-amber">Resilience</div>
                <h3 class="feature-title">Graceful Ollama Fallback</h3>
                <p class="feature-desc">
                    If the primary Groq API fails or times out, the gateway automatically falls back to a local or self-hosted Ollama instance &mdash; ensuring zero downtime for your users.
                </p>
                <ul class="feature-list">
                    <li>Automatic failover on Groq errors</li>
                    <li>Configurable Ollama endpoint URL</li>
                    <li>Response normalized to OpenAI format</li>
                    <li>Fallback latency tracked separately</li>
                </ul>
            </article>
        </div>
    </section>

    <!-- ARCHITECTURE -->
    <section class="section" id="architecture">
        <div class="section-header reveal">
            <div class="section-label">Drop-In API</div>
            <h2 class="section-title">OpenAI-compatible. Zero code changes.</h2>
        </div>

        <div class="arch-section reveal">
            <div class="arch-split">
                <div class="arch-text">
                    <h3>Replace your base URL. That's it.</h3>
                    <p>
                        The gateway exposes the standard <code>/v1/chat/completions</code> endpoint. Point any OpenAI SDK, LangChain, or custom client at this proxy and get semantic caching + intelligent routing for free.
                    </p>
                    <p>
                        Every response includes an <code>X-Cache-Lookup</code> header so you can inspect cache behavior. Metrics are tracked in Redis and exposed via the analytics dashboard.
                    </p>
                    <div class="arch-tags">
                        <span class="arch-tag">FastAPI</span>
                        <span class="arch-tag">Groq</span>
                        <span class="arch-tag">Qdrant</span>
                        <span class="arch-tag">Redis</span>
                        <span class="arch-tag">HuggingFace</span>
                        <span class="arch-tag">Ollama</span>
                        <span class="arch-tag">fastembed</span>
                    </div>
                </div>
                <div class="arch-code">
<pre><span class="cmt"># Standard OpenAI-format request</span>
<span class="kw">curl</span> -X POST <span class="str">http://localhost:8000/v1/chat/completions</span> \
  -H <span class="str">"Content-Type: application/json"</span> \
  -d '{
    <span class="hdr">"messages"</span>: [
      {<span class="str">"role"</span>: <span class="str">"user"</span>,
       <span class="str">"content"</span>: <span class="str">"Explain semantic caching"</span>}
    ]
  }'

<span class="cmt"># Response headers</span>
<span class="hdr">X-Cache-Lookup</span>: <span class="str">HIT</span>    <span class="cmt"># or MISS</span>
<span class="hdr">Content-Type</span>: <span class="str">application/json</span>

<span class="cmt"># Response body (OpenAI-compatible)</span>
{
  <span class="hdr">"id"</span>: <span class="str">"chatcmpl-abc123"</span>,
  <span class="hdr">"model"</span>: <span class="str">"llama-3.1-8b-instant"</span>,
  <span class="hdr">"choices"</span>: [{ <span class="hdr">"message"</span>: { ... } }],
  <span class="hdr">"usage"</span>: { <span class="str">"total_tokens"</span>: <span class="num">142</span> }
}</pre>
                </div>
            </div>
        </div>
    </section>

    <!-- DASHBOARD -->
    <section class="dash-section" id="dashboard">
        <div class="section" id="sandbox" style="padding-bottom: 2rem;">
            <div class="section-header reveal" style="margin-bottom: 2rem;">
                <div class="section-label">Live Dashboard</div>
                <h2 class="section-title">Real-time analytics &amp; sandbox.</h2>
                <p class="section-desc">Monitor cost savings, cache hit rates, and latency. Test the gateway live in the chat sandbox.</p>
            </div>

            <div class="tabs-nav">
                <button class="tab-btn active" onclick="switchTab('analytics')">Analytics &amp; Logs</button>
                <button class="tab-btn" onclick="switchTab('chat')">Chat Sandbox</button>
            </div>

            <!-- Analytics Tab -->
            <div id="tab-analytics" class="tab-content active">
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-header">
                            <span class="metric-label">Cost Saved</span>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--emerald)"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
                        </div>
                        <div class="metric-value" id="val-saved" style="color:var(--emerald)">$0.000000</div>
                        <div class="metric-sub">Estimated savings from cache hits</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-header">
                            <span class="metric-label">Cost Spent</span>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--amber)"><ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v8c0 1.66 3.58 3 8 3s8-1.34 8-3V6"/><path d="M4 11c0 1.66 3.58 3 8 3s8-1.34 8-3"/></svg>
                        </div>
                        <div class="metric-value" id="val-spent" style="color:var(--amber)">$0.000000</div>
                        <div class="metric-sub">Total upstream API spend</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-header">
                            <span class="metric-label">Cache Hit Rate</span>
                            <div class="circ-prog">
                                <svg viewBox="0 0 36 36">
                                    <path class="circ-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                                    <path class="circ-fill" id="hitrate-circle" stroke-dasharray="0, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                                </svg>
                            </div>
                        </div>
                        <div class="metric-value" id="val-hitrate" style="color:var(--accent)">0.00%</div>
                        <div class="metric-sub">Semantic cache efficiency</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-header">
                            <span class="metric-label">Avg. Latency</span>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--cyan)"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                        </div>
                        <div class="latency-split">
                            <span class="metric-value" id="val-latency-cached" style="color:var(--text)">0ms</span>
                            <span class="latency-tag cached">Cached</span>
                            <span style="color:var(--text-muted)">/</span>
                            <span class="metric-value" id="val-latency-direct" style="color:var(--text)">0ms</span>
                            <span class="latency-tag direct">Direct</span>
                        </div>
                        <div class="metric-sub">Mean response time comparison</div>
                    </div>
                </div>

                <div class="dash-body">
                    <div class="card">
                        <div class="card-title">Latency Comparison</div>
                        <div class="chart-container">
                            <canvas id="latencyChart"></canvas>
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-title">Query Log</div>
                        <div class="table-wrap">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Prompt</th>
                                        <th>Complexity</th>
                                        <th>Model</th>
                                        <th>Cache</th>
                                        <th>Latency</th>
                                    </tr>
                                </thead>
                                <tbody id="queries-tbody"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Chat Tab -->
            <div id="tab-chat" class="tab-content">
                <div class="chat-layout">
                    <div class="chat-messages" id="chat-messages">
                        <div class="message assistant system-message">
                            <div class="msg-bubble">
                                &#128075; Connected to the <strong>Semantic LLM Gateway</strong>. Send any message to test intent routing (Simple vs Complex) and semantic caching in real-time.
                            </div>
                        </div>
                    </div>
                    <div class="chat-input-bar">
                        <input type="text" class="chat-input" id="chat-input" placeholder="Ask anything to test the gateway..." onkeydown="handleKey(event)" />
                        <button class="btn-send" id="btn-send" onclick="sendMessage()">Send</button>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- FOOTER -->
    <footer class="footer">
        <div class="footer-inner">
            <div class="footer-brand">
                <div class="footer-logo">Semantic LLM Gateway</div>
                <p>Cost-aware routing proxy for Groq with semantic caching, intelligent complexity routing, and Ollama fallback. OpenAI-compatible API.</p>
                <div class="footer-stack">
                    <span>FastAPI</span>
                    <span>Groq</span>
                    <span>Qdrant</span>
                    <span>Redis</span>
                    <span>HuggingFace</span>
                    <span>fastembed</span>
                    <span>Ollama</span>
                </div>
            </div>
            <div class="footer-links-group">
                <div class="footer-col">
                    <h4>Navigate</h4>
                    <ul>
                        <li><a href="#hero">Home</a></li>
                        <li><a href="#features">Features</a></li>
                        <li><a href="#how-it-works">How It Works</a></li>
                        <li><a href="#architecture">API</a></li>
                    </ul>
                </div>
                <div class="footer-col">
                    <h4>Dashboard</h4>
                    <ul>
                        <li><a href="#dashboard">Analytics</a></li>
                        <li><a href="#sandbox">Chat Sandbox</a></li>
                        <li><a href="/docs">API Docs</a></li>
                        <li><a href="/health">Health Check</a></li>
                    </ul>
                </div>
                <div class="footer-col">
                    <h4>Endpoints</h4>
                    <ul>
                        <li><a href="/v1/chat/completions">/v1/chat/completions</a></li>
                        <li><a href="/api/metrics">/api/metrics</a></li>
                        <li><a href="/health">/health</a></li>
                    </ul>
                </div>
            </div>
        </div>
        <p class="footer-copy">Semantic LLM Gateway &middot; Built with FastAPI &amp; Groq</p>
    </footer>

    <!-- JAVASCRIPT -->
    <script>
        /* Scroll Reveal */
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -60px 0px' });

        document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

        /* Tabs */
        let latencyChart = null;
        let activeTab = 'analytics';
        let chatHistory = [];

        function switchTab(tabId) {
            activeTab = tabId;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(btn => btn.textContent.toLowerCase().includes(tabId));
            if (activeBtn) activeBtn.classList.add('active');

            document.getElementById('tab-' + tabId).classList.add('active');

            if (tabId === 'analytics') fetchMetrics();
        }

        /* Metrics */
        async function fetchMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();

                document.getElementById('val-saved').textContent = '$' + data.total_saved.toFixed(6);
                document.getElementById('val-spent').textContent = '$' + data.total_spent.toFixed(6);
                document.getElementById('val-hitrate').textContent = data.hit_rate.toFixed(2) + '%';

                const percent = Math.min(100, Math.max(0, data.hit_rate));
                document.getElementById('hitrate-circle').setAttribute('stroke-dasharray', percent + ', 100');

                document.getElementById('val-latency-cached').textContent = Math.round(data.avg_latency_hit) + 'ms';
                document.getElementById('val-latency-direct').textContent = Math.round(data.avg_latency_miss) + 'ms';

                const tbody = document.getElementById('queries-tbody');
                tbody.innerHTML = '';

                if (data.queries.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:2rem">No queries yet. Try the Chat Sandbox!</td></tr>';
                } else {
                    data.queries.forEach(function(q) {
                        const tr = document.createElement('tr');
                        const cacheBadge = q.is_cache_hit === 1
                            ? '<span class="status-dot hit">HIT</span>'
                            : '<span class="status-dot miss">MISS</span>';
                        const complexityBadge = q.complexity === 'COMPLEX'
                            ? '<span class="badge advanced">Complex</span>'
                            : '<span class="badge simple">Simple</span>';
                        tr.innerHTML =
                            '<td class="prompt-text" title="' + escapeHtml(q.prompt) + '">' + escapeHtml(q.prompt) + '</td>' +
                            '<td>' + complexityBadge + '</td>' +
                            '<td style="color:var(--text-secondary)">' + formatModelRoute(q.model_routed) + '</td>' +
                            '<td>' + cacheBadge + '</td>' +
                            '<td style="font-weight:600">' + Math.round(q.latency_ms) + 'ms</td>';
                        tbody.appendChild(tr);
                    });
                }

                updateChart(data.queries);
            } catch (error) {
                console.error('Metrics fetch error:', error);
            }
        }

        function formatModelRoute(model) {
            if (!model) return 'Unknown';
            if (model.startsWith("llama-3.1-8b")) return "<strong>Groq</strong> Llama3.1-8B";
            if (model.startsWith("llama-3.3-70b")) return "<strong>Groq</strong> Llama3.3-70B";
            if (model.startsWith("ollama")) return "<strong>Ollama</strong> Fallback";
            if (model.indexOf("-") !== -1) {
                var parts = model.split("-");
                return "<strong>" + parts[0].charAt(0).toUpperCase() + parts[0].slice(1) + "</strong> " + parts.slice(1).join(" ");
            }
            return "<strong>Model</strong> " + model;
        }

        function escapeHtml(text) {
            return text.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;");
        }

        /* Chart */
        function updateChart(queries) {
            var chrono = queries.slice().reverse();
            var labels = [], hitData = [], missData = [];

            chrono.forEach(function(q) {
                var t = new Date(q.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'});
                labels.push(t);
                if (q.is_cache_hit === 1) { hitData.push(q.latency_ms); missData.push(null); }
                else { missData.push(q.latency_ms); hitData.push(null); }
            });

            var ctx = document.getElementById('latencyChart').getContext('2d');
            if (latencyChart) latencyChart.destroy();

            var grad1 = ctx.createLinearGradient(0,0,0,280);
            grad1.addColorStop(0,'rgba(124,92,252,0.15)');
            grad1.addColorStop(1,'rgba(124,92,252,0)');

            var grad2 = ctx.createLinearGradient(0,0,0,280);
            grad2.addColorStop(0,'rgba(251,191,36,0.15)');
            grad2.addColorStop(1,'rgba(251,191,36,0)');

            latencyChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels.length > 0 ? labels : ['08:00','10:00','12:00','14:00','16:00','18:00','20:00'],
                    datasets: [
                        {
                            label: 'Cache HIT',
                            data: hitData.length > 0 ? hitData : [80,110,90,120,80,100,75],
                            borderColor: '#7c5cfc',
                            backgroundColor: grad1,
                            borderWidth: 2, tension: 0.4, fill: true, spanGaps: true,
                            pointBackgroundColor: '#7c5cfc', pointHoverRadius: 5, pointRadius: 3
                        },
                        {
                            label: 'Cache MISS',
                            data: missData.length > 0 ? missData : [230,380,260,310,480,470,350],
                            borderColor: '#fbbf24',
                            backgroundColor: grad2,
                            borderWidth: 2, tension: 0.4, fill: true, spanGaps: true,
                            pointBackgroundColor: '#fbbf24', pointHoverRadius: 5, pointRadius: 3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#8a8a9a', font: { family: 'Inter', size: 11 } }
                        }
                    },
                    scales: {
                        y: {
                            title: { display: true, text: 'Latency (ms)', color: '#55556a' },
                            grid: { color: '#1e1e26' },
                            ticks: { color: '#55556a' },
                            beginAtZero: true
                        },
                        x: {
                            title: { display: true, text: 'Timeline', color: '#55556a' },
                            grid: { display: false },
                            ticks: { color: '#55556a' }
                        }
                    }
                }
            });
        }

        /* Chat */
        function handleKey(e) { if (e.key === 'Enter') sendMessage(); }

        async function sendMessage() {
            var input = document.getElementById('chat-input');
            var prompt = input.value.trim();
            if (!prompt) return;
            input.value = '';

            appendMessage('user', prompt);
            var typingId = appendTypingIndicator();
            chatHistory.push({ role: 'user', content: prompt });

            var sendBtn = document.getElementById('btn-send');
            var inputField = document.getElementById('chat-input');
            sendBtn.disabled = true;
            inputField.disabled = true;

            var startTime = performance.now();

            try {
                var response = await fetch('/v1/chat/completions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ messages: chatHistory })
                });

                var latencyMs = performance.now() - startTime;
                removeTypingIndicator(typingId);

                if (!response.ok) {
                    var errDetail = 'Server returned code ' + response.status;
                    try { var errJson = await response.json(); if (errJson && errJson.detail) errDetail = errJson.detail; } catch(e) {}
                    throw new Error(errDetail);
                }

                var data = await response.json();
                var assistantMessage = data.choices[0].message.content;
                var cacheLookup = response.headers.get('X-Cache-Lookup') || 'MISS';
                var modelRouted = data.model;
                var usage = data.usage || { prompt_tokens: 0, completion_tokens: 0 };

                chatHistory.push({ role: 'assistant', content: assistantMessage });

                appendMessage('assistant', assistantMessage, {
                    latency: latencyMs,
                    cache: cacheLookup,
                    model: modelRouted,
                    tokens: usage.prompt_tokens + usage.completion_tokens
                });

                fetchMetrics();
            } catch (error) {
                removeTypingIndicator(typingId);
                appendMessage('assistant', 'Error: ' + error.message);
            } finally {
                sendBtn.disabled = false;
                inputField.disabled = false;
                inputField.focus();
            }
        }

        function appendMessage(sender, text, meta) {
            var container = document.getElementById('chat-messages');
            var msgDiv = document.createElement('div');
            msgDiv.className = 'message ' + sender;

            var bubble = document.createElement('div');
            bubble.className = 'msg-bubble';
            bubble.innerHTML = escapeHtml(text).replace(/\n/g, '<br/>');
            msgDiv.appendChild(bubble);

            if (meta) {
                var info = document.createElement('div');
                info.className = 'msg-info';
                var cacheClass = meta.cache === 'HIT' ? 'hit' : 'miss';
                info.innerHTML =
                    '<span class="status-dot ' + cacheClass + '">' + meta.cache + '</span>' +
                    '<span>Route: <strong>' + meta.model + '</strong></span>' +
                    '<span>Latency: <strong>' + meta.latency.toFixed(0) + 'ms</strong></span>' +
                    '<span>Tokens: <strong>' + meta.tokens + '</strong></span>';
                msgDiv.appendChild(info);
            }

            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
        }

        function appendTypingIndicator() {
            var container = document.getElementById('chat-messages');
            var msgDiv = document.createElement('div');
            var id = 'typing-' + Date.now();
            msgDiv.className = 'message assistant';
            msgDiv.id = id;
            var bubble = document.createElement('div');
            bubble.className = 'msg-bubble';
            bubble.innerHTML = '<span style="color:var(--text-muted)">Gateway routing query...</span>';
            msgDiv.appendChild(bubble);
            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
            return id;
        }

        function removeTypingIndicator(id) {
            var el = document.getElementById(id);
            if (el) el.remove();
        }

        /* Init */
        fetchMetrics();
        setInterval(fetchMetrics, 15000);

        /* Smooth scroll for nav links */
        document.querySelectorAll('a[href^="#"]').forEach(function(a) {
            a.addEventListener('click', function(e) {
                e.preventDefault();
                var target = document.querySelector(a.getAttribute('href'));
                if (target) {
                    var offset = 70;
                    var top = target.getBoundingClientRect().top + window.pageYOffset - offset;
                    window.scrollTo({ top: top, behavior: 'smooth' });
                }
            });
        });
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)
