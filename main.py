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
    description="Intelligent Cost-Aware LLM Gateway with Semantic Caching, Prompt Compression, and Graceful Fallback",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Cache-Lookup", "X-Cache-Similarity", "X-Model-Route", "X-Tokens-Saved", "X-Latency-Ms"],
)

# Include OpenAI compatible router
app.include_router(chat_router, prefix="/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/metrics")
async def get_metrics():
    """
    Exposes metrics derived from live gateway requests.
    """
    summary = await get_metrics_summary()
    return summary

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    """
    Serves the production-ready Semantic LLM Gateway developer dashboard.
    """
    html_content = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Semantic Gateway — Intelligent LLM Cost Optimization & Semantic Cache</title>
    <meta name="description" content="Production LLM gateway with sub-50ms semantic vector caching, prompt compression, and intelligent complexity routing.">
    <!-- Google Fonts: Inter for UI, Lora for Editorial Serif accents, JetBrains Mono for Code -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Lora:ital,wght@0,500;1,400;1,600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        /* ═══════════════════════════════════════════
           DESIGN SYSTEM (Linear × Stripe Editorial)
           ═══════════════════════════════════════════ */
        :root {
            --bg: #fbfbf8;
            --surface: #ffffff;
            --surface-subtle: #f6f6f3;
            --surface-hover: #f1f1ec;
            --border: #e6e6e0;
            --border-hover: #d2d2cb;
            --text-primary: #111111;
            --text-secondary: #4b4b45;
            --text-muted: #787870;
            --blue: #2563eb;
            --blue-light: #eff6ff;
            --blue-hover: #1d4ed8;
            --green: #10b981;
            --green-light: #ecfdf5;
            --amber: #f59e0b;
            --purple: #8b5cf6;
            --purple-light: #f5f3ff;
            --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --font-serif: 'Lora', Georgia, serif;
            --font-mono: 'JetBrains Mono', 'SFMono-Regular', Consolas, Menlo, monospace;
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 14px;
            --shadow-subtle: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02);
            --shadow-md: 0 4px 16px -2px rgba(0,0,0,0.06), 0 2px 6px -1px rgba(0,0,0,0.03);
            --shadow-lg: 0 12px 32px -4px rgba(0,0,0,0.1), 0 4px 12px -2px rgba(0,0,0,0.05);
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
           HEADER & NAVIGATION
           ═══════════════════════════════════════════ */
        .nav {
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(251, 251, 248, 0.92);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            padding: 0.85rem 0;
            transition: all 0.2s ease;
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
            font-size: 1.15rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }

        .nav-logo-mark {
            width: 26px;
            height: 26px;
            background: var(--text-primary);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            font-size: 0.8rem;
            font-weight: 800;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }

        .nav-logo-word em {
            font-style: italic;
            font-family: var(--font-serif);
            font-weight: 600;
            color: var(--blue);
        }

        .nav-pill-group {
            display: flex;
            align-items: center;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            box-shadow: var(--shadow-subtle);
            overflow: hidden;
        }

        .nav-pill-link {
            text-decoration: none;
            color: var(--text-secondary);
            font-size: 0.85rem;
            font-weight: 500;
            padding: 0.5rem 1.15rem;
            border-right: 1px solid var(--border);
            transition: all 0.15s ease;
        }
        .nav-pill-link:last-child { border-right: none; }
        .nav-pill-link:hover { color: var(--text-primary); background: var(--surface-hover); }

        .nav-actions {
            display: flex;
            align-items: center;
            gap: 0.65rem;
        }

        .nav-btn {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            box-shadow: var(--shadow-subtle);
            padding: 0.5rem 1rem;
            text-decoration: none;
            color: var(--text-primary);
            font-size: 0.85rem;
            font-weight: 500;
            transition: all 0.15s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            cursor: pointer;
        }
        .nav-btn:hover { background: var(--surface-hover); border-color: var(--border-hover); }

        /* ═══════════════════════════════════════════
           HERO SECTION
           ═══════════════════════════════════════════ */
        .section-hero {
            padding: 6.5rem 2rem 5rem;
            max-width: 1200px;
            margin: 0 auto;
        }

        .hero-badge-wrap {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 0.35rem 0.85rem;
            border-radius: 30px;
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--text-secondary);
            box-shadow: var(--shadow-subtle);
            margin-bottom: 2rem;
        }
        .hero-badge-dot {
            width: 8px;
            height: 8px;
            background: var(--green);
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
        }

        .hero-title {
            font-size: clamp(2.8rem, 6.5vw, 4.6rem);
            line-height: 1.06;
            font-weight: 700;
            letter-spacing: -0.04em;
            color: var(--text-primary);
            max-width: 960px;
            margin-bottom: 1.5rem;
        }

        .hero-subtitle {
            font-size: 1.2rem;
            line-height: 1.6;
            color: var(--text-secondary);
            max-width: 760px;
            margin-bottom: 2.5rem;
        }

        .hero-cta-group {
            display: flex;
            align-items: center;
            gap: 1.25rem;
            flex-wrap: wrap;
        }

        .btn-primary {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            background: var(--text-primary);
            color: #ffffff;
            text-decoration: none;
            font-size: 0.95rem;
            font-weight: 600;
            padding: 0.85rem 1.75rem;
            border-radius: var(--radius-sm);
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: var(--shadow-md);
            transition: all 0.2s ease;
            cursor: pointer;
        }
        .btn-primary:hover {
            background: #272727;
            transform: translateY(-1px);
            box-shadow: var(--shadow-lg);
        }

        .btn-secondary {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.95rem;
            font-weight: 500;
            padding: 0.85rem 1.25rem;
            border-radius: var(--radius-sm);
            transition: all 0.15s ease;
        }
        .btn-secondary:hover { color: var(--text-primary); background: var(--surface-hover); }

        /* ═══════════════════════════════════════════
           TERMINAL SPLIT / QUICKSTART
           ═══════════════════════════════════════════ */
        .section-split {
            max-width: 1200px;
            margin: 0 auto;
            padding: 4rem 2rem 5rem;
            display: grid;
            grid-template-columns: 1fr 1.1fr;
            gap: 4rem;
            align-items: center;
        }

        .split-eyebrow {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--blue);
            font-weight: 700;
            margin-bottom: 1rem;
        }

        .split-title {
            font-size: 2.75rem;
            line-height: 1.12;
            letter-spacing: -0.03em;
            margin-bottom: 1.25rem;
        }

        .split-desc {
            font-size: 1.05rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
            line-height: 1.6;
        }

        .terminal-window {
            background: #101114;
            border: 1px solid #23252b;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-lg);
            overflow: hidden;
            width: 100%;
        }

        .terminal-header {
            background: #18191f;
            padding: 0.75rem 1.25rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid #23252b;
        }

        .terminal-dots { display: flex; gap: 0.4rem; }
        .terminal-dot { width: 10px; height: 10px; border-radius: 50%; }
        .terminal-dot.r { background: #ff5f56; }
        .terminal-dot.y { background: #ffbd2e; }
        .terminal-dot.g { background: #27c93f; }

        .terminal-title {
            color: #8c909e;
            font-size: 0.78rem;
            font-family: var(--font-mono);
        }

        .terminal-body {
            padding: 1.5rem;
            font-family: var(--font-mono);
            font-size: 0.85rem;
            color: #e2e4ea;
            line-height: 1.8;
        }

        .term-check { color: #27c93f; margin-right: 0.6rem; font-weight: bold; }
        .term-dim { color: #6b7082; }
        .term-accent { color: #60a5fa; }
        .term-code-block {
            background: #090a0d;
            border: 1px solid #1f2129;
            border-radius: var(--radius-sm);
            padding: 1rem;
            margin-top: 1rem;
            color: #cbd5e1;
            font-size: 0.8rem;
            overflow-x: auto;
        }

        /* ═══════════════════════════════════════════
           EDITORIAL FEATURE CARDS
           ═══════════════════════════════════════════ */
        .section-cards {
            max-width: 1200px;
            margin: 3rem auto 6rem;
            padding: 0 2rem;
        }

        .cards-header {
            text-align: center;
            max-width: 760px;
            margin: 0 auto 3.5rem;
        }

        .cards-header h2 {
            font-size: 2.4rem;
            letter-spacing: -0.03em;
            margin-bottom: 1rem;
        }

        .cards-header p {
            color: var(--text-secondary);
            font-size: 1.05rem;
        }

        .cards-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.75rem;
        }

        .ed-card {
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 2.25rem;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-subtle);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.2s ease;
        }
        .ed-card:hover {
            border-color: var(--border-hover);
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        .ed-card-label {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--blue);
            margin-bottom: 0.85rem;
            display: block;
        }

        .ed-card-title {
            font-size: 1.45rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-bottom: 0.85rem;
        }

        .ed-card p {
            font-size: 0.925rem;
            color: var(--text-secondary);
            margin-bottom: 1.75rem;
            line-height: 1.6;
        }

        .ed-card ul {
            list-style: none;
            font-size: 0.875rem;
            color: var(--text-secondary);
            border-top: 1px solid var(--border);
            padding-top: 1.25rem;
        }

        .ed-card ul li {
            position: relative;
            padding-left: 1.25rem;
            margin-bottom: 0.65rem;
        }
        .ed-card ul li::before {
            content: '✓';
            position: absolute;
            left: 0;
            color: var(--green);
            font-weight: bold;
        }

        /* ═══════════════════════════════════════════
           INTERACTIVE SANDBOX & DASHBOARD (TABS)
           ═══════════════════════════════════════════ */
        .section-demo {
            max-width: 1200px;
            margin: 0 auto 6rem;
            padding: 0 2rem;
        }

        .dash-tab-wrap {
            display: flex;
            justify-content: center;
            gap: 1.5rem;
            margin-bottom: 2.5rem;
            border-bottom: 1px solid var(--border);
        }

        .dash-tab {
            padding: 0.75rem 1.25rem;
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-muted);
            cursor: pointer;
            border-bottom: 2px solid transparent;
            margin-bottom: -1px;
            transition: all 0.15s ease;
        }
        .dash-tab:hover { color: var(--text-primary); }
        .dash-tab.active {
            color: var(--blue);
            border-bottom: 2px solid var(--blue);
        }

        .dash-content {
            display: none;
        }
        .dash-content.active {
            display: block;
            animation: fadeIn 0.2s ease-in-out;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

        /* Split Sandbox Layout */
        .demo-grid {
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 2.5rem;
            align-items: start;
        }

        .card-box {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-subtle);
            padding: 1.75rem;
        }

        .demo-label-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.85rem;
        }

        .demo-label {
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        /* Preset Chips */
        .chips-scroll {
            display: flex;
            gap: 0.5rem;
            overflow-x: auto;
            padding-bottom: 0.75rem;
            margin-bottom: 1rem;
        }
        .preset-chip {
            background: var(--surface-subtle);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 0.35rem 0.85rem;
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--text-secondary);
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.15s ease;
        }
        .preset-chip:hover {
            background: var(--surface-hover);
            color: var(--text-primary);
            border-color: var(--border-hover);
        }

        /* Textarea input */
        .prompt-textarea {
            width: 100%;
            height: 140px;
            padding: 1rem;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            font-family: var(--font-mono);
            font-size: 0.875rem;
            color: var(--text-primary);
            line-height: 1.5;
            resize: vertical;
            outline: none;
            transition: border-color 0.15s ease;
        }
        .prompt-textarea:focus {
            border-color: var(--blue);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        .prompt-action-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 1rem;
        }

        .char-count {
            font-size: 0.8rem;
            color: var(--text-muted);
            font-family: var(--font-mono);
        }

        .btn-compress {
            background: var(--text-primary);
            color: #ffffff;
            font-size: 0.9rem;
            font-weight: 600;
            padding: 0.7rem 1.6rem;
            border-radius: var(--radius-sm);
            border: none;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.15s ease;
            box-shadow: var(--shadow-subtle);
        }
        .btn-compress:hover:not(:disabled) {
            background: #2a2a2a;
            transform: translateY(-1px);
        }
        .btn-compress:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        /* Result Inspector Area */
        .result-container {
            margin-top: 1.5rem;
            border-top: 1px solid var(--border);
            padding-top: 1.5rem;
        }

        .result-tabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }

        .res-tab-btn {
            background: var(--surface-subtle);
            border: 1px solid var(--border);
            padding: 0.35rem 0.85rem;
            border-radius: var(--radius-sm);
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.15s ease;
        }
        .res-tab-btn.active {
            background: var(--text-primary);
            color: #ffffff;
            border-color: var(--text-primary);
        }

        .res-pane {
            display: none;
            background: var(--surface-subtle);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 1.25rem;
            font-size: 0.875rem;
            line-height: 1.6;
        }
        .res-pane.active { display: block; }

        .res-response-text {
            font-family: var(--font-sans);
            color: var(--text-primary);
            white-space: pre-wrap;
        }

        .diff-view {
            font-family: var(--font-mono);
            font-size: 0.8rem;
            line-height: 1.6;
            max-height: 250px;
            overflow-y: auto;
        }
        .diff-original { color: #ef4444; background: #fef2f2; padding: 0.5rem; border-radius: 4px; margin-bottom: 0.5rem; }
        .diff-optimized { color: #10b981; background: #ecfdf5; padding: 0.5rem; border-radius: 4px; }

        .diagnostics-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
        }
        .diag-item {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 0.75rem 1rem;
        }
        .diag-title { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; }
        .diag-val { font-size: 0.95rem; font-weight: 600; color: var(--text-primary); margin-top: 0.2rem; }

        /* Right Side: Stats Card */
        .stats-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-subtle);
            padding: 1.75rem;
        }

        .stats-list { list-style: none; }
        .stat-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.1rem 0;
            border-bottom: 1px solid var(--border);
            font-size: 0.9rem;
        }
        .stat-row:last-child { border-bottom: none; }
        .stat-name { color: var(--text-secondary); font-weight: 500; }
        .stat-value { font-weight: 600; color: var(--text-primary); text-align: right; }
        .stat-value.blue { color: var(--blue); }
        .stat-value.green { color: var(--green); }
        .stat-sub { font-size: 0.75rem; color: var(--text-muted); display: block; font-weight: normal; }

        /* Impact Dashboard Tab Layout */
        .analytics-wrap {
            display: flex;
            flex-direction: column;
            gap: 2.5rem;
        }

        .chart-box {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-subtle);
            padding: 2rem;
            height: 340px;
        }

        .metrics-summary-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.25rem;
        }
        .summary-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            padding: 1.25rem;
            box-shadow: var(--shadow-subtle);
        }
        .summary-card-title { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); }
        .summary-card-val { font-size: 1.6rem; font-weight: 700; color: var(--text-primary); margin-top: 0.4rem; }

        .table-wrap {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-subtle);
            overflow-x: auto;
        }
        table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
        th, td { text-align: left; padding: 1.1rem 1.25rem; border-bottom: 1px solid var(--border); }
        th { color: var(--text-muted); font-weight: 700; text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.05em; background: var(--surface-subtle); }
        tr:last-child td { border-bottom: none; }
        tr:hover td { background: var(--surface-subtle); }

        .status-dot {
            display: inline-block;
            width: 8px; height: 8px;
            border-radius: 50%;
            margin-right: 0.4rem;
        }
        .status-dot.hit { background: var(--green); }
        .status-dot.miss { background: var(--amber); }

        .badge {
            padding: 0.25rem 0.6rem;
            border-radius: 4px;
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
        }
        .badge.simple { background: var(--blue-light); color: var(--blue); }
        .badge.complex { background: var(--purple-light); color: var(--purple); }

        /* Modal Styles */
        .modal-backdrop {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(4px);
            z-index: 200;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .modal-backdrop.open { display: flex; }
        .modal-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-lg);
            max-width: 680px;
            width: 100%;
            max-height: 85vh;
            overflow-y: auto;
            padding: 2.25rem;
        }
        .modal-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }
        .modal-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: var(--text-muted);
        }

        /* ═══════════════════════════════════════════
           FOOTER
           ═══════════════════════════════════════════ */
        .footer {
            background: #101114;
            color: #ffffff;
            padding: 5rem 2rem 4rem;
            border-top: 1px solid #23252b;
        }

        .footer-inner {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1fr;
            gap: 3.5rem;
        }

        .footer-brand h4 { font-size: 1.15rem; font-weight: 700; margin-bottom: 1rem; color: #fff; }
        .footer-brand p { font-size: 0.875rem; color: #8c909e; line-height: 1.7; max-width: 320px; }
        
        .footer-col h5 { font-size: 0.85rem; color: #fff; margin-bottom: 1.25rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
        .footer-col ul { list-style: none; }
        .footer-col li { margin-bottom: 0.75rem; }
        .footer-col a { color: #8c909e; text-decoration: none; font-size: 0.875rem; transition: color 0.2s; }
        .footer-col a:hover { color: #ffffff; }

        /* Responsive Breakpoints */
        @media (max-width: 1024px) {
            .section-split, .demo-grid { grid-template-columns: 1fr; gap: 2.5rem; }
            .cards-grid { grid-template-columns: repeat(2, 1fr); }
            .metrics-summary-grid { grid-template-columns: repeat(2, 1fr); }
            .footer-inner { grid-template-columns: 1fr 1fr; gap: 2.5rem; }
        }

        @media (max-width: 768px) {
            .nav-pill-group { display: none; }
            .hero-title { font-size: 2.6rem; }
            .split-title { font-size: 2.2rem; }
            .cards-grid { grid-template-columns: 1fr; }
            .metrics-summary-grid { grid-template-columns: 1fr; }
            .footer-inner { grid-template-columns: 1fr; }
            .diagnostics-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>

    <!-- NAVIGATION -->
    <header>
        <nav class="nav" aria-label="Main Navigation">
            <div class="nav-inner">
                <a href="/" class="nav-logo" aria-label="Semantic Gateway Home">
                    <div class="nav-logo-mark">SG</div>
                    <span class="nav-logo-word">Semantic<em>Gateway</em></span>
                </a>
                <div class="nav-pill-group">
                    <a href="#features" class="nav-pill-link">Guide</a>
                    <a href="#demo" class="nav-pill-link">Savings</a>
                    <a href="#demo" class="nav-pill-link">Demo</a>
                    <a href="#quickstart" class="nav-pill-link">Quick start</a>
                </div>
                <div class="nav-actions">
                    <button class="nav-btn" onclick="openDocsModal()" aria-label="Open Documentation">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
                        Docs
                    </button>
                    <button class="nav-btn" onclick="switchTab('analytics'); document.getElementById('demo').scrollIntoView({behavior: 'smooth'});" aria-label="Open Dashboard Tab">
                        Dashboard
                    </button>
                    <a href="https://github.com/anothercodingguy/SemanticLLM" target="_blank" rel="noopener noreferrer" class="nav-btn" aria-label="GitHub Repository" style="padding: 0.5rem 0.65rem;">
                        <svg viewBox="0 0 24 24" width="17" height="17" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
                    </a>
                </div>
            </div>
        </nav>
    </header>

    <!-- HERO -->
    <main>
        <section class="section-hero" id="hero">
            <div class="hero-badge-wrap">
                <span class="hero-badge-dot"></span>
                <span>Production Gateway · Groq Llama 3.1 & 3.3 Connected</span>
            </div>
            <h1 class="hero-title">Cut Your LLM API Costs by 65%.</h1>
            <p class="hero-subtitle">
                For teams running chat, RAG, support, or coding agents. Semantic Gateway removes low-value context before inference, catches semantic paraphrases in cache, and routes simple queries cheaply.
            </p>
            <div class="hero-cta-group">
                <a href="#quickstart" class="btn-primary">
                    Install the gateway
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                </a>
                <a href="#demo" class="btn-secondary">Try it on your context ↗</a>
            </div>
        </section>

        <!-- TERMINAL SPLIT / QUICKSTART -->
        <section class="section-split" id="quickstart">
            <div>
                <div class="split-eyebrow">INTELLIGENT ROUTING · API-FIRST</div>
                <h2 class="split-title">One endpoint.<br>Every LLM.<br>Fewer tokens.</h2>
                <p class="split-desc">
                    Auto-detect context similarity. The gateway intercepts huge context dumps before they burn tokens, routing via Groq Llama 3 or falling back gracefully.
                </p>
                <div style="display:flex; gap:1rem; align-items:center;">
                    <button onclick="openDocsModal()" class="btn-primary">View Setup Guide</button>
                    <a href="#demo" class="btn-secondary">See live demo ↗</a>
                </div>
            </div>
            <div class="terminal-window">
                <div class="terminal-header">
                    <div class="terminal-dots">
                        <div class="terminal-dot r"></div>
                        <div class="terminal-dot y"></div>
                        <div class="terminal-dot g"></div>
                    </div>
                    <div class="terminal-title">semantic-gateway — live status</div>
                    <div style="font-size:0.75rem; color:#27c93f; font-family:var(--font-mono);">● active</div>
                </div>
                <div class="terminal-body">
                    <div><span class="term-check">✓</span> Groq Llama-3.1-8B-Instant <span class="term-dim">($0.05/M)</span></div>
                    <div><span class="term-check">✓</span> Groq Llama-3.3-70B-Versatile <span class="term-dim">($0.59/M)</span></div>
                    <div><span class="term-check">✓</span> Semantic Vector Cache <span class="term-dim">(384-dim fastembed)</span></div>
                    <div><span class="term-check">✓</span> Context Compression Engine <span class="term-dim">(Deduplication active)</span></div>
                    <div><span class="term-check">✓</span> In-Memory Metrics Store <span class="term-dim">(Zero latency)</span></div>
                    
                    <div class="term-code-block">
                        <div class="term-dim"># Python OpenAI Drop-in Configuration</div>
                        <div><span class="term-accent">from</span> openai <span class="term-accent">import</span> OpenAI</div>
                        <div>client = OpenAI(base_url=<span style="color:#a5d6ff;">"http://localhost:8000/v1"</span>, api_key=<span style="color:#a5d6ff;">"none"</span>)</div>
                    </div>
                </div>
            </div>
        </section>

        <!-- EDITORIAL FEATURE CARDS -->
        <section class="section-cards" id="features">
            <div class="cards-header">
                <h2>Control AI feature cost before the model call</h2>
                <p>Paste the same context a production AI feature would send: chat history, retrieval output, support logs. The gateway optimizes it before the request reaches the model.</p>
            </div>
            <div class="cards-grid">
                <article class="ed-card">
                    <div>
                        <span class="ed-card-label">Cost Model</span>
                        <h3 class="ed-card-title">Semantic Vector Cache</h3>
                        <p>Embeds prompts into 384-dim vectors to catch semantically equivalent queries and return instant sub-50ms responses.</p>
                    </div>
                    <ul>
                        <li>Cosine similarity threshold (0.82)</li>
                        <li>Zero provider spend on cache hits</li>
                    </ul>
                </article>
                <article class="ed-card">
                    <div>
                        <span class="ed-card-label">Quality</span>
                        <h3 class="ed-card-title">Complexity Routing</h3>
                        <p>Simple queries route to fast, cheap models (Llama 8B). Complex queries scale up to 70B automatically.</p>
                    </div>
                    <ul>
                        <li>$0.05/M vs $0.59/M automated routing</li>
                        <li>Exact per-query spend tracking</li>
                    </ul>
                </article>
                <article class="ed-card">
                    <div>
                        <span class="ed-card-label">Reliability</span>
                        <h3 class="ed-card-title">Graceful Fallback</h3>
                        <p>Run locally or in production. Built-in failover to Ollama or resilient provider fallback with zero crashes.</p>
                    </div>
                    <ul>
                        <li>OpenAI-compatible /v1/chat/completions</li>
                        <li>Safe context deduplication</li>
                    </ul>
                </article>
            </div>
        </section>

        <!-- INTERACTIVE SANDBOX & DASHBOARD -->
        <section class="section-demo" id="demo">
            <div class="dash-tab-wrap" role="tablist">
                <button class="dash-tab active" id="tabbtn-sandbox" onclick="switchTab('sandbox')" role="tab" aria-selected="true" aria-controls="tab-sandbox">Interactive Sandbox</button>
                <button class="dash-tab" id="tabbtn-analytics" onclick="switchTab('analytics')" role="tab" aria-selected="false" aria-controls="tab-analytics">Impact Dashboard</button>
            </div>

            <!-- Tab 1: Interactive Sandbox -->
            <div id="tab-sandbox" class="dash-content active" role="tabpanel" aria-labelledby="tabbtn-sandbox">
                <div class="demo-grid">
                    <!-- Left Column: Input & Results -->
                    <div class="card-box">
                        <div class="demo-label-row">
                            <span class="demo-label">1. Select Preset or Type Prompt</span>
                            <span class="char-count" id="prompt-char-count">0 chars · ~0 tokens</span>
                        </div>

                        <!-- Presets -->
                        <div class="chips-scroll" aria-label="Preset Prompts">
                            <button type="button" class="preset-chip" onclick="loadPreset('simple')">⚡ Simple Lookup</button>
                            <button type="button" class="preset-chip" onclick="loadPreset('paraphrase')">🎯 Semantic Paraphrase (Cache Test)</button>
                            <button type="button" class="preset-chip" onclick="loadPreset('noisy')">🧹 Noisy Context / RAG</button>
                            <button type="button" class="preset-chip" onclick="loadPreset('complex')">🧠 Complex Architecture</button>
                        </div>

                        <textarea class="prompt-textarea" id="chat-input" placeholder="Enter a prompt to test compression, semantic caching, and routing..." oninput="updateCharCount()" onkeydown="handleKey(event)"></textarea>

                        <div class="prompt-action-bar">
                            <div style="font-size:0.8rem; color:var(--text-muted);">
                                Press <kbd style="background:var(--surface-subtle); padding:0.15rem 0.4rem; border:1px solid var(--border); border-radius:3px;">Cmd/Ctrl+Enter</kbd> to execute
                            </div>
                            <button class="btn-compress" id="btn-send" onclick="sendMessage()">
                                <span id="btn-spinner" style="display:none; width:14px; height:14px; border:2px solid #fff; border-top-color:transparent; border-radius:50%; animation:spin 0.8s linear infinite;"></span>
                                <span id="btn-text">Compress & Route</span>
                            </button>
                        </div>

                        <!-- Error Alert -->
                        <div id="error-alert" style="display:none; margin-top:1rem; padding:0.85rem 1rem; background:#fef2f2; border:1px solid #fecaca; border-radius:var(--radius-sm); color:#b91c1c; font-size:0.85rem;"></div>

                        <!-- Result Inspector -->
                        <div class="result-container" id="result-container" style="display:none;">
                            <div class="demo-label-row">
                                <span class="demo-label">2. Gateway Output & Optimization Inspector</span>
                            </div>

                            <div class="result-tabs">
                                <button type="button" class="res-tab-btn active" id="btn-res-output" onclick="switchResultTab('output')">Model Output</button>
                                <button type="button" class="res-tab-btn" id="btn-res-compression" onclick="switchResultTab('compression')">Context Compression (<span id="res-tab-comp-pct">0%</span>)</button>
                                <button type="button" class="res-tab-btn" id="btn-res-diag" onclick="switchResultTab('diag')">Routing & Cache Diagnostics</button>
                            </div>

                            <!-- Pane 1: Output -->
                            <div class="res-pane active" id="pane-output">
                                <div class="res-response-text" id="res-text"></div>
                            </div>

                            <!-- Pane 2: Compression Diff -->
                            <div class="res-pane" id="pane-compression">
                                <div style="margin-bottom:0.75rem; font-weight:600; color:var(--text-primary);" id="res-comp-summary"></div>
                                <div class="diff-view">
                                    <div class="diff-original">
                                        <div style="font-size:0.7rem; font-weight:bold; margin-bottom:0.25rem;">ORIGINAL CONTEXT (<span id="diff-orig-tokens">0</span> tokens)</div>
                                        <div id="diff-orig-text"></div>
                                    </div>
                                    <div class="diff-optimized">
                                        <div style="font-size:0.7rem; font-weight:bold; margin-bottom:0.25rem;">OPTIMIZED CONTEXT (<span id="diff-opt-tokens">0</span> tokens — <span id="diff-saved-tokens">0</span> saved)</div>
                                        <div id="diff-opt-text"></div>
                                    </div>
                                </div>
                                <ul id="res-savings-notes" style="margin-top:0.75rem; padding-left:1.25rem; font-size:0.8rem; color:var(--text-secondary);"></ul>
                            </div>

                            <!-- Pane 3: Diagnostics -->
                            <div class="res-pane" id="pane-diag">
                                <div class="diagnostics-grid">
                                    <div class="diag-item">
                                        <div class="diag-title">Semantic Cache Status</div>
                                        <div class="diag-val" id="diag-cache">—</div>
                                    </div>
                                    <div class="diag-item">
                                        <div class="diag-title">Selected Model Route</div>
                                        <div class="diag-val" id="diag-model" style="font-family:var(--font-mono); font-size:0.85rem;">—</div>
                                    </div>
                                    <div class="diag-item">
                                        <div class="diag-title">Total Latency</div>
                                        <div class="diag-val" id="diag-latency">—</div>
                                    </div>
                                    <div class="diag-item">
                                        <div class="diag-title">Cost Comparison</div>
                                        <div class="diag-val" id="diag-cost">—</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Right Column: Live Metrics Panel -->
                    <div class="stats-card">
                        <div class="demo-label-row">
                            <span class="demo-label">TOKEN & INFERENCE IMPACT</span>
                            <span style="font-size:0.75rem; color:var(--green); font-weight:600;">● LIVE REAL-TIME</span>
                        </div>
                        <ul class="stats-list">
                            <li class="stat-row">
                                <span class="stat-name">Total Requests Analyzed</span>
                                <span class="stat-value" id="val-requests">0</span>
                            </li>
                            <li class="stat-row">
                                <span class="stat-name">Cache Hits</span>
                                <span class="stat-value" id="val-hits">0</span>
                            </li>
                            <li class="stat-row">
                                <span class="stat-name">Cache Efficiency</span>
                                <span class="stat-value blue" id="val-hitrate">0.0%</span>
                            </li>
                            <li class="stat-row">
                                <span class="stat-name">Tokens Processed</span>
                                <span class="stat-value" id="val-tokens-in">0</span>
                            </li>
                            <li class="stat-row">
                                <span class="stat-name">Tokens Saved (Compression)</span>
                                <span class="stat-value green" id="val-tokens-saved">0</span>
                            </li>
                            <li class="stat-row">
                                <span class="stat-name">API Spend Estimated</span>
                                <span class="stat-value" id="val-spent">$0.00000</span>
                            </li>
                            <li class="stat-row">
                                <span class="stat-name">API Cost Saved</span>
                                <span class="stat-value green" id="val-saved">$0.00000</span>
                            </li>
                            <li class="stat-row">
                                <span class="stat-name">Latency (Direct Miss)</span>
                                <div style="text-align:right">
                                    <span class="stat-value" id="val-latency-direct">—</span>
                                    <span class="stat-sub">avg. upstream inference</span>
                                </div>
                            </li>
                            <li class="stat-row">
                                <span class="stat-name">Latency (Semantic Hit)</span>
                                <div style="text-align:right">
                                    <span class="stat-value blue" id="val-latency-cached">—</span>
                                    <span class="stat-sub">avg. cache return</span>
                                </div>
                            </li>
                            <li class="stat-row">
                                <span class="stat-name">Latest Model Route</span>
                                <span class="stat-value" id="val-latest-route" style="font-family:var(--font-mono); font-size:0.8rem;">—</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>

            <!-- Tab 2: Impact Dashboard -->
            <div id="tab-analytics" class="dash-content" role="tabpanel" aria-labelledby="tabbtn-analytics">
                <div class="analytics-wrap">
                    <div class="metrics-summary-grid">
                        <div class="summary-card">
                            <div class="summary-card-title">Total Requests</div>
                            <div class="summary-card-val" id="dash-requests">0</div>
                        </div>
                        <div class="summary-card">
                            <div class="summary-card-title">Cache Hit Rate</div>
                            <div class="summary-card-val" style="color:var(--blue);" id="dash-hitrate">0.0%</div>
                        </div>
                        <div class="summary-card">
                            <div class="summary-card-title">Total Tokens Saved</div>
                            <div class="summary-card-val" style="color:var(--green);" id="dash-tokens-saved">0</div>
                        </div>
                        <div class="summary-card">
                            <div class="summary-card-title">Estimated Cost Saved</div>
                            <div class="summary-card-val" style="color:var(--green);" id="dash-cost-saved">$0.00000</div>
                        </div>
                    </div>

                    <div class="chart-box">
                        <div class="demo-label-row">
                            <span class="demo-label">Latency Comparison: Upstream Miss vs Cache Hit (ms)</span>
                        </div>
                        <div style="height: calc(100% - 30px);">
                            <canvas id="latencyChart"></canvas>
                        </div>
                    </div>

                    <div class="table-wrap">
                        <table>
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Prompt</th>
                                    <th>Routing Tier</th>
                                    <th>Model Executed</th>
                                    <th>Cache Lookup</th>
                                    <th>Tokens (In / Opt)</th>
                                    <th>Latency</th>
                                    <th>Cost Saved</th>
                                </tr>
                            </thead>
                            <tbody id="queries-tbody">
                                <tr>
                                    <td colspan="8" style="text-align:center; color:var(--text-muted); padding:2.5rem;">No queries recorded yet. Send a request in the Sandbox!</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <!-- SETUP GUIDE / DOCS MODAL -->
    <div class="modal-backdrop" id="docs-modal" onclick="if(event.target===this) closeDocsModal()">
        <div class="modal-card">
            <div class="modal-head">
                <h3 style="font-size:1.35rem; font-weight:700;">Semantic Gateway Integration Guide</h3>
                <button class="modal-close" onclick="closeDocsModal()">&times;</button>
            </div>
            <p style="color:var(--text-secondary); margin-bottom:1.5rem; font-size:0.95rem;">
                Semantic Gateway acts as a high-performance proxy in front of Groq and local LLMs. Drop it into any OpenAI-compatible client library by changing the base URL.
            </p>

            <h4 style="font-size:0.95rem; font-weight:700; margin-bottom:0.5rem;">Python OpenAI SDK Configuration</h4>
            <div class="term-code-block" style="margin-top:0; margin-bottom:1.5rem;">
<span class="term-accent">from</span> openai <span class="term-accent">import</span> OpenAI

client = OpenAI(
    base_url=<span style="color:#a5d6ff;">"http://localhost:8000/v1"</span>,
    api_key=<span style="color:#a5d6ff;">"not-required"</span>  <span class="term-dim"># Server-side auth</span>
)

response = client.chat.completions.create(
    model=<span style="color:#a5d6ff;">"llama-3.1-8b-instant"</span>,
    messages=[{<span style="color:#a5d6ff;">"role"</span>: <span style="color:#a5d6ff;">"user"</span>, <span style="color:#a5d6ff;">"content"</span>: <span style="color:#a5d6ff;">"Hello!"</span>}]
)
print(response.choices[0].message.content)
            </div>

            <h4 style="font-size:0.95rem; font-weight:700; margin-bottom:0.5rem;">cURL Example</h4>
            <div class="term-code-block" style="margin-top:0;">
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "What is semantic caching?"}]
  }'
            </div>

            <div style="margin-top:2rem; text-align:right;">
                <button class="btn-primary" onclick="closeDocsModal()">Got it</button>
            </div>
        </div>
    </div>

    <!-- FOOTER -->
    <footer class="footer">
        <div class="footer-inner">
            <div class="footer-brand">
                <h4>Semantic Gateway</h4>
                <p>High-performance prompt compression, sub-50ms semantic vector caching, and cost-aware model routing.</p>
                <p style="margin-top:1rem; color:#5c606e; font-size:0.8rem;">Apache 2.0 Open Source</p>
            </div>
            <div class="footer-col">
                <h5>Navigation</h5>
                <ul>
                    <li><a href="#hero">Overview</a></li>
                    <li><a href="#features">Features</a></li>
                    <li><a href="#demo">Interactive Sandbox</a></li>
                    <li><a href="#quickstart">Quick Start</a></li>
                </ul>
            </div>
            <div class="footer-col">
                <h5>Resources</h5>
                <ul>
                    <li><a href="javascript:void(0)" onclick="openDocsModal()">API Documentation</a></li>
                    <li><a href="/api/metrics" target="_blank">Raw Metrics Endpoint</a></li>
                    <li><a href="/health" target="_blank">Health Check</a></li>
                    <li><a href="https://github.com/anothercodingguy/SemanticLLM" target="_blank">GitHub Repository</a></li>
                </ul>
            </div>
            <div class="footer-col">
                <h5>Architecture</h5>
                <ul>
                    <li><a href="#features">384-Dim FastEmbed Vectors</a></li>
                    <li><a href="#features">Groq Llama 3.1 & 3.3</a></li>
                    <li><a href="#features">Ollama Fallback</a></li>
                    <li><a href="#features">Context Deduplication</a></li>
                </ul>
            </div>
        </div>
    </footer>

    <!-- JAVASCRIPT LOGIC -->
    <script>
        let latencyChart = null;

        const PRESETS = {
            simple: "What does fetch_user return when the row is missing?",
            paraphrase: "What happens if fetch_user cannot find the database row?",
            noisy: "System Context & Retrieval Output:\n[2026-08-14 12:00:00 INFO] User initiated authentication flow\n[2026-08-14 12:00:00 INFO] User initiated authentication flow\n[2026-08-14 12:00:01 DEBUG] Connected to Postgres pool (4 active)\n[2026-08-14 12:00:01 DEBUG] Connected to Postgres pool (4 active)\n\nUser Question:\nHow do I configure connection pooling for high concurrency?",
            complex: "Analyze the architecture of a high-concurrency distributed event pipeline. Write Python code demonstrating an asynchronous worker pool with circuit breakers and fallback retry mechanisms."
        };

        function escapeHtml(unsafe) {
            return (unsafe || '').toString()
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        function loadPreset(key) {
            const input = document.getElementById('chat-input');
            input.value = PRESETS[key] || '';
            updateCharCount();
            input.focus();
        }

        function updateCharCount() {
            const val = document.getElementById('chat-input').value;
            const chars = val.length;
            const words = val.trim() ? val.trim().split(/\s+/).length : 0;
            const tokens = Math.max(0, Math.round(Math.max(words * 1.3, chars / 4)));
            document.getElementById('prompt-char-count').textContent = `${chars} chars · ~${tokens} tokens`;
        }

        function handleKey(e) {
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                sendMessage();
            }
        }

        function switchTab(tabId) {
            document.querySelectorAll('.dash-tab').forEach(el => {
                el.classList.remove('active');
                el.setAttribute('aria-selected', 'false');
            });
            document.querySelectorAll('.dash-content').forEach(el => el.classList.remove('active'));
            
            const btn = document.getElementById('tabbtn-' + tabId);
            const pane = document.getElementById('tab-' + tabId);
            if (btn) { btn.classList.add('active'); btn.setAttribute('aria-selected', 'true'); }
            if (pane) pane.classList.add('active');

            if (tabId === 'analytics') {
                fetchMetrics();
            }
        }

        function switchResultTab(tabId) {
            document.querySelectorAll('.res-tab-btn').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.res-pane').forEach(el => el.classList.remove('active'));
            
            const btn = document.getElementById('btn-res-' + tabId);
            const pane = document.getElementById('pane-' + tabId);
            if (btn) btn.classList.add('active');
            if (pane) pane.classList.add('active');
        }

        function openDocsModal() {
            document.getElementById('docs-modal').classList.add('open');
        }

        function closeDocsModal() {
            document.getElementById('docs-modal').classList.remove('open');
        }

        async function fetchMetrics() {
            try {
                const res = await fetch('/api/metrics');
                if (!res.ok) return;
                const data = await res.json();

                // Sandbox stats
                document.getElementById('val-requests').textContent = data.total_requests;
                document.getElementById('val-hits').textContent = data.cache_hits;
                document.getElementById('val-hitrate').textContent = data.hit_rate.toFixed(1) + '%';
                document.getElementById('val-tokens-in').textContent = data.total_tokens_in.toLocaleString();
                document.getElementById('val-tokens-saved').textContent = `${data.total_tokens_saved.toLocaleString()} (${data.token_reduction_rate.toFixed(1)}%)`;
                document.getElementById('val-spent').textContent = '$' + data.total_spent.toFixed(5);
                document.getElementById('val-saved').textContent = '$' + data.total_saved.toFixed(5);
                
                document.getElementById('val-latency-direct').textContent = data.avg_latency_miss > 0 ? Math.round(data.avg_latency_miss) + 'ms' : '—';
                document.getElementById('val-latency-cached').textContent = data.avg_latency_hit > 0 ? Math.round(data.avg_latency_hit) + 'ms' : '—';

                if (data.latest_model_route && data.latest_model_route !== '—') {
                    document.getElementById('val-latest-route').textContent = data.latest_model_route;
                }

                // Dashboard cards
                document.getElementById('dash-requests').textContent = data.total_requests;
                document.getElementById('dash-hitrate').textContent = data.hit_rate.toFixed(1) + '%';
                document.getElementById('dash-tokens-saved').textContent = data.total_tokens_saved.toLocaleString();
                document.getElementById('dash-cost-saved').textContent = '$' + data.total_saved.toFixed(5);

                // Update Table
                const tbody = document.getElementById('queries-tbody');
                if (data.queries && data.queries.length > 0) {
                    tbody.innerHTML = '';
                    data.queries.forEach(q => {
                        const tr = document.createElement('tr');
                        const routeBadge = (q.complexity || 'SIMPLE').toUpperCase() === 'COMPLEX' ? 'complex' : 'simple';
                        const cacheDot = q.is_cache_hit ? 'hit' : 'miss';
                        const cacheLabel = q.is_cache_hit ? `HIT (${q.similarity_score}%)` : 'MISS';
                        const timeStr = q.timestamp ? new Date(q.timestamp).toLocaleTimeString() : '—';

                        tr.innerHTML = `
                            <td style="color:var(--text-muted); font-size:0.8rem; font-family:var(--font-mono);">${escapeHtml(timeStr)}</td>
                            <td style="max-width:240px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${escapeHtml(q.prompt)}">${escapeHtml(q.prompt)}</td>
                            <td><span class="badge ${routeBadge}">${escapeHtml(q.complexity || 'SIMPLE')}</span></td>
                            <td style="font-family:var(--font-mono); font-size:0.8rem; color:var(--text-secondary);">${escapeHtml(q.model_routed)}</td>
                            <td><span class="status-dot ${cacheDot}"></span>${cacheLabel}</td>
                            <td style="font-family:var(--font-mono); font-size:0.8rem;">${q.original_tokens || 0} → ${q.optimized_tokens || 0}</td>
                            <td style="font-weight:600;">${Math.round(q.latency_ms)}ms</td>
                            <td style="color:var(--green); font-weight:600; font-family:var(--font-mono);">$${(q.cost_saved || 0).toFixed(5)}</td>
                        `;
                        tbody.appendChild(tr);
                    });

                    updateChart(data.queries);
                } else {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--text-muted); padding:2.5rem;">No queries recorded yet. Send a request in the Sandbox!</td></tr>';
                    updateChart([]);
                }
            } catch (err) {
                console.error('Metrics fetch error:', err);
            }
        }

        function updateChart(queries) {
            const chrono = [...queries].reverse().slice(-20);
            const labels = [], hitData = [], missData = [];
            chrono.forEach(q => {
                const d = new Date(q.timestamp);
                labels.push(d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
                if (q.is_cache_hit) {
                    hitData.push(q.latency_ms);
                    missData.push(null);
                } else {
                    missData.push(q.latency_ms);
                    hitData.push(null);
                }
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
                            borderWidth: 2,
                            tension: 0.1,
                            spanGaps: true
                        },
                        {
                            label: 'Direct Upstream Miss (ms)',
                            data: missData,
                            borderColor: '#f59e0b',
                            backgroundColor: '#f59e0b',
                            pointRadius: 5,
                            borderWidth: 2,
                            tension: 0.1,
                            spanGaps: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top', labels: { boxWidth: 12, font: { family: 'Inter', size: 12 } } }
                    },
                    scales: {
                        y: { beginAtZero: true, title: { display: true, text: 'Latency (ms)' }, grid: { color: 'rgba(0,0,0,0.04)' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }

        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const prompt = input.value.trim();
            const errBox = document.getElementById('error-alert');
            errBox.style.display = 'none';

            if (!prompt) {
                errBox.textContent = 'Please enter a prompt before submitting.';
                errBox.style.display = 'block';
                return;
            }

            const btn = document.getElementById('btn-send');
            const btnText = document.getElementById('btn-text');
            const btnSpinner = document.getElementById('btn-spinner');
            
            btn.disabled = true;
            btnText.textContent = 'Optimizing & Routing...';
            btnSpinner.style.display = 'inline-block';

            try {
                const res = await fetch('/v1/chat/completions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        messages: [{ role: 'user', content: prompt }]
                    })
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || `Server responded with status ${res.status}`);
                }

                const data = await res.json();
                
                // Display Results
                document.getElementById('result-container').style.display = 'block';

                // 1. Output pane
                const replyText = data.choices && data.choices[0] && data.choices[0].message ? data.choices[0].message.content : 'No response text received.';
                document.getElementById('res-text').textContent = replyText;

                // 2. Compression pane
                const comp = data.compression || {};
                const compPct = comp.compression_percent || 0.0;
                document.getElementById('res-tab-comp-pct').textContent = compPct > 0 ? `${compPct}% reduced` : '0%';
                document.getElementById('res-comp-summary').textContent = compPct > 0 
                    ? `Context compressed by ${compPct}% (${comp.tokens_saved} tokens eliminated)`
                    : 'Context is already concise; sent directly without loss.';
                
                document.getElementById('diff-orig-tokens').textContent = comp.original_tokens || 0;
                document.getElementById('diff-orig-text').textContent = comp.original_text || prompt;
                document.getElementById('diff-opt-tokens').textContent = comp.optimized_tokens || 0;
                document.getElementById('diff-saved-tokens').textContent = comp.tokens_saved || 0;
                document.getElementById('diff-opt-text').textContent = comp.optimized_text || prompt;

                const notesUl = document.getElementById('res-savings-notes');
                notesUl.innerHTML = '';
                (comp.savings_notes || []).forEach(note => {
                    const li = document.createElement('li');
                    li.textContent = note;
                    notesUl.appendChild(li);
                });

                // 3. Diagnostics pane
                const cache = data.cache || {};
                const routing = data.routing || {};
                const latency = data.latency || {};
                const cost = data.cost || {};

                document.getElementById('diag-cache').innerHTML = cache.hit
                    ? `<span style="color:var(--green); font-weight:bold;">HIT (${cache.similarity}% similarity)</span>`
                    : `<span style="color:var(--amber); font-weight:bold;">MISS</span> (Threshold: ${cache.threshold || 82}%)`;

                document.getElementById('diag-model').textContent = `${routing.model || data.model} [${routing.complexity || 'SIMPLE'}]`;
                document.getElementById('diag-latency').textContent = `${latency.total_ms || 0}ms (Cache: ${latency.cache_lookup_ms || 0}ms, Upstream: ${latency.upstream_inference_ms || 0}ms)`;
                document.getElementById('diag-cost').innerHTML = `<span style="color:var(--green); font-weight:bold;">Saved $${(cost.cost_saved || 0).toFixed(5)}</span> (Spent $${(cost.actual_spent || 0).toFixed(5)})`;

                // Update Metrics
                await fetchMetrics();

            } catch (err) {
                console.error(err);
                errBox.textContent = `Gateway Error: ${err.message}`;
                errBox.style.display = 'block';
            } finally {
                btn.disabled = false;
                btnText.textContent = 'Compress & Route';
                btnSpinner.style.display = 'none';
            }
        }

        // Initialize on load
        updateCharCount();
        fetchMetrics();
        setInterval(fetchMetrics, 8000);
    </script>
    <style>
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    </style>
</body>
</html>"""
    return HTMLResponse(content=html_content)
