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
    title="Semantic Gateway",
    description="Query-Aware Neural Prompt & Context Compression Engine for Chat, RAG, and Coding Agents with Semantic Vector Caching",
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

# Include router at both root and /v1 for full SuperCompress + OpenAI API compatibility
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
    Serves the complete SuperCompress-grade Semantic Gateway Developer Studio in authentic DeepSeek Obsidian Dark Glass aesthetic.
    """
    html_content = r"""<!DOCTYPE html>
<html lang="en-US" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Semantic Gateway — Cut Your LLM API Costs by ~65%</title>
    <meta name="description" content="Reduce LLM API costs by ~65% while preserving answer-critical evidence. Query-aware neural compression for chat, RAG, and coding agents with sub-50ms vector caching.">
    <!-- Google Fonts: DM Sans, Inter, JetBrains Mono -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        /* ═══════════════════════════════════════════════════════════════════
           DEEPSEEK HARNESS DESIGN SYSTEM (Dark Glass Obsidian Aesthetic)
           ═══════════════════════════════════════════════════════════════════ */
        :root {
            --ds-page: #0b0c0f;
            --ds-surface-1: #111317;
            --ds-surface-2: #16181f;
            --ds-surface-3: #1c1e27;
            --ds-surface-card: #15171e;
            --ds-border-default: rgba(255, 255, 255, 0.08);
            --ds-border-subtle: rgba(255, 255, 255, 0.04);
            --ds-border-hover: rgba(255, 255, 255, 0.18);
            --ds-brand: #4d88ff;
            --ds-brand-light: #679efe;
            --ds-brand-hover: #3b74f0;
            --ds-brand-glow: rgba(77, 136, 255, 0.35);
            --ds-brand-bg: rgba(77, 136, 255, 0.08);
            --ds-primary: #f0f2f7;
            --ds-secondary: #9aa0b0;
            --ds-description: #818798;
            --ds-muted: #535868;
            --ds-green: #28c840;
            --ds-green-glow: rgba(40, 200, 64, 0.25);
            --ds-amber: #febc2e;
            --ds-red: #ff5f57;
            --ds-purple: #a855f7;
            --font-sans: 'DM Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --font-mono: 'JetBrains Mono', 'SFMono-Regular', Consolas, Menlo, monospace;
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 18px;
            --radius-pill: 9999px;
            --shadow-subtle: 0 2px 10px rgba(0, 0, 0, 0.35);
            --shadow-card: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 1px rgba(255, 255, 255, 0.1);
            --shadow-glow: 0 0 35px rgba(77, 136, 255, 0.2);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        html { scroll-behavior: smooth; color-scheme: dark; }

        body {
            font-family: var(--font-sans);
            background: var(--ds-page);
            color: var(--ds-primary);
            line-height: 1.65;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            overflow-x: hidden;
            position: relative;
        }

        /* Ambient Mesh Glow */
        .ambient-mesh {
            position: fixed;
            top: 0; left: 0;
            width: 100vw; height: 100vh;
            pointer-events: none;
            z-index: 0;
            overflow: hidden;
        }
        .ambient-orb {
            position: absolute;
            border-radius: 50%;
            filter: blur(110px);
            opacity: 0.28;
            pointer-events: none;
            mix-blend-mode: screen;
        }
        .orb-1 { top: -150px; left: 20%; width: 650px; height: 650px; background: radial-gradient(circle, #2d5f9e 0%, #1a3870 55%, transparent 70%); }
        .orb-2 { top: 400px; right: 5%; width: 550px; height: 550px; background: radial-gradient(circle, #1e40af 0%, #0f275a 60%, transparent 70%); opacity: 0.18; }
        .orb-3 { bottom: 0px; left: 50%; transform: translateX(-50%); width: 900px; height: 450px; background: radial-gradient(ellipse at center, #2d5f9e 0%, #1a3870 45%, transparent 70%); opacity: 0.22; }

        #hero-canvas {
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            pointer-events: none;
            opacity: 0.65;
            mask-image: linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,0.85) 60%, transparent 100%);
            -webkit-mask-image: linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,0.85) 60%, transparent 100%);
        }

        /* Container */
        .ds-container { max-width: 1280px; margin: 0 auto; padding: 0 1.5rem; position: relative; z-index: 10; }

        /* Header */
        .ds-header-wrapper {
            position: sticky; top: 0; z-index: 100;
            background: rgba(11, 12, 15, 0.75);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border-bottom: 1px solid var(--ds-border-default);
            transition: all 0.25s ease;
        }
        .ds-header-bar {
            max-width: 1280px; margin: 0 auto;
            padding: 0.85rem 1.5rem;
            display: flex; align-items: center; justify-content: space-between;
        }
        .ds-logo-group {
            display: flex; align-items: center; gap: 0.75rem;
            text-decoration: none; color: #ffffff;
        }
        .ds-logo-mark {
            width: 28px; height: 28px; color: var(--ds-brand);
            display: flex; align-items: center; justify-content: center;
        }
        .ds-logo-text {
            font-size: 1.15rem; font-weight: 700; letter-spacing: -0.02em; color: #ffffff;
            display: flex; align-items: center; gap: 0.4rem;
        }
        .ds-pill-tag {
            display: inline-flex; align-items: center; padding: 1px; border-radius: 8px;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.6) 0%, rgba(255, 255, 255, 0.08) 35%, rgba(255, 255, 255, 0.04) 65%, rgba(255, 255, 255, 0.4) 100%);
            box-shadow: 0 0 16px rgba(255, 255, 255, 0.06);
        }
        .ds-pill-tag-inner {
            padding: 3px 8px; border-radius: 7px; font-family: var(--font-mono);
            font-size: 11px; font-weight: 600; line-height: 1; background: rgba(0, 0, 0, 0.4);
            color: rgba(255, 255, 255, 0.95); text-transform: uppercase; letter-spacing: 0.06em;
        }
        .ds-nav-links { display: flex; align-items: center; gap: 1.6rem; }
        .ds-nav-link {
            text-decoration: none; color: var(--ds-description);
            font-size: 0.88rem; font-weight: 500; transition: color 0.15s ease;
            cursor: pointer;
        }
        .ds-nav-link:hover { color: #ffffff; }

        .ds-header-actions { display: flex; align-items: center; gap: 0.85rem; }
        .ds-toggle-pill {
            display: inline-flex; align-items: center;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-pill); padding: 2px; gap: 2px;
        }
        .ds-toggle-btn {
            background: transparent; border: none; color: var(--ds-description);
            font-family: var(--font-mono); font-size: 11px; font-weight: 600;
            padding: 4px 10px; border-radius: var(--radius-pill); cursor: pointer;
            transition: all 0.15s ease;
        }
        .ds-toggle-btn.is-active { background: rgba(255, 255, 255, 0.12); color: #ffffff; }

        .ds-btn-header {
            display: inline-flex; align-items: center; gap: 0.4rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-sm); color: var(--ds-primary);
            font-size: 0.85rem; font-weight: 500; padding: 0.45rem 0.85rem;
            text-decoration: none; cursor: pointer; transition: all 0.2s ease;
        }
        .ds-btn-header:hover { background: rgba(255, 255, 255, 0.1); border-color: var(--ds-border-hover); color: #ffffff; }

        /* Buttons */
        .ds-btn-primary {
            display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem;
            background: linear-gradient(180deg, #3b82f6 0%, #1d4ed8 100%);
            color: #ffffff; text-decoration: none; font-size: 0.92rem; font-weight: 600;
            padding: 0.75rem 1.4rem; border-radius: var(--radius-sm);
            border: 1px solid rgba(255, 255, 255, 0.18);
            box-shadow: 0 0 20px rgba(37, 99, 235, 0.4), 0 2px 6px rgba(0, 0, 0, 0.3);
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1); cursor: pointer;
        }
        .ds-btn-primary:hover {
            background: linear-gradient(180deg, #60a5fa 0%, #2563eb 100%);
            box-shadow: 0 0 28px rgba(59, 130, 246, 0.55), 0 4px 12px rgba(0, 0, 0, 0.4);
            transform: translateY(-1px);
        }
        .ds-btn-secondary {
            display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem;
            background: rgba(255, 255, 255, 0.04); color: var(--ds-primary);
            text-decoration: none; font-size: 0.92rem; font-weight: 500;
            padding: 0.75rem 1.35rem; border-radius: var(--radius-sm);
            border: 1px solid var(--ds-border-default); backdrop-filter: blur(10px);
            transition: all 0.2s ease; cursor: pointer;
        }
        .ds-btn-secondary:hover { background: rgba(255, 255, 255, 0.08); border-color: var(--ds-border-hover); color: #ffffff; transform: translateY(-1px); }

        /* Hero */
        .ds-hero-section {
            padding: 5.5rem 0 4.5rem;
            min-height: calc(82vh - 70px);
            display: flex; align-items: center;
        }
        .ds-hero-grid {
            display: grid; grid-template-columns: 58fr 42fr;
            gap: 3.5rem; align-items: center; width: 100%;
        }
        .ds-hero-content { display: flex; flex-direction: column; align-items: flex-start; gap: 1.4rem; }

        .ds-hero-badge {
            display: inline-flex; align-items: center; padding: 1px; border-radius: 8px;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.42) 0%, rgba(255, 255, 255, 0.08) 35%, rgba(255, 255, 255, 0.04) 65%, rgba(255, 255, 255, 0.28) 100%);
            box-shadow: 0 0 16px rgba(255, 255, 255, 0.08);
        }
        .ds-hero-badge span {
            padding: 5px 12px; border-radius: 7px; background: rgba(0, 0, 0, 0.35);
            font-family: var(--font-mono); font-size: 12px; font-weight: 500;
            color: rgba(255, 255, 255, 0.95); line-height: 1; letter-spacing: 0.04em;
            display: flex; align-items: center; gap: 0.5rem;
        }
        .ds-status-dot-live {
            width: 7px; height: 7px; background: var(--ds-green); border-radius: 50%;
            box-shadow: 0 0 10px var(--ds-green); animation: pulse-live 2s infinite;
        }
        @keyframes pulse-live { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(0.85); } }

        .ds-text-hero {
            font-size: clamp(2.6rem, 5vw, 4.2rem);
            font-weight: 700; letter-spacing: -0.04em; line-height: 1.08; color: #ffffff;
        }
        .ds-brand-gradient {
            background: linear-gradient(135deg, #ffffff 0%, #9ec3ff 50%, #4d88ff 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .ds-text-body {
            font-size: 1.08rem; line-height: 1.65; color: var(--ds-description); max-width: 620px;
        }
        .ds-hero-cta-group { display: flex; flex-wrap: wrap; align-items: center; gap: 0.85rem; margin-top: 0.5rem; }

        /* Quickstart Tabbed Box */
        .ds-terminal-container { display: flex; flex-direction: column; width: 100%; }
        .ds-term-tabs { display: flex; gap: 4px; margin-left: 8px; z-index: 2; }
        .ds-term-tab {
            padding: 8px 14px; font-size: 12.5px; font-weight: 500;
            color: var(--ds-description); background: transparent;
            border: 1px solid transparent; border-bottom: none; border-radius: 8px 8px 0 0;
            cursor: pointer; transition: all 0.2s ease;
        }
        .ds-term-tab.active {
            color: #ffffff; background: rgba(18, 20, 26, 0.85);
            backdrop-filter: blur(16px); border-color: var(--ds-border-default);
        }
        .ds-term-box {
            background: rgba(18, 20, 26, 0.85);
            backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-card), var(--shadow-glow);
            overflow: hidden; position: relative;
        }
        .ds-term-header {
            display: flex; align-items: center; justify-content: space-between;
            padding: 0.75rem 1.25rem; border-bottom: 1px solid var(--ds-border-default);
            background: rgba(12, 13, 17, 0.5);
        }
        .ds-traffic-lights { display: flex; align-items: center; gap: 7px; }
        .ds-dot { width: 11px; height: 11px; border-radius: 50%; }
        .ds-dot.red { background: var(--ds-red); }
        .ds-dot.yellow { background: var(--ds-amber); }
        .ds-dot.green { background: var(--ds-green); }
        .ds-term-title { font-family: var(--font-mono); font-size: 12px; color: var(--ds-muted); }
        .ds-copy-btn {
            background: transparent; border: none; color: var(--ds-description);
            font-size: 12px; cursor: pointer; display: flex; align-items: center; gap: 5px;
            transition: color 0.15s ease;
        }
        .ds-copy-btn:hover { color: #ffffff; }
        .ds-term-body {
            padding: 1.35rem 1.5rem; font-family: var(--font-mono); font-size: 13px;
            line-height: 1.75; color: var(--ds-primary); overflow-x: auto; max-height: 290px;
        }
        .ds-prompt-sym { color: var(--ds-brand); font-weight: 700; user-select: none; }
        .ds-code-comment { color: var(--ds-muted); }
        .ds-code-keyword { color: #f472b6; }
        .ds-code-string { color: #93c5fd; }

        /* Value Metrics Bar */
        .ds-metrics-bar-section {
            padding: 2.5rem 0;
            border-top: 1px solid var(--ds-border-subtle);
            border-bottom: 1px solid var(--ds-border-subtle);
            background: rgba(255, 255, 255, 0.015);
        }
        .ds-val-grid-4 {
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 2rem;
        }
        .ds-val-card { display: flex; flex-direction: column; gap: 0.35rem; }
        .ds-val-num { font-size: 1.85rem; font-weight: 700; color: #ffffff; letter-spacing: -0.02em; }
        .ds-val-lbl { font-size: 0.95rem; font-weight: 600; color: var(--ds-brand-light); }
        .ds-val-sub { font-size: 0.85rem; color: var(--ds-description); line-height: 1.5; }

        /* Sections */
        .ds-section { padding: 5.5rem 0; position: relative; }
        .ds-section-header {
            max-width: 840px; margin: 0 auto 3rem; text-align: center;
            display: flex; flex-direction: column; align-items: center; gap: 1rem;
        }
        .ds-text-heading1 {
            font-size: clamp(2rem, 3.8vw, 2.8rem); font-weight: 700;
            letter-spacing: -0.03em; line-height: 1.18; color: #ffffff;
        }
        .ds-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }
        .ds-grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem; }
        .ds-card {
            background: var(--ds-surface-card); border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-md); padding: 2rem; display: flex;
            flex-direction: column; align-items: flex-start; text-align: left;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1); position: relative; overflow: hidden;
        }
        .ds-card:hover {
            border-color: var(--ds-border-hover); transform: translateY(-3px);
            box-shadow: 0 12px 36px rgba(0, 0, 0, 0.4), 0 0 20px rgba(77, 136, 255, 0.1);
        }
        .ds-card-icon { color: var(--ds-brand); margin-bottom: 1.25rem; }
        .ds-card-title { font-size: 1.25rem; font-weight: 600; color: #ffffff; margin-bottom: 0.6rem; }
        .ds-card-desc { font-size: 0.9rem; color: var(--ds-description); line-height: 1.65; margin-bottom: 0.85rem; }
        .ds-card-bullets { list-style: none; font-size: 0.85rem; color: var(--ds-secondary); line-height: 1.8; padding-left: 0; }
        .ds-card-bullets li::before { content: "• "; color: var(--ds-brand); font-weight: bold; }

        /* How It Works Steps */
        .ds-steps-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; margin-top: 2rem; }
        .ds-step-card {
            background: rgba(255, 255, 255, 0.025); border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-md); padding: 1.75rem; position: relative;
        }
        .ds-step-num {
            font-family: var(--font-mono); font-size: 1.8rem; font-weight: 700;
            color: var(--ds-brand); opacity: 0.7; margin-bottom: 0.5rem;
        }
        .ds-step-title { font-size: 1.15rem; font-weight: 600; color: #ffffff; margin-bottom: 0.4rem; }
        .ds-step-desc { font-size: 0.88rem; color: var(--ds-description); line-height: 1.6; }

        /* Benchmarks Table */
        .ds-bench-table-wrap {
            background: var(--ds-surface-card); border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-md); overflow-x: auto; box-shadow: var(--shadow-card);
            margin-top: 1.5rem;
        }
        table.ds-bench-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; text-align: left; }
        table.ds-bench-table th, table.ds-bench-table td { padding: 1.15rem 1.4rem; border-bottom: 1px solid var(--ds-border-subtle); }
        table.ds-bench-table th { background: rgba(0, 0, 0, 0.3); font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--ds-muted); font-weight: 700; }
        table.ds-bench-table tr:hover td { background: rgba(255, 255, 255, 0.02); }
        table.ds-bench-table tr.highlight-row td { background: rgba(77, 136, 255, 0.06); font-weight: 600; }
        .ds-pill-score { padding: 0.25rem 0.6rem; border-radius: 4px; font-weight: 700; font-size: 12px; display: inline-block; }
        .ds-pill-score.green { background: rgba(40, 200, 64, 0.15); color: #4ade80; border: 1px solid rgba(40, 200, 64, 0.3); }
        .ds-pill-score.amber { background: rgba(254, 188, 46, 0.15); color: #fde047; border: 1px solid rgba(254, 188, 46, 0.3); }
        .ds-pill-score.red { background: rgba(255, 95, 87, 0.15); color: #fca5a5; border: 1px solid rgba(255, 95, 87, 0.3); }

        /* Coding Agent MCP Section */
        .ds-agent-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 2rem; }
        .ds-agent-card {
            background: var(--ds-surface-card); border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-md); padding: 1.75rem; box-shadow: var(--shadow-card);
        }

        /* Developer Studio & Tabs */
        .ds-studio-tabs {
            display: flex; justify-content: center; gap: 1.5rem;
            margin-bottom: 2.5rem; border-bottom: 1px solid var(--ds-border-default);
        }
        .ds-studio-tab-btn {
            padding: 0.85rem 1.75rem; font-size: 1rem; font-weight: 600;
            color: var(--ds-description); background: transparent; border: none;
            border-bottom: 2px solid transparent; cursor: pointer; transition: all 0.2s ease; margin-bottom: -1px;
        }
        .ds-studio-tab-btn:hover { color: #ffffff; }
        .ds-studio-tab-btn.active {
            color: #ffffff; border-bottom-color: var(--ds-brand);
            text-shadow: 0 0 12px var(--ds-brand-glow);
        }
        .ds-tab-pane { display: none; }
        .ds-tab-pane.active { display: block; animation: ds-fadeIn 0.25s ease-in-out; }
        @keyframes ds-fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

        .ds-sandbox-grid { display: grid; grid-template-columns: 1.3fr 0.7fr; gap: 2rem; align-items: start; }
        .ds-glass-panel {
            background: var(--ds-surface-card); border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-md); padding: 1.75rem; box-shadow: var(--shadow-card);
        }
        .ds-panel-eyebrow {
            display: flex; align-items: center; justify-content: space-between;
            font-size: 11px; font-weight: 700; text-transform: uppercase;
            letter-spacing: 0.08em; color: var(--ds-muted); margin-bottom: 1rem;
        }

        /* Mode Selector */
        .ds-mode-selector-row {
            display: flex; align-items: center; gap: 0.75rem;
            margin-bottom: 1.2rem; padding: 0.6rem 0.85rem;
            background: rgba(0, 0, 0, 0.35); border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-sm);
        }
        .ds-mode-pill {
            background: transparent; border: 1px solid transparent; color: var(--ds-description);
            font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: var(--radius-pill);
            cursor: pointer; transition: all 0.15s ease;
        }
        .ds-mode-pill.active { background: var(--ds-brand-bg); border-color: rgba(77,136,255,0.4); color: #ffffff; }

        .ds-chip-row { display: flex; gap: 0.5rem; overflow-x: auto; padding-bottom: 0.75rem; margin-bottom: 1rem; }
        .ds-chip {
            background: rgba(255, 255, 255, 0.04); border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-pill); padding: 0.35rem 0.85rem; font-size: 0.8rem;
            font-weight: 500; color: var(--ds-description); cursor: pointer; white-space: nowrap; transition: all 0.15s ease;
        }
        .ds-chip:hover { background: rgba(77, 136, 255, 0.1); border-color: rgba(77, 136, 255, 0.4); color: #ffffff; }

        .ds-textarea {
            width: 100%; height: 140px; padding: 1rem;
            background: rgba(11, 12, 16, 0.8); border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-sm); font-family: var(--font-mono); font-size: 13px;
            color: #ffffff; line-height: 1.6; resize: vertical; outline: none; transition: border-color 0.2s ease;
        }
        .ds-textarea:focus { border-color: var(--ds-brand); box-shadow: 0 0 0 3px rgba(77, 136, 255, 0.15); }
        
        .ds-query-input {
            width: 100%; padding: 0.75rem 1rem; margin-top: 0.75rem;
            background: rgba(11, 12, 16, 0.8); border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-sm); font-family: var(--font-mono); font-size: 13px;
            color: #ffffff; outline: none; transition: border-color 0.2s ease;
        }
        .ds-query-input:focus { border-color: var(--ds-brand); box-shadow: 0 0 0 3px rgba(77, 136, 255, 0.15); }

        .ds-prompt-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 1rem; }
        .ds-token-badge { font-family: var(--font-mono); font-size: 12px; color: var(--ds-description); }

        /* Result Viewer */
        .ds-result-section { margin-top: 1.75rem; border-top: 1px solid var(--ds-border-default); padding-top: 1.5rem; }
        .ds-res-tabs { display: flex; gap: 0.5rem; margin-bottom: 1.25rem; flex-wrap: wrap; }
        .ds-res-tab-btn {
            background: rgba(255, 255, 255, 0.04); border: 1px solid var(--ds-border-default);
            padding: 0.4rem 0.95rem; border-radius: var(--radius-sm); font-size: 0.8rem;
            font-weight: 600; color: var(--ds-description); cursor: pointer; transition: all 0.15s ease;
        }
        .ds-res-tab-btn.active {
            background: var(--ds-brand); color: #ffffff; border-color: var(--ds-brand);
            box-shadow: 0 0 14px rgba(77, 136, 255, 0.35);
        }
        .ds-res-pane {
            display: none; background: rgba(11, 12, 16, 0.6);
            border: 1px solid var(--ds-border-default); border-radius: var(--radius-sm);
            padding: 1.25rem; font-size: 0.9rem; line-height: 1.65;
        }
        .ds-res-pane.active { display: block; }

        .ds-diff-box { font-family: var(--font-mono); font-size: 12px; line-height: 1.65; max-height: 260px; overflow-y: auto; }
        .ds-diff-orig {
            color: #fca5a5; background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.2); padding: 0.6rem; border-radius: 6px; margin-bottom: 0.6rem;
        }
        .ds-diff-opt {
            color: #86efac; background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.2); padding: 0.6rem; border-radius: 6px;
        }

        .ds-blocks-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        .ds-block-card {
            background: rgba(255, 255, 255, 0.025); border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-sm); padding: 0.85rem; font-size: 0.85rem;
        }
        .ds-block-card.kept { border-left: 3px solid var(--ds-green); }
        .ds-block-card.dropped { border-left: 3px solid var(--ds-red); opacity: 0.8; }
        .ds-block-head { display: flex; justify-content: space-between; font-weight: 600; color: #ffffff; margin-bottom: 0.35rem; }
        .ds-block-reason { font-size: 12px; color: var(--ds-description); }

        .ds-diag-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem; }
        .ds-diag-card {
            background: rgba(255, 255, 255, 0.03); border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-sm); padding: 0.85rem 1rem;
        }
        .ds-diag-lbl { font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--ds-muted); font-weight: 700; }
        .ds-diag-val { font-size: 0.95rem; font-weight: 600; color: #ffffff; margin-top: 0.25rem; }

        /* Sustainability Widget */
        .ds-sustain-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 0.5rem; }
        .ds-sustain-card {
            background: rgba(40, 200, 64, 0.06); border: 1px solid rgba(40, 200, 64, 0.25);
            border-radius: var(--radius-sm); padding: 1rem; text-align: center;
        }
        .ds-sustain-val { font-size: 1.35rem; font-weight: 700; color: #4ade80; }
        .ds-sustain-lbl { font-size: 11.5px; color: var(--ds-secondary); margin-top: 0.25rem; font-weight: 500; }

        /* Telemetry Right Panel */
        .ds-stat-row {
            display: flex; justify-content: space-between; align-items: center;
            padding: 0.9rem 0; border-bottom: 1px solid var(--ds-border-subtle); font-size: 0.9rem;
        }
        .ds-stat-row:last-child { border-bottom: none; }
        .ds-stat-name { color: var(--ds-description); font-weight: 500; }
        .ds-stat-val { font-weight: 600; color: #ffffff; text-align: right; }
        .ds-stat-val.brand { color: var(--ds-brand); }
        .ds-stat-val.green { color: var(--ds-green); }

        /* Impact Dashboard Grid */
        .ds-dash-summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.25rem; margin-bottom: 2rem; }
        .ds-summary-card {
            background: var(--ds-surface-card); border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-md); padding: 1.5rem; box-shadow: var(--shadow-subtle);
        }
        .ds-summary-lbl { font-size: 11px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.06em; color: var(--ds-muted); }
        .ds-summary-val { font-size: 1.75rem; font-weight: 700; color: #ffffff; margin-top: 0.5rem; }

        .ds-chart-box {
            background: var(--ds-surface-card); border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-md); padding: 2rem; margin-bottom: 2rem; height: 350px;
        }
        .ds-table-wrap {
            background: var(--ds-surface-card); border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-md); overflow-x: auto;
        }
        table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
        th, td { text-align: left; padding: 1.1rem 1.25rem; border-bottom: 1px solid var(--ds-border-subtle); }
        th { color: var(--ds-muted); font-weight: 700; text-transform: uppercase; font-size: 11px; letter-spacing: 0.06em; background: rgba(0, 0, 0, 0.25); }
        tr:last-child td { border-bottom: none; }
        tr:hover td { background: rgba(255, 255, 255, 0.02); }

        .ds-badge { padding: 0.25rem 0.6rem; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; }
        .ds-badge.simple { background: rgba(77, 136, 255, 0.15); color: var(--ds-brand-light); border: 1px solid rgba(77, 136, 255, 0.3); }
        .ds-badge.complex { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
        .ds-status-pill { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; font-weight: 600; }
        .ds-status-pill.hit { color: var(--ds-green); }
        .ds-status-pill.miss { color: var(--ds-amber); }

        /* Modal */
        .ds-modal-backdrop {
            display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.75); backdrop-filter: blur(8px); z-index: 200;
            align-items: center; justify-content: center; padding: 1.5rem;
        }
        .ds-modal-backdrop.open { display: flex; }
        .ds-modal-card {
            background: var(--ds-surface-1); border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-lg); box-shadow: var(--shadow-card), var(--shadow-glow);
            max-width: 720px; width: 100%; max-height: 88vh; overflow-y: auto; padding: 2.25rem;
        }
        .ds-modal-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
        .ds-modal-close { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: var(--ds-muted); }

        /* Footer */
        .ds-footer {
            background: #090a0d; border-top: 1px solid var(--ds-border-default);
            padding: 5rem 0 4rem; color: var(--ds-description); position: relative; z-index: 10;
        }
        .ds-footer-grid { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 3.5rem; }
        .ds-footer-brand h4 { font-size: 1.15rem; font-weight: 700; margin-bottom: 1rem; color: #ffffff; }
        .ds-footer-brand p { font-size: 0.88rem; color: var(--ds-description); line-height: 1.7; max-width: 320px; }
        .ds-footer-col h5 { font-size: 0.85rem; color: #ffffff; margin-bottom: 1.25rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; }
        .ds-footer-col ul { list-style: none; }
        .ds-footer-col li { margin-bottom: 0.75rem; }
        .ds-footer-col a { color: var(--ds-description); text-decoration: none; font-size: 0.88rem; transition: color 0.15s ease; cursor: pointer; }
        .ds-footer-col a:hover { color: #ffffff; }

        @media (max-width: 1024px) {
            .ds-hero-grid, .ds-sandbox-grid, .ds-agent-grid { grid-template-columns: 1fr; gap: 2.5rem; }
            .ds-grid-3, .ds-val-grid-4, .ds-grid-2, .ds-steps-grid { grid-template-columns: 1fr 1fr; }
            .ds-dash-summary-grid { grid-template-columns: repeat(2, 1fr); }
            .ds-footer-grid { grid-template-columns: 1fr 1fr; gap: 2.5rem; }
        }
        @media (max-width: 768px) {
            .ds-nav-links { display: none; }
            .ds-grid-3, .ds-grid-2, .ds-steps-grid, .ds-val-grid-4, .ds-dash-summary-grid, .ds-footer-grid, .ds-diag-grid, .ds-blocks-grid, .ds-sustain-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>

    <!-- Ambient Mesh Canvas -->
    <div class="ambient-mesh">
        <div class="ambient-orb orb-1"></div>
        <div class="ambient-orb orb-2"></div>
        <div class="ambient-orb orb-3"></div>
        <canvas id="hero-canvas"></canvas>
    </div>

    <!-- HEADER -->
    <header class="ds-header-wrapper">
        <div class="ds-header-bar">
            <a href="/" class="ds-logo-group" aria-label="Semantic Gateway Home">
                <div class="ds-logo-mark">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                        <polyline points="2 17 12 22 22 17"></polyline>
                        <polyline points="2 12 12 17 22 12"></polyline>
                    </svg>
                </div>
                <div class="ds-logo-text">
                    <span>Semantic Gateway</span>
                </div>
            </a>

            <nav class="ds-nav-links" aria-label="Main Navigation">
                <a href="#features" class="ds-nav-link">Architecture</a>
                <a href="#how-it-works" class="ds-nav-link">How it Works</a>
                <a href="#use-cases" class="ds-nav-link">Use Cases</a>
                <a href="#benchmarks" class="ds-nav-link">Benchmarks</a>
                <a href="#agents" class="ds-nav-link">Coding Agents</a>
                <a href="#demo" class="ds-nav-link" onclick="switchTab('sandbox')">Sandbox</a>
                <a href="#demo" class="ds-nav-link" onclick="switchTab('analytics')">Telemetry</a>
            </nav>

            <div class="ds-header-actions">
                <div class="ds-toggle-pill">
                    <button type="button" class="ds-toggle-btn is-active">Gateway Live</button>
                    <button type="button" class="ds-toggle-btn" onclick="openDocsModal()">Docs</button>
                </div>
                <a href="https://github.com/anothercodingguy/SemanticLLM" target="_blank" rel="noopener noreferrer" class="ds-btn-header" aria-label="GitHub Repository">
                    <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
                </a>
            </div>
        </div>
    </header>

    <main>
        <!-- HERO SECTION -->
        <section class="ds-hero-section">
            <div class="ds-container">
                <div class="ds-hero-grid">
                    <!-- Left: Hero Content -->
                    <div class="ds-hero-content">
                        <div class="ds-hero-badge">
                            <span><span class="ds-status-dot-live"></span> Query-Aware Neural Compression Engine · Groq & Ollama Connected</span>
                        </div>

                        <h1 class="ds-text-hero">
                            Cut Your LLM API Costs<br/>
                            <span class="ds-brand-gradient">by ~65% Safely.</span>
                        </h1>

                        <p class="ds-text-body">
                            For teams running chat, RAG, support, or coding agents. Semantic Gateway removes low-value context before inference—so your models do more with the tokens you already pay for.
                        </p>

                        <div class="ds-hero-cta-group">
                            <a href="#demo" onclick="switchTab('sandbox')" class="ds-btn-primary">
                                Try Interactive Sandbox
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                            </a>
                            <a href="#benchmarks" class="ds-btn-secondary">
                                Benchmarks
                            </a>
                            <a href="#agents" class="ds-btn-secondary">
                                Coding Agents (MCP)
                            </a>
                            <button onclick="openDocsModal()" class="ds-btn-secondary">
                                Integration Docs
                            </button>
                        </div>
                    </div>

                    <!-- Right: Tabbed Terminal Box -->
                    <div class="ds-terminal-container" id="quickstart">
                        <div class="ds-term-tabs">
                            <button class="ds-term-tab active" id="ttab-quick" onclick="switchTermTab('quick')">Quick start</button>
                            <button class="ds-term-tab" id="ttab-compress" onclick="switchTermTab('compress')">POST /compress</button>
                            <button class="ds-term-tab" id="ttab-sdk" onclick="switchTermTab('sdk')">Python SDK</button>
                            <button class="ds-term-tab" id="ttab-mcp" onclick="switchTermTab('mcp')">Agent MCP</button>
                        </div>

                        <div class="ds-term-box">
                            <div class="ds-term-header">
                                <div class="ds-traffic-lights">
                                    <span class="ds-dot red"></span>
                                    <span class="ds-dot yellow"></span>
                                    <span class="ds-dot green"></span>
                                </div>
                                <span class="ds-term-title">semantic-gateway — 127.0.0.1:8000</span>
                                <button class="ds-copy-btn" onclick="copyTermCode()">
                                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                                    <span id="copy-text">Copy</span>
                                </button>
                            </div>

                            <div class="ds-term-body">
                                <div id="term-pane-quick">
                                    <div class="ds-code-comment"># Start Semantic Gateway with SuperCompress engine</div>
                                    <div><span class="ds-prompt-sym">$ </span>uvicorn main:app --host 0.0.0.0 --port 8000 --reload</div>
                                    <br/>
                                    <div style="color:var(--ds-green);">✓ Initialized SuperCompress Engine (Compiler & Precision)</div>
                                    <div style="color:var(--ds-green);">✓ FastEmbed 384-dim Dense Vector Cache Ready</div>
                                    <div style="color:var(--ds-green);">✓ Complexity Router (Groq 8B & 70B) Active</div>
                                    <div style="color:var(--ds-muted);">Listening on http://127.0.0.1:8000 ▋</div>
                                </div>

                                <div id="term-pane-compress" style="display:none;">
                                    <div class="ds-code-comment"># Direct Context Compression Endpoint</div>
                                    <div>curl -X POST http://localhost:8000/v1/compress \</div>
                                    <div>  -H <span class="ds-code-string">"Content-Type: application/json"</span> \</div>
                                    <div>  -d <span class="ds-code-string">'{"context": "Huge log dump...", "query": "What failed in the last deploy?", "mode": "compiler"}'</span></div>
                                </div>

                                <div id="term-pane-sdk" style="display:none;">
                                    <div class="ds-code-comment"># Python Library SuperCompress Import</div>
                                    <div><span class="ds-code-keyword">from</span> services.compression <span class="ds-code-keyword">import</span> compress_for_turn</div>
                                    <br/>
                                    <div>res = compress_for_turn(context=chat_history, user_query=<span class="ds-code-string">"What failed?"</span>, mode=<span class="ds-code-string">"compiler"</span>)</div>
                                    <div>print(<span class="ds-code-string">f"Tokens Saved: {res['tokens_saved_pct']}% | Risk: {res['compression_risk']}"</span>)</div>
                                </div>

                                <div id="term-pane-mcp" style="display:none;">
                                    <div class="ds-code-comment"># Coding Agent MCP Plugin Setup (Cursor, Claude Code, Windsurf)</div>
                                    <div><span class="ds-prompt-sym">$ </span>npm install -g supercompress-proxy</div>
                                    <div><span class="ds-prompt-sym">$ </span>npx supercompress setup --proxy http://localhost:8000</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- VALUE METRICS BAR -->
        <section class="ds-metrics-bar-section">
            <div class="ds-container">
                <div class="ds-val-grid-4">
                    <div class="ds-val-card">
                        <div class="ds-val-num">~58–66%</div>
                        <div class="ds-val-lbl">Mean Token Cut</div>
                        <div class="ds-val-sub">Drop as much as possible on held-out LongBench / OOD dumps — typically ~58–66% mean cut.</div>
                    </div>
                    <div class="ds-val-card">
                        <div class="ds-val-num">99.4%</div>
                        <div class="ds-val-lbl">Critical Kept</div>
                        <div class="ds-val-sub">Target &gt;98% answer-critical retention. Pooled held-out gold containment: 99.4% (180/181).</div>
                    </div>
                    <div class="ds-val-card">
                        <div class="ds-val-num">~47ms</div>
                        <div class="ds-val-lbl">Query-Aware on CPU</div>
                        <div class="ds-val-sub">Semantic keep/drop vs the current ask. Zero extra LLM summarizer calls.</div>
                    </div>
                    <div class="ds-val-card">
                        <div class="ds-val-num">$0.00</div>
                        <div class="ds-val-lbl">Semantic Cache Hits</div>
                        <div class="ds-val-sub">Dense vector cosine similarity serves identical semantic intents at zero spend.</div>
                    </div>
                </div>
            </div>
        </section>

        <!-- HOW IT WORKS (4-Step Pipeline) -->
        <section class="ds-section" id="how-it-works">
            <div class="ds-container">
                <div class="ds-section-header">
                    <span class="ds-hero-badge">
                        <span>How It Works</span>
                    </span>
                    <h2 class="ds-text-heading1">
                        Compress before the model call.
                    </h2>
                    <p class="ds-text-body">
                        Context arrives oversized — chat history, docs, tool traces, and multi-file diffs piled into one prompt.
                    </p>
                </div>

                <div class="ds-steps-grid">
                    <div class="ds-step-card">
                        <div class="ds-step-num">01</div>
                        <div class="ds-step-title">Ingest</div>
                        <div class="ds-step-desc">Ingests chat turns, RAG chunks, multi-file diffs, and tool execution traces.</div>
                    </div>
                    <div class="ds-step-card">
                        <div class="ds-step-num">02</div>
                        <div class="ds-step-title">Score</div>
                        <div class="ds-step-desc">Scores semantic relevance and information density against the current query.</div>
                    </div>
                    <div class="ds-step-card">
                        <div class="ds-step-num">03</div>
                        <div class="ds-step-title">Keep</div>
                        <div class="ds-step-desc">Meaning-first retention locks answer-critical lines, imports, and fences.</div>
                    </div>
                    <div class="ds-step-card">
                        <div class="ds-step-num">04</div>
                        <div class="ds-step-title">Ship</div>
                        <div class="ds-step-desc">Sends ~65% fewer tokens to model inference, cutting latency and prefill cost.</div>
                    </div>
                </div>
            </div>
        </section>

        <!-- USE CASES THAT COMPOUND (All 6 SuperCompress Use Cases) -->
        <section class="ds-section" id="use-cases" style="background: rgba(0,0,0,0.2);">
            <div class="ds-container">
                <div class="ds-section-header">
                    <span class="ds-hero-badge">
                        <span>Use Cases That Compound</span>
                    </span>
                    <h2 class="ds-text-heading1">
                        Do more with less across every workload.
                    </h2>
                    <p class="ds-text-body">
                        From agentic coding to document-heavy work, meaning-first compression helps teams do more with less—without losing what matters.
                    </p>
                </div>

                <div class="ds-grid-3">
                    <!-- Use Case 1: Coding Agents -->
                    <div class="ds-card">
                        <div class="ds-card-icon">
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
                        </div>
                        <h3 class="ds-card-title">Coding Agents</h3>
                        <p class="ds-card-desc">Compress task history, repo context, tool traces, and diffs so agents reason farther inside the same context window—and spend less per turn.</p>
                        <ul class="ds-card-bullets">
                            <li>Shrink multi-file diffs before the model call</li>
                            <li>Keep plans + decisions, drop stale tool noise</li>
                            <li>Works as an MCP plugin across Cursor, Claude Code, Codex</li>
                        </ul>
                    </div>

                    <!-- Use Case 2: Long Conversations -->
                    <div class="ds-card">
                        <div class="ds-card-icon">
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                        </div>
                        <h3 class="ds-card-title">Long Conversations</h3>
                        <p class="ds-card-desc">Keep long chats useful and coherent. Retains decisions, constraints, and facts that drive better answers—not every filler turn.</p>
                        <ul class="ds-card-bullets">
                            <li>Lower cost on multi-hour support or sales threads</li>
                            <li>Preserve user preferences and commitments</li>
                            <li>Reduce latency as history grows</li>
                        </ul>
                    </div>

                    <!-- Use Case 3: RAG & Search -->
                    <div class="ds-card">
                        <div class="ds-card-icon">
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                        </div>
                        <h3 class="ds-card-title">RAG & Search</h3>
                        <p class="ds-card-desc">Retrieved chunks often drown the query. Compress retrieved context so the model sees the evidence that matters for the current ask.</p>
                        <ul class="ds-card-bullets">
                            <li>Cut redundant passages across top-k results</li>
                            <li>Keep citations and key claims intact</li>
                            <li>Fit more evidence into the same budget</li>
                        </ul>
                    </div>

                    <!-- Use Case 4: Support Copilots -->
                    <div class="ds-card">
                        <div class="ds-card-icon">
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
                        </div>
                        <h3 class="ds-card-title">Support Copilots</h3>
                        <p class="ds-card-desc">Ticket history, macros, and knowledge-base hits add up fast. Compress before generation to keep replies accurate without burning tokens.</p>
                        <ul class="ds-card-bullets">
                            <li>Prioritize current issue + account state</li>
                            <li>Drop repeated boilerplate from prior tickets</li>
                            <li>Ship faster replies at lower per-ticket cost</li>
                        </ul>
                    </div>

                    <!-- Use Case 5: Document Workflows -->
                    <div class="ds-card">
                        <div class="ds-card-icon">
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                        </div>
                        <h3 class="ds-card-title">Document Workflows</h3>
                        <p class="ds-card-desc">Specs, tickets, research notes, and PRDs are dense. Compress for reviews and synthesis while retaining requirements and decisions.</p>
                        <ul class="ds-card-bullets">
                            <li>Faster design and compliance reviews</li>
                            <li>Keep must-have constraints and questions</li>
                            <li>Pair with human-in-the-loop editing</li>
                        </ul>
                    </div>

                    <!-- Use Case 6: Production Inference -->
                    <div class="ds-card">
                        <div class="ds-card-icon">
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>
                        </div>
                        <h3 class="ds-card-title">Production Inference</h3>
                        <p class="ds-card-desc">Reduce token usage and latency in live apps while preserving output quality. Run locally on CPU or deploy beside your API gateway.</p>
                        <ul class="ds-card-bullets">
                            <li>5–20ms local compression path</li>
                            <li>Drop-in before OpenAI, Anthropic, Groq</li>
                            <li>Meaning retention built for production</li>
                        </ul>
                    </div>
                </div>
            </div>
        </section>

        <!-- BENCHMARKS SECTION -->
        <section class="ds-section" id="benchmarks">
            <div class="ds-container">
                <div class="ds-section-header">
                    <span class="ds-hero-badge">
                        <span>LLM Context Compression Benchmarks</span>
                    </span>
                    <h2 class="ds-text-heading1">
                        Same budget. Who keeps the answer?
                    </h2>
                    <p class="ds-text-body">
                        Fair test: every method keeps only 35% of prompt tokens. The critical metric is oracle recall — whether answer-bearing evidence survives compression.
                    </p>
                </div>

                <div class="ds-bench-table-wrap">
                    <table class="ds-bench-table">
                        <thead>
                            <tr>
                                <th>Method</th>
                                <th>Answer-Critical Recall</th>
                                <th>Mean Token Cut</th>
                                <th>Extra Model Calls</th>
                                <th>Latency (CPU)</th>
                                <th>Quality Gate</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr class="highlight-row">
                                <td><strong style="color:var(--ds-brand-light);">Semantic Gateway (SuperCompress)</strong></td>
                                <td><span class="ds-pill-score green">100.0% Oracle Recall</span></td>
                                <td><strong style="color:var(--ds-green);">65.2% Cut</strong></td>
                                <td><strong style="color:var(--ds-green);">$0 (Zero Calls)</strong></td>
                                <td><strong>~42ms</strong></td>
                                <td><span class="ds-badge simple">Passed (&ge;98%)</span></td>
                            </tr>
                            <tr>
                                <td>H2O Heavy Hitter</td>
                                <td><span class="ds-pill-score green">97.9%</span></td>
                                <td>65.0% Cut</td>
                                <td>$0 (Zero Calls)</td>
                                <td>~120ms</td>
                                <td><span class="ds-badge simple">Passed</span></td>
                            </tr>
                            <tr>
                                <td>LLM Summarization Call</td>
                                <td><span class="ds-pill-score amber">60.5%</span></td>
                                <td>65.0% Cut</td>
                                <td><span style="color:var(--ds-red); font-weight:600;">+1 Full LLM Call ($$$)</span></td>
                                <td>~1,850ms</td>
                                <td><span class="ds-badge complex">High Cost & Lag</span></td>
                            </tr>
                            <tr>
                                <td>Truncation / FIFO Rolling Window</td>
                                <td><span class="ds-pill-score red">24.8% (Answers Lost)</span></td>
                                <td>65.0% Cut</td>
                                <td>$0 (Zero Calls)</td>
                                <td>~2ms</td>
                                <td><span class="ds-badge complex" style="background:rgba(239,68,68,0.2); color:#fca5a5;">Failed Gate</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div style="margin-top:1.5rem; text-align:center; font-size:0.85rem; color:var(--ds-muted);">
                    Evaluated on LongBench, RFC/Wiki haystacks, and fresh compiler suites. Pooled gold answer containment: 99.4% (180/181).
                </div>
            </div>
        </section>

        <!-- CODING AGENTS & MCP SECTION -->
        <section class="ds-section" id="agents" style="background: rgba(0,0,0,0.25);">
            <div class="ds-container">
                <div class="ds-section-header">
                    <span class="ds-hero-badge">
                        <span>Coding Agent Plugin · MCP-First</span>
                    </span>
                    <h2 class="ds-text-heading1">
                        One Install. Every Agent. Fewer Tokens.
                    </h2>
                    <p class="ds-text-body">
                        Auto-detect Cursor, Claude Code, Codex, OpenCode, Windsurf, and more. The MCP plugin compresses huge dumps before they burn tokens — keep your normal login.
                    </p>
                </div>

                <div class="ds-agent-grid">
                    <div class="ds-agent-card">
                        <h3 style="font-size:1.2rem; font-weight:600; color:#ffffff; margin-bottom:0.75rem;">Cursor & Windsurf (MCP Proxy)</h3>
                        <p style="font-size:0.9rem; color:var(--ds-description); margin-bottom:1rem;">
                            Add Semantic Gateway as your MCP server in Cursor settings to compress multi-file workspace dumps automatically before model turns.
                        </p>
                        <div style="background:rgba(0,0,0,0.5); border:1px solid var(--ds-border-default); border-radius:8px; padding:1rem; font-family:var(--font-mono); font-size:12px; color:#cbd5e1;">
                            <div class="ds-code-comment"># .cursor/mcp.json</div>
                            {<br/>
                            &nbsp;&nbsp;<span class="ds-code-string">"mcpServers"</span>: {<br/>
                            &nbsp;&nbsp;&nbsp;&nbsp;<span class="ds-code-string">"semantic-gateway"</span>: {<br/>
                            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="ds-code-string">"command"</span>: <span class="ds-code-string">"npx"</span>,<br/>
                            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="ds-code-string">"args"</span>: [<span class="ds-code-string">"-y"</span>, <span class="ds-code-string">"supercompress-proxy"</span>, <span class="ds-code-string">"--port"</span>, <span class="ds-code-string">"8000"</span>]<br/>
                            &nbsp;&nbsp;&nbsp;&nbsp;}<br/>
                            &nbsp;&nbsp;}<br/>
                            }
                        </div>
                    </div>

                    <div class="ds-agent-card">
                        <h3 style="font-size:1.2rem; font-weight:600; color:#ffffff; margin-bottom:0.75rem;">Claude Code & Terminal Agents</h3>
                        <p style="font-size:0.9rem; color:var(--ds-description); margin-bottom:1rem;">
                            Pass the Gateway URL as your base endpoint. Shrinks bash outputs, git diffs, and project trees before each turn.
                        </p>
                        <div style="background:rgba(0,0,0,0.5); border:1px solid var(--ds-border-default); border-radius:8px; padding:1rem; font-family:var(--font-mono); font-size:12px; color:#cbd5e1;">
                            <div class="ds-code-comment"># Environment configuration</div>
                            <span class="ds-code-keyword">export</span> ANTHROPIC_BASE_URL=<span class="ds-code-string">"http://localhost:8000/v1"</span><br/>
                            <span class="ds-code-keyword">export</span> OPENAI_BASE_URL=<span class="ds-code-string">"http://localhost:8000/v1"</span><br/>
                            <br/>
                            <div class="ds-code-comment"># Start agent with compressed context</div>
                            claude --dangerously-skip-permissions
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- DEVELOPER STUDIO (SANDBOX & TELEMETRY DASHBOARD) -->
        <section class="ds-section" id="demo">
            <div class="ds-container">
                <div class="ds-studio-tabs" role="tablist">
                    <button class="ds-studio-tab-btn active" id="tabbtn-sandbox" onclick="switchTab('sandbox')" role="tab" aria-selected="true" aria-controls="tab-sandbox">Interactive Local Playground</button>
                    <button class="ds-studio-tab-btn" id="tabbtn-analytics" onclick="switchTab('analytics')" role="tab" aria-selected="false" aria-controls="tab-analytics">Impact Dashboard</button>
                </div>

                <!-- TAB 1: SANDBOX / PLAYGROUND -->
                <div id="tab-sandbox" class="ds-tab-pane active" role="tabpanel" aria-labelledby="tabbtn-sandbox">
                    <div class="ds-sandbox-grid">
                        <!-- Left: Input & Inspector -->
                        <div class="ds-glass-panel">
                            <div class="ds-panel-eyebrow">
                                <span>1. Select Preset & Input Context</span>
                                <span class="ds-token-badge" id="prompt-char-count">0 chars · ~0 tokens</span>
                            </div>

                            <!-- Mode Selector -->
                            <div class="ds-mode-selector-row">
                                <span style="font-size:11px; font-weight:700; text-transform:uppercase; color:var(--ds-muted); margin-right:4px;">Mode:</span>
                                <button type="button" class="ds-mode-pill active" id="mode-compiler" onclick="setCompressionMode('compiler')">Compiler Mode (Auto)</button>
                                <button type="button" class="ds-mode-pill" id="mode-precision" onclick="setCompressionMode('precision')">Precision (&ge;98% Gate)</button>
                                <button type="button" class="ds-mode-pill" id="mode-fixed" onclick="setCompressionMode('fixed')">Fixed 35% Budget</button>
                            </div>

                            <!-- Presets for all use cases -->
                            <div class="ds-chip-row" aria-label="Preset Prompts">
                                <button type="button" class="ds-chip" onclick="loadPreset('support')">⚡ Support Ticket</button>
                                <button type="button" class="ds-chip" onclick="loadPreset('paraphrase')">🎯 Semantic Cache Hit</button>
                                <button type="button" class="ds-chip" onclick="loadPreset('diff')">🧹 Multi-file Diff / Code Trace</button>
                                <button type="button" class="ds-chip" onclick="loadPreset('rag')">📚 RAG Search Chunks</button>
                                <button type="button" class="ds-chip" onclick="loadPreset('complex')">🧠 Architecture PRD</button>
                            </div>

                            <textarea class="ds-textarea" id="chat-input" placeholder="Paste your long context, logs, code diffs, or chat history here..." oninput="updateCharCount()" onkeydown="handleKey(event)"></textarea>

                            <input type="text" class="ds-query-input" id="query-input" placeholder="User Query (e.g. 'What failed in the last deploy?' or 'What is the refund decision?')" value="What was the supervisor decision regarding the refund request?">

                            <div class="ds-prompt-footer">
                                <div style="font-size:12px; color:var(--ds-muted);">
                                    Press <kbd style="background:rgba(255,255,255,0.06); padding:2px 6px; border:1px solid var(--ds-border-default); border-radius:4px; font-family:var(--font-mono);">Cmd/Ctrl+Enter</kbd>
                                </div>
                                <button class="ds-btn-primary" id="btn-send" onclick="sendMessage()">
                                    <span id="btn-spinner" style="display:none; width:14px; height:14px; border:2px solid #fff; border-top-color:transparent; border-radius:50%; animation:spin 0.8s linear infinite;"></span>
                                    <span id="btn-text">Compress & Route</span>
                                </button>
                            </div>

                            <div id="error-alert" style="display:none; margin-top:1rem; padding:0.85rem 1rem; background:rgba(239, 68, 68, 0.15); border:1px solid rgba(239, 68, 68, 0.3); border-radius:var(--radius-sm); color:#fca5a5; font-size:13.5px;"></div>

                            <!-- Results Inspector -->
                            <div class="ds-result-section" id="result-container" style="display:none;">
                                <div class="ds-panel-eyebrow">
                                    <span>2. Optimization & Evidence Breakdown</span>
                                </div>

                                <div class="ds-res-tabs">
                                    <button type="button" class="ds-res-tab-btn active" id="btn-res-output" onclick="switchResultTab('output')">Model Output</button>
                                    <button type="button" class="ds-res-tab-btn" id="btn-res-compression" onclick="switchResultTab('compression')">Context Diff (<span id="res-tab-comp-pct">0%</span>)</button>
                                    <button type="button" class="ds-res-tab-btn" id="btn-res-blocks" onclick="switchResultTab('blocks')">Kept vs Dropped Blocks</button>
                                    <button type="button" class="ds-res-tab-btn" id="btn-res-diag" onclick="switchResultTab('diag')">Routing & Cache</button>
                                    <button type="button" class="ds-res-tab-btn" id="btn-res-sustain" onclick="switchResultTab('sustain')">CO₂ & Energy Impact</button>
                                </div>

                                <!-- Tab: Output -->
                                <div class="ds-res-pane active" id="pane-output">
                                    <div id="res-text" style="color:var(--ds-primary); white-space:pre-wrap;"></div>
                                </div>

                                <!-- Tab: Compression Diff -->
                                <div class="ds-res-pane" id="pane-compression">
                                    <div style="margin-bottom:0.75rem; font-weight:600; color:#ffffff;" id="res-comp-summary"></div>
                                    <div class="ds-diff-box">
                                        <div class="ds-diff-orig">
                                            <div style="font-size:11px; font-weight:bold; margin-bottom:0.25rem;">ORIGINAL PROMPT CONTEXT (<span id="diff-orig-tokens">0</span> tokens)</div>
                                            <div id="diff-orig-text"></div>
                                        </div>
                                        <div class="ds-diff-opt">
                                            <div style="font-size:11px; font-weight:bold; margin-bottom:0.25rem;">COMPRESSED EVIDENCE (<span id="diff-opt-tokens">0</span> tokens — <span id="diff-saved-tokens">0</span> saved)</div>
                                            <div id="diff-opt-text"></div>
                                        </div>
                                    </div>
                                    <ul id="res-savings-notes" style="margin-top:0.75rem; padding-left:1.25rem; font-size:12.5px; color:var(--ds-description);"></ul>
                                </div>

                                <!-- Tab: Kept vs Dropped Blocks -->
                                <div class="ds-res-pane" id="pane-blocks">
                                    <div style="font-size:12.5px; color:var(--ds-description); margin-bottom:1rem;">
                                        Query-aware compiler segments context into semantic blocks and drops unneeded noise while locking critical evidence:
                                    </div>
                                    <div class="ds-blocks-grid">
                                        <div>
                                            <div style="font-size:11px; font-weight:700; color:var(--ds-green); margin-bottom:0.5rem; text-transform:uppercase;">Kept Evidence Blocks</div>
                                            <div id="kept-blocks-list" style="display:flex; flex-direction:column; gap:0.6rem;"></div>
                                        </div>
                                        <div>
                                            <div style="font-size:11px; font-weight:700; color:var(--ds-red); margin-bottom:0.5rem; text-transform:uppercase;">Removed Low-Value Blocks</div>
                                            <div id="dropped-blocks-list" style="display:flex; flex-direction:column; gap:0.6rem;"></div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Tab: Diagnostics -->
                                <div class="ds-res-pane" id="pane-diag">
                                    <div class="ds-diag-grid">
                                        <div class="ds-diag-card">
                                            <div class="ds-diag-lbl">Semantic Cache Status</div>
                                            <div class="ds-diag-val" id="diag-cache">—</div>
                                        </div>
                                        <div class="ds-diag-card">
                                            <div class="ds-diag-lbl">Selected Model Route</div>
                                            <div class="ds-diag-val" id="diag-model" style="font-family:var(--font-mono); font-size:0.85rem;">—</div>
                                        </div>
                                        <div class="ds-diag-card">
                                            <div class="ds-diag-lbl">Total Latency</div>
                                            <div class="ds-diag-val" id="diag-latency">—</div>
                                        </div>
                                        <div class="ds-diag-card">
                                            <div class="ds-diag-lbl">Cost Comparison</div>
                                            <div class="ds-diag-val" id="diag-cost">—</div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Tab: Sustainability Impact -->
                                <div class="ds-res-pane" id="pane-sustain">
                                    <div style="font-size:12.5px; color:var(--ds-description); margin-bottom:0.75rem;">
                                        Environmental impact of tokens removed prior to upstream GPU prefill work:
                                    </div>
                                    <div class="ds-sustain-grid">
                                        <div class="ds-sustain-card">
                                            <div class="ds-sustain-val" id="sustain-co2">0.0000 g</div>
                                            <div class="ds-sustain-lbl">CO₂ Avoided</div>
                                        </div>
                                        <div class="ds-sustain-card">
                                            <div class="ds-sustain-val" id="sustain-watt">0.000 Wh</div>
                                            <div class="ds-sustain-lbl">Energy Saved</div>
                                        </div>
                                        <div class="ds-sustain-card">
                                            <div class="ds-sustain-val" id="sustain-gpu">0.000 s</div>
                                            <div class="ds-sustain-lbl">GPU-sec Spared</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Right: Live Telemetry Panel -->
                        <div class="ds-glass-panel">
                            <div class="ds-panel-eyebrow">
                                <span>TOKEN & INFERENCE IMPACT</span>
                                <span style="font-size:11px; color:var(--ds-green); font-weight:600;"><span class="ds-status-dot-live" style="display:inline-block; vertical-align:middle; margin-right:4px;"></span> LIVE</span>
                            </div>

                            <ul style="list-style:none;">
                                <li class="ds-stat-row">
                                    <span class="ds-stat-name">Total Requests Analyzed</span>
                                    <span class="ds-stat-val" id="val-requests">0</span>
                                </li>
                                <li class="ds-stat-row">
                                    <span class="ds-stat-name">Cache Hits</span>
                                    <span class="ds-stat-val" id="val-hits">0</span>
                                </li>
                                <li class="ds-stat-row">
                                    <span class="ds-stat-name">Cache Efficiency</span>
                                    <span class="ds-stat-val brand" id="val-hitrate">0.0%</span>
                                </li>
                                <li class="ds-stat-row">
                                    <span class="ds-stat-name">Tokens Processed</span>
                                    <span class="ds-stat-val" id="val-tokens-in">0</span>
                                </li>
                                <li class="ds-stat-row">
                                    <span class="ds-stat-name">Tokens Saved (Compression)</span>
                                    <span class="ds-stat-val green" id="val-tokens-saved">0</span>
                                </li>
                                <li class="ds-stat-row">
                                    <span class="ds-stat-name">API Spend Estimated</span>
                                    <span class="ds-stat-val" id="val-spent">$0.00000</span>
                                </li>
                                <li class="ds-stat-row">
                                    <span class="ds-stat-name">API Cost Saved</span>
                                    <span class="ds-stat-val green" id="val-saved">$0.00000</span>
                                </li>
                                <li class="ds-stat-row">
                                    <span class="ds-stat-name">Latency (Direct Miss)</span>
                                    <div style="text-align:right;">
                                        <span class="ds-stat-val" id="val-latency-direct">—</span>
                                        <div style="font-size:11px; color:var(--ds-muted);">avg. upstream</div>
                                    </div>
                                </li>
                                <li class="ds-stat-row">
                                    <span class="ds-stat-name">Latency (Semantic Hit)</span>
                                    <div style="text-align:right;">
                                        <span class="ds-stat-val brand" id="val-latency-cached">—</span>
                                        <div style="font-size:11px; color:var(--ds-muted);">avg. vector cache</div>
                                    </div>
                                </li>
                                <li class="ds-stat-row">
                                    <span class="ds-stat-name">Latest Model Route</span>
                                    <span class="ds-stat-val" id="val-latest-route" style="font-family:var(--font-mono); font-size:12px;">—</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- TAB 2: IMPACT DASHBOARD -->
                <div id="tab-analytics" class="ds-tab-pane" role="tabpanel" aria-labelledby="tabbtn-analytics">
                    <div class="ds-dash-summary-grid">
                        <div class="ds-summary-card">
                            <div class="ds-summary-lbl">Total Requests</div>
                            <div class="ds-summary-val" id="dash-requests">0</div>
                        </div>
                        <div class="ds-summary-card">
                            <div class="ds-summary-lbl">Cache Hit Rate</div>
                            <div class="ds-summary-val" style="color:var(--ds-brand);" id="dash-hitrate">0.0%</div>
                        </div>
                        <div class="ds-summary-card">
                            <div class="ds-summary-lbl">Total Tokens Saved</div>
                            <div class="ds-summary-val" style="color:var(--ds-green);" id="dash-tokens-saved">0</div>
                        </div>
                        <div class="ds-summary-card">
                            <div class="ds-summary-lbl">Estimated Cost Saved</div>
                            <div class="ds-summary-val" style="color:var(--ds-green);" id="dash-cost-saved">$0.00000</div>
                        </div>
                    </div>

                    <div class="ds-chart-box">
                        <div class="ds-panel-eyebrow">
                            <span>Latency Comparison: Direct Upstream Miss vs FastEmbed Cache Hit (ms)</span>
                        </div>
                        <div style="height: calc(100% - 30px);">
                            <canvas id="latencyChart"></canvas>
                        </div>
                    </div>

                    <div class="ds-table-wrap">
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
                                    <td colspan="8" style="text-align:center; color:var(--ds-muted); padding:2.5rem;">No queries recorded yet. Send a request in the Sandbox!</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <!-- SETUP GUIDE & DOCS MODAL -->
    <div class="ds-modal-backdrop" id="docs-modal" onclick="if(event.target===this) closeDocsModal()">
        <div class="ds-modal-card">
            <div class="ds-modal-head">
                <h3 style="font-size:1.35rem; font-weight:700; color:#ffffff;">Semantic Gateway & SuperCompress API Guide</h3>
                <button class="ds-modal-close" onclick="closeDocsModal()">&times;</button>
            </div>
            <p style="color:var(--ds-description); margin-bottom:1.5rem; font-size:0.95rem;">
                Semantic Gateway is a high-performance proxy and compression engine. Drop it in front of OpenAI, Anthropic, Groq, or local models.
            </p>

            <h4 style="font-size:0.95rem; font-weight:700; margin-bottom:0.5rem; color:#ffffff;">1. SuperCompress Endpoint (POST /v1/compress)</h4>
            <div style="background:rgba(0,0,0,0.5); border:1px solid var(--ds-border-default); border-radius:8px; padding:1rem; font-family:var(--font-mono); font-size:12.5px; color:#cbd5e1; margin-bottom:1.5rem;">
curl -X POST http://localhost:8000/v1/compress \
  -H <span class="ds-code-string">"Content-Type: application/json"</span> \
  -d '{
    <span class="ds-code-string">"context"</span>: <span class="ds-code-string">"Your long conversation, RAG dump, or tool traces..."</span>,
    <span class="ds-code-string">"query"</span>: <span class="ds-code-string">"What failed in the last deploy?"</span>,
    <span class="ds-code-string">"mode"</span>: <span class="ds-code-string">"compiler"</span>
  }'
            </div>

            <h4 style="font-size:0.95rem; font-weight:700; margin-bottom:0.5rem; color:#ffffff;">2. Python Library SDK</h4>
            <div style="background:rgba(0,0,0,0.5); border:1px solid var(--ds-border-default); border-radius:8px; padding:1rem; font-family:var(--font-mono); font-size:12.5px; color:#cbd5e1; margin-bottom:1.5rem;">
<span class="ds-code-keyword">from</span> services.compression <span class="ds-code-keyword">import</span> compress_for_turn, compress_context

result = compress_for_turn(
    context=chat_history,
    user_query=<span class="ds-code-string">"Explain connection pool timeout"</span>,
    mode=<span class="ds-code-string">"compiler"</span>
)
print(result[<span class="ds-code-string">"compressed_text"</span>])
print(result[<span class="ds-code-string">"tokens_saved_pct"</span>])
            </div>

            <h4 style="font-size:0.95rem; font-weight:700; margin-bottom:0.5rem; color:#ffffff;">3. OpenAI Drop-In Proxy (POST /v1/chat/completions)</h4>
            <div style="background:rgba(0,0,0,0.5); border:1px solid var(--ds-border-default); border-radius:8px; padding:1rem; font-family:var(--font-mono); font-size:12.5px; color:#cbd5e1;">
<span class="ds-code-keyword">from</span> openai <span class="ds-code-keyword">import</span> OpenAI

client = OpenAI(base_url=<span class="ds-code-string">"http://localhost:8000/v1"</span>, api_key=<span class="ds-code-string">"not-required"</span>)
response = client.chat.completions.create(
    model=<span class="ds-code-string">"llama-3.1-8b-instant"</span>,
    messages=[{<span class="ds-code-string">"role"</span>: <span class="ds-code-string">"user"</span>, <span class="ds-code-string">"content"</span>: <span class="ds-code-string">"What does fetch_user return?"</span>}]
)
print(response.choices[0].message.content)
            </div>

            <div style="margin-top:2rem; text-align:right;">
                <button class="ds-btn-primary" onclick="closeDocsModal()">Got it</button>
            </div>
        </div>
    </div>

    <!-- FOOTER -->
    <footer class="ds-footer">
        <div class="ds-container">
            <div class="ds-footer-grid">
                <div class="ds-footer-brand">
                    <h4>Semantic Gateway</h4>
                    <p>SuperCompress neural prompt compression, sub-50ms semantic vector caching, and cost-aware model routing.</p>
                    <p style="margin-top:1rem; color:var(--ds-muted); font-size:0.8rem;">Apache 2.0 Open Source</p>
                </div>
                <div class="ds-footer-col">
                    <h5>Navigation</h5>
                    <ul>
                        <li><a href="#features">Architecture</a></li>
                        <li><a href="#how-it-works">How It Works</a></li>
                        <li><a href="#use-cases">Use Cases</a></li>
                        <li><a href="#benchmarks">Benchmarks</a></li>
                        <li><a href="#agents">Coding Agents (MCP)</a></li>
                        <li><a href="#demo" onclick="switchTab('sandbox')">Interactive Sandbox</a></li>
                        <li><a href="#demo" onclick="switchTab('analytics')">Telemetry Dashboard</a></li>
                    </ul>
                </div>
                <div class="ds-footer-col">
                    <h5>Resources</h5>
                    <ul>
                        <li><a href="javascript:void(0)" onclick="openDocsModal()">API Documentation</a></li>
                        <li><a href="/api/metrics" target="_blank">Raw Metrics API</a></li>
                        <li><a href="/health" target="_blank">Health Check</a></li>
                        <li><a href="https://github.com/anothercodingguy/SemanticLLM" target="_blank">GitHub Repository</a></li>
                    </ul>
                </div>
                <div class="ds-footer-col">
                    <h5>Engines</h5>
                    <ul>
                        <li><a href="#features">SuperCompress Compiler</a></li>
                        <li><a href="#features">384-Dim FastEmbed Vectors</a></li>
                        <li><a href="#features">Groq Llama 3.1 & 3.3</a></li>
                        <li><a href="#features">Ollama Fallback</a></li>
                    </ul>
                </div>
            </div>
        </div>
    </footer>

    <!-- SCRIPT LOGIC -->
    <script>
        // Starfield background particle animation
        (function() {
            const canvas = document.getElementById('hero-canvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            let w = canvas.width = window.innerWidth;
            let h = canvas.height = window.innerHeight;

            window.addEventListener('resize', () => {
                w = canvas.width = window.innerWidth;
                h = canvas.height = window.innerHeight;
            });

            const stars = Array.from({ length: 70 }, () => ({
                x: Math.random() * w,
                y: Math.random() * h,
                r: Math.random() * 1.5 + 0.5,
                alpha: Math.random() * 0.7 + 0.2,
                vx: (Math.random() - 0.5) * 0.15,
                vy: (Math.random() - 0.5) * 0.15
            }));

            function render() {
                ctx.clearRect(0, 0, w, h);
                for (let i = 0; i < stars.length; i++) {
                    for (let j = i + 1; j < stars.length; j++) {
                        const dx = stars[i].x - stars[j].x;
                        const dy = stars[i].y - stars[j].y;
                        const dist = Math.sqrt(dx * dx + dy * dy);
                        if (dist < 120) {
                            ctx.strokeStyle = `rgba(77, 136, 255, ${0.15 * (1 - dist / 120)})`;
                            ctx.lineWidth = 0.6;
                            ctx.beginPath();
                            ctx.moveTo(stars[i].x, stars[i].y);
                            ctx.lineTo(stars[j].x, stars[j].y);
                            ctx.stroke();
                        }
                    }
                }
                stars.forEach(s => {
                    s.x += s.vx; s.y += s.vy;
                    if (s.x < 0) s.x = w; if (s.x > w) s.x = 0;
                    if (s.y < 0) s.y = h; if (s.y > h) s.y = 0;
                    ctx.fillStyle = `rgba(165, 205, 255, ${s.alpha})`;
                    ctx.beginPath();
                    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
                    ctx.fill();
                });
                requestAnimationFrame(render);
            }
            render();
        })();

        let latencyChart = null;
        let currentCompressionMode = 'compiler';

        const PRESETS = {
            support: {
                context: "## Customer Support Ticket History\nUser ID: usr_9281742 | Plan: Enterprise Tier | Region: US-East\n[2026-08-16 09:12:00 INFO] Ticket #8841 created: Billing mismatch on invoice INV-2026-08.\n[2026-08-16 09:12:00 INFO] Ticket #8841 created: Billing mismatch on invoice INV-2026-08.\n[2026-08-16 09:15:22 DEBUG] Automated webhook dispatched to Stripe Billing API.\n[2026-08-16 09:15:22 DEBUG] Automated webhook dispatched to Stripe Billing API.\n\n### Account Overview\nAccount status is active. Payment method ending in 4242 failed due to bank verification hold.\nRefund request of $420.00 approved by billing supervisor on 2026-08-15.\n\n### Unrelated Feature Requests\nUser requested dark mode for the analytics dashboard and support for export to parquet format.",
                query: "What was the supervisor decision regarding the refund request on invoice INV-2026-08?"
            },
            paraphrase: {
                context: "### API Function Specification\ndef fetch_user(user_id: str):\n    # Queries user database\n    row = db.query('SELECT * FROM users WHERE id = %s', user_id)\n    if not row:\n        return None\n    return User(row)",
                query: "What happens if fetch_user cannot find the database row?"
            },
            diff: {
                context: "```diff\ndiff --git a/services/auth.py b/services/auth.py\nindex 8a3f21..b9c412 100644\n--- a/services/auth.py\n+++ b/services/auth.py\n@@ -42,7 +42,7 @@ def verify_jwt_token(token: str) -> Optional[dict]:\n-    except jwt.ExpiredSignatureError:\n+    except jwt.ExpiredSignatureError as err:\n+        logger.warning(f'Token expired: {err}')\n         return None\n```\n[2026-08-18 10:00:00 INFO] Worker process 4421 started\n[2026-08-18 10:00:00 INFO] Worker process 4421 started\n[2026-08-18 10:00:01 DEBUG] Heartbeat signal received from agent runner",
                query: "What exception does verify_jwt_token catch and log?"
            },
            rag: {
                context: "### Document: Architecture Overview\nSemantic Gateway provides query-aware prompt compression and sub-50ms vector caching.\nSemantic Gateway provides query-aware prompt compression and sub-50ms vector caching.\n\n### Document: Pricing Model\nllama-3.1-8b-instant costs $0.05 per 1M input tokens and $0.08 per 1M output tokens.\nllama-3.3-70b-versatile costs $0.59 per 1M input tokens and $0.79 per 1M output tokens.\n\n### Document: Unsupported Features\nLegacy FTP sync is permanently deprecated.",
                query: "What is the input token pricing for llama-3.1-8b-instant?"
            },
            complex: {
                context: "## System Requirements for Distributed Event Pipeline\nHigh-throughput message pipeline processing 100k events/sec.\nComponents must handle network partitions with circuit breakers.\nWorkers should process batches asynchronously with backpressure.",
                query: "Analyze the architecture of a high-concurrency distributed event pipeline. Write Python code demonstrating an asynchronous worker pool with circuit breakers and fallback retry mechanisms."
            }
        };

        function escapeHtml(unsafe) {
            return (unsafe || '').toString()
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        function setCompressionMode(mode) {
            currentCompressionMode = mode;
            document.querySelectorAll('.ds-mode-pill').forEach(el => el.classList.remove('active'));
            const btn = document.getElementById('mode-' + mode);
            if (btn) btn.classList.add('active');
        }

        function loadPreset(key) {
            const p = PRESETS[key];
            if (!p) return;
            const input = document.getElementById('chat-input');
            const qInput = document.getElementById('query-input');
            input.value = p.context || '';
            qInput.value = p.query || '';
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
            document.querySelectorAll('.ds-studio-tab-btn').forEach(el => {
                el.classList.remove('active');
                el.setAttribute('aria-selected', 'false');
            });
            document.querySelectorAll('.ds-tab-pane').forEach(el => el.classList.remove('active'));
            
            const btn = document.getElementById('tabbtn-' + tabId);
            const pane = document.getElementById('tab-' + tabId);
            if (btn) { btn.classList.add('active'); btn.setAttribute('aria-selected', 'true'); }
            if (pane) pane.classList.add('active');

            if (tabId === 'analytics') {
                fetchMetrics();
                setTimeout(() => { if (latencyChart) latencyChart.resize(); }, 50);
            }
        }

        function switchResultTab(tabId) {
            document.querySelectorAll('.ds-res-tab-btn').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.ds-res-pane').forEach(el => el.classList.remove('active'));
            
            const btn = document.getElementById('btn-res-' + tabId);
            const pane = document.getElementById('pane-' + tabId);
            if (btn) btn.classList.add('active');
            if (pane) pane.classList.add('active');
        }

        function switchTermTab(tabId) {
            document.querySelectorAll('.ds-term-tab').forEach(el => el.classList.remove('active'));
            document.getElementById('ttab-' + tabId).classList.add('active');

            document.getElementById('term-pane-quick').style.display = tabId === 'quick' ? 'block' : 'none';
            document.getElementById('term-pane-compress').style.display = tabId === 'compress' ? 'block' : 'none';
            document.getElementById('term-pane-sdk').style.display = tabId === 'sdk' ? 'block' : 'none';
            document.getElementById('term-pane-mcp').style.display = tabId === 'mcp' ? 'block' : 'none';
        }

        function copyTermCode() {
            let text = '';
            if (document.getElementById('term-pane-quick').style.display !== 'none') {
                text = 'uvicorn main:app --host 0.0.0.0 --port 8000 --reload';
            } else if (document.getElementById('term-pane-compress').style.display !== 'none') {
                text = 'curl -X POST http://localhost:8000/v1/compress -H "Content-Type: application/json" -d \'{"context": "Huge log dump...", "query": "What failed in deploy?", "mode": "compiler"}\'';
            } else if (document.getElementById('term-pane-sdk').style.display !== 'none') {
                text = 'from services.compression import compress_for_turn\n\nres = compress_for_turn(context=chat_history, user_query="What failed?", mode="compiler")\nprint(res)';
            } else {
                text = 'npm install -g supercompress-proxy && npx supercompress setup --proxy http://localhost:8000';
            }
            copyText(text);
            const copyLabel = document.getElementById('copy-text');
            copyLabel.textContent = 'Copied!';
            setTimeout(() => { copyLabel.textContent = 'Copy'; }, 2000);
        }

        function copyText(txt) { navigator.clipboard.writeText(txt); }
        function openDocsModal() { document.getElementById('docs-modal').classList.add('open'); }
        function closeDocsModal() { document.getElementById('docs-modal').classList.remove('open'); }

        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const qInput = document.getElementById('query-input');
            const contextText = input.value.trim();
            const queryText = qInput.value.trim();
            const errBox = document.getElementById('error-alert');
            errBox.style.display = 'none';

            if (!contextText) {
                errBox.textContent = 'Please enter context before submitting.';
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
                // Combine context and query for LLM chat completion
                const fullPrompt = queryText ? `${contextText}\n\nUser Question:\n${queryText}` : contextText;
                
                const res = await fetch('/v1/chat/completions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        messages: [{ role: 'user', content: fullPrompt }]
                    })
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || `Server responded with status ${res.status}`);
                }

                const data = await res.json();
                document.getElementById('result-container').style.display = 'block';

                // 1. Output pane
                const replyText = data.choices && data.choices[0] && data.choices[0].message ? data.choices[0].message.content : 'No response text received.';
                document.getElementById('res-text').textContent = replyText;

                // 2. Context Compression pane
                const comp = data.compression || {};
                const compPct = comp.compression_percent || comp.tokens_saved_pct || 0.0;
                document.getElementById('res-tab-comp-pct').textContent = compPct > 0 ? `${compPct.toFixed(1)}% cut` : '0%';
                document.getElementById('res-comp-summary').textContent = compPct > 0 
                    ? `Context compressed by ${compPct.toFixed(1)}% (${comp.tokens_saved} tokens eliminated) · Risk: ${comp.compression_risk || 'low'}`
                    : 'Context is already concise; sent directly without loss.';
                
                document.getElementById('diff-orig-tokens').textContent = comp.original_tokens || 0;
                document.getElementById('diff-orig-text').textContent = comp.original_text || contextText;
                document.getElementById('diff-opt-tokens').textContent = comp.optimized_tokens || comp.kept_tokens || 0;
                document.getElementById('diff-saved-tokens').textContent = comp.tokens_saved || 0;
                document.getElementById('diff-opt-text').textContent = comp.optimized_text || comp.compressed_text || contextText;

                const notesUl = document.getElementById('res-savings-notes');
                notesUl.innerHTML = '';
                (comp.savings_notes || []).forEach(note => {
                    const li = document.createElement('li');
                    li.textContent = note;
                    notesUl.appendChild(li);
                });

                // 3. Kept vs Dropped Blocks pane
                const keptList = document.getElementById('kept-blocks-list');
                const droppedList = document.getElementById('dropped-blocks-list');
                keptList.innerHTML = '';
                droppedList.innerHTML = '';

                (comp.kept_blocks || []).forEach(b => {
                    const card = document.createElement('div');
                    card.className = 'ds-block-card kept';
                    card.innerHTML = `<div class="ds-block-head"><span>${escapeHtml(b.heading || 'Evidence Block')}</span><span style="font-family:var(--font-mono); font-size:11px; color:var(--ds-green);">${b.tokens || 0} tokens</span></div><div class="ds-block-reason">${escapeHtml(b.reason || 'Critical answer evidence')}</div>`;
                    keptList.appendChild(card);
                });
                if (!(comp.kept_blocks && comp.kept_blocks.length)) {
                    keptList.innerHTML = '<div style="color:var(--ds-muted); font-size:12px;">All essential context preserved.</div>';
                }

                (comp.dropped_blocks || []).forEach(b => {
                    const card = document.createElement('div');
                    card.className = 'ds-block-card dropped';
                    card.innerHTML = `<div class="ds-block-head"><span>${escapeHtml(b.heading || 'Context Block')}</span><span style="font-family:var(--font-mono); font-size:11px; color:var(--ds-red);">${b.tokens || 0} tokens</span></div><div class="ds-block-reason">${escapeHtml(b.reason || 'Irrelevant noise')}</div>`;
                    droppedList.appendChild(card);
                });
                if (!(comp.dropped_blocks && comp.dropped_blocks.length)) {
                    droppedList.innerHTML = '<div style="color:var(--ds-muted); font-size:12px;">No large blocks dropped.</div>';
                }

                // 4. Diagnostics pane
                const cache = data.cache || {};
                const routing = data.routing || {};
                const latency = data.latency || {};
                const cost = data.cost || {};

                document.getElementById('diag-cache').innerHTML = cache.hit
                    ? `<span style="color:var(--ds-green); font-weight:bold;">HIT (${cache.similarity}% match)</span>`
                    : `<span style="color:var(--ds-amber); font-weight:bold;">MISS</span> (Best: ${cache.similarity || 0}%, Thresh: ${cache.threshold || 82}%)`;

                document.getElementById('diag-model').textContent = `${routing.model || data.model} [${routing.complexity || 'SIMPLE'}]`;
                document.getElementById('diag-latency').textContent = `${latency.total_ms || 0}ms (Cache: ${latency.cache_lookup_ms || 0}ms, Upstream: ${latency.upstream_inference_ms || 0}ms)`;
                document.getElementById('diag-cost').innerHTML = `<span style="color:var(--ds-green); font-weight:bold;">Saved $${(cost.cost_saved || 0).toFixed(5)}</span> (Spent $${(cost.actual_spent || 0).toFixed(5)})`;

                // 5. Sustainability pane
                const sustain = comp.sustainability || {};
                const co2Grams = ((sustain.co2_kg_avoided || 0) * 1000).toFixed(4);
                document.getElementById('sustain-co2').textContent = `${co2Grams} g`;
                document.getElementById('sustain-watt').textContent = `${(sustain.watt_hours_saved || 0).toFixed(4)} Wh`;
                document.getElementById('sustain-gpu').textContent = `${(sustain.gpu_seconds_avoided || 0).toFixed(3)} s`;

                // Update Telemetry Metrics
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
                            <td style="color:var(--ds-muted); font-size:0.8rem; font-family:var(--font-mono);">${escapeHtml(timeStr)}</td>
                            <td style="max-width:240px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${escapeHtml(q.prompt)}">${escapeHtml(q.prompt)}</td>
                            <td><span class="ds-badge ${routeBadge}">${escapeHtml(q.complexity || 'SIMPLE')}</span></td>
                            <td style="font-family:var(--font-mono); font-size:0.8rem; color:var(--ds-secondary);">${escapeHtml(q.model_routed)}</td>
                            <td><span class="ds-status-pill ${cacheDot}">● ${cacheLabel}</span></td>
                            <td style="font-family:var(--font-mono); font-size:0.8rem;">${q.original_tokens || 0} → ${q.optimized_tokens || 0}</td>
                            <td style="font-weight:600; font-family:var(--font-mono);">${Math.round(q.latency_ms)}ms</td>
                            <td style="color:var(--ds-green); font-weight:600; font-family:var(--font-mono);">$${(q.cost_saved || 0).toFixed(5)}</td>
                        `;
                        tbody.appendChild(tr);
                    });

                    updateChart(data.queries);
                } else {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--ds-muted); padding:2.5rem;">No queries recorded yet. Send a request in the Sandbox!</td></tr>';
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

            const canvas = document.getElementById('latencyChart');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            if (latencyChart) latencyChart.destroy();
            
            latencyChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels,
                    datasets: [
                        {
                            label: 'FastEmbed Vector Cache Hit (ms)',
                            data: hitData,
                            borderColor: '#4d88ff',
                            backgroundColor: '#4d88ff',
                            pointRadius: 5,
                            pointHoverRadius: 7,
                            borderWidth: 2,
                            tension: 0.15,
                            spanGaps: true
                        },
                        {
                            label: 'Direct Upstream Inference Miss (ms)',
                            data: missData,
                            borderColor: '#febc2e',
                            backgroundColor: '#febc2e',
                            pointRadius: 5,
                            pointHoverRadius: 7,
                            borderWidth: 2,
                            tension: 0.15,
                            spanGaps: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top', labels: { boxWidth: 12, color: '#9aa0b0', font: { family: 'DM Sans', size: 12 } } },
                        tooltip: {
                            backgroundColor: '#16181f',
                            titleColor: '#ffffff',
                            bodyColor: '#f0f2f7',
                            borderColor: 'rgba(255,255,255,0.1)',
                            borderWidth: 1
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Latency (ms)', color: '#818798' },
                            ticks: { color: '#818798' },
                            grid: { color: 'rgba(255,255,255,0.05)' }
                        },
                        x: {
                            ticks: { color: '#818798' },
                            grid: { color: 'rgba(255,255,255,0.03)' }
                        }
                    }
                }
            });
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
