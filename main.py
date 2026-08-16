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
    Serves the production-ready Semantic LLM Gateway developer dashboard in authentic DeepSeek Harness aesthetic.
    """
    html_content = r"""<!DOCTYPE html>
<html lang="en-US" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Semantic Gateway Developer Preview: Everything is optimized. Every token is cached.</title>
    <meta name="description" content="Production LLM gateway with sub-50ms semantic vector caching, prompt compression, and intelligent complexity routing. Cut Your LLM API Costs by 65%.">
    <!-- Google Fonts: DM Sans, Inter, JetBrains Mono -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
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
            --ds-border-hover: rgba(255, 255, 255, 0.16);
            --ds-brand: #4d88ff;
            --ds-brand-light: #679efe;
            --ds-brand-hover: #3b74f0;
            --ds-brand-glow: rgba(77, 136, 255, 0.3);
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

        /* Ambient Glow Background */
        .ambient-mesh {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
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

        .orb-1 {
            top: -150px;
            left: 20%;
            width: 650px;
            height: 650px;
            background: radial-gradient(circle, #2d5f9e 0%, #1a3870 55%, transparent 70%);
        }

        .orb-2 {
            top: 400px;
            right: 5%;
            width: 550px;
            height: 550px;
            background: radial-gradient(circle, #1e40af 0%, #0f275a 60%, transparent 70%);
            opacity: 0.18;
        }

        .orb-3 {
            bottom: 0px;
            left: 50%;
            transform: translateX(-50%);
            width: 900px;
            height: 450px;
            background: radial-gradient(ellipse at center, #2d5f9e 0%, #1a3870 45%, transparent 70%);
            opacity: 0.22;
        }

        #hero-canvas {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            opacity: 0.65;
            mask-image: linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,0.85) 60%, transparent 100%);
            -webkit-mask-image: linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,0.85) 60%, transparent 100%);
        }

        /* ═══════════════════════════════════════════════════════════════════
           HEADER & NAVIGATION (DeepSeek Harness Style)
           ═══════════════════════════════════════════════════════════════════ */
        .ds-header-wrapper {
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(11, 12, 15, 0.75);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border-bottom: 1px solid var(--ds-border-default);
            transition: all 0.25s ease;
        }

        .ds-header-bar {
            max-width: 1280px;
            margin: 0 auto;
            padding: 0.85rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .ds-logo-group {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            text-decoration: none;
            color: #ffffff;
        }

        .ds-logo-mark {
            width: 28px;
            height: 28px;
            color: var(--ds-brand);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .ds-logo-text {
            font-size: 1.15rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        /* Signature DeepSeek Gradient Pill Tag */
        .ds-pill-tag {
            display: inline-flex;
            align-items: center;
            padding: 1px;
            border-radius: 8px;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.6) 0%, rgba(255, 255, 255, 0.08) 35%, rgba(255, 255, 255, 0.04) 65%, rgba(255, 255, 255, 0.4) 100%);
            box-shadow: 0 0 16px rgba(255, 255, 255, 0.06), 0 0 32px rgba(255, 255, 255, 0.02);
        }

        .ds-pill-tag-inner {
            padding: 3px 8px;
            border-radius: 7px;
            font-family: var(--font-mono);
            font-size: 11px;
            font-weight: 600;
            line-height: 1;
            background: rgba(0, 0, 0, 0.4);
            color: rgba(255, 255, 255, 0.95);
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        .ds-nav-links {
            display: flex;
            align-items: center;
            gap: 1.75rem;
        }

        .ds-nav-link {
            text-decoration: none;
            color: var(--ds-description);
            font-size: 0.88rem;
            font-weight: 500;
            transition: color 0.15s ease;
        }
        .ds-nav-link:hover { color: #ffffff; }

        .ds-header-actions {
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }

        .ds-toggle-pill {
            display: inline-flex;
            align-items: center;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-pill);
            padding: 2px;
            gap: 2px;
        }

        .ds-toggle-btn {
            background: transparent;
            border: none;
            color: var(--ds-description);
            font-family: var(--font-mono);
            font-size: 11px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: var(--radius-pill);
            cursor: pointer;
            transition: all 0.15s ease;
        }
        .ds-toggle-btn.is-active {
            background: rgba(255, 255, 255, 0.12);
            color: #ffffff;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
        }

        .ds-btn-header {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-sm);
            color: var(--ds-primary);
            font-size: 0.85rem;
            font-weight: 500;
            padding: 0.45rem 0.85rem;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .ds-btn-header:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: var(--ds-border-hover);
            color: #ffffff;
        }

        /* ═══════════════════════════════════════════════════════════════════
           BUTTONS & PILLS (DeepSeek Harness Primary & Secondary)
           ═══════════════════════════════════════════════════════════════════ */
        .ds-btn-primary {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            background: linear-gradient(180deg, #3b82f6 0%, #1d4ed8 100%);
            color: #ffffff;
            text-decoration: none;
            font-size: 0.92rem;
            font-weight: 600;
            padding: 0.75rem 1.5rem;
            border-radius: var(--radius-sm);
            border: 1px solid rgba(255, 255, 255, 0.18);
            box-shadow: 0 0 20px rgba(37, 99, 235, 0.4), 0 2px 6px rgba(0, 0, 0, 0.3);
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            cursor: pointer;
        }
        .ds-btn-primary:hover {
            background: linear-gradient(180deg, #60a5fa 0%, #2563eb 100%);
            box-shadow: 0 0 28px rgba(59, 130, 246, 0.55), 0 4px 12px rgba(0, 0, 0, 0.4);
            transform: translateY(-1px);
        }

        .ds-btn-secondary {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            background: rgba(255, 255, 255, 0.04);
            color: var(--ds-primary);
            text-decoration: none;
            font-size: 0.92rem;
            font-weight: 500;
            padding: 0.75rem 1.35rem;
            border-radius: var(--radius-sm);
            border: 1px solid var(--ds-border-default);
            backdrop-filter: blur(10px);
            transition: all 0.2s ease;
            cursor: pointer;
        }
        .ds-btn-secondary:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--ds-border-hover);
            color: #ffffff;
            transform: translateY(-1px);
        }

        /* ═══════════════════════════════════════════════════════════════════
           HERO SECTION (60/40 Split + DeepSeek Typography)
           ═══════════════════════════════════════════════════════════════════ */
        .ds-container {
            max-width: 1280px;
            margin: 0 auto;
            padding: 0 1.5rem;
            position: relative;
            z-index: 10;
        }

        .ds-hero-section {
            padding: 6.5rem 0 5rem;
            min-height: calc(85vh - 70px);
            display: flex;
            align-items: center;
        }

        .ds-hero-grid {
            display: grid;
            grid-template-columns: 58fr 42fr;
            gap: 3.5rem;
            align-items: center;
            width: 100%;
        }

        .ds-hero-content {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 1.5rem;
        }

        .ds-hero-badge {
            display: inline-flex;
            align-items: center;
            padding: 1px;
            border-radius: 8px;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.42) 0%, rgba(255, 255, 255, 0.08) 35%, rgba(255, 255, 255, 0.04) 65%, rgba(255, 255, 255, 0.28) 100%);
            box-shadow: 0 0 16px rgba(255, 255, 255, 0.08), 0 0 32px rgba(255, 255, 255, 0.04);
        }

        .ds-hero-badge span {
            padding: 5px 12px;
            border-radius: 7px;
            background: rgba(0, 0, 0, 0.35);
            font-family: var(--font-mono);
            font-size: 12px;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.95);
            line-height: 1;
            letter-spacing: 0.04em;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .ds-status-dot-live {
            width: 7px;
            height: 7px;
            background: var(--ds-green);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--ds-green);
            animation: pulse-live 2s infinite;
        }

        @keyframes pulse-live {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.85); }
        }

        .ds-text-hero {
            font-size: clamp(2.8rem, 5.5vw, 4.4rem);
            font-weight: 700;
            letter-spacing: -0.04em;
            line-height: 1.08;
            color: #ffffff;
        }

        .ds-brand-gradient {
            background: linear-gradient(135deg, #ffffff 0%, #9ec3ff 50%, #4d88ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .ds-text-body {
            font-size: 1.1rem;
            line-height: 1.65;
            color: var(--ds-description);
            max-width: 620px;
        }

        .ds-hero-cta-group {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.85rem;
            margin-top: 0.5rem;
        }

        /* ═══════════════════════════════════════════════════════════════════
           TERMINAL QUICKSTART CARD (DeepSeek Harness Tabbed Box)
           ═══════════════════════════════════════════════════════════════════ */
        .ds-terminal-container {
            display: flex;
            flex-direction: column;
            width: 100%;
        }

        .ds-term-tabs {
            display: flex;
            gap: 4px;
            margin-left: 8px;
            z-index: 2;
        }

        .ds-term-tab {
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 500;
            color: var(--ds-description);
            background: transparent;
            border: 1px solid transparent;
            border-bottom: none;
            border-radius: 8px 8px 0 0;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .ds-term-tab.active {
            color: #ffffff;
            background: rgba(18, 20, 26, 0.85);
            backdrop-filter: blur(16px);
            border-color: var(--ds-border-default);
        }

        .ds-term-box {
            background: rgba(18, 20, 26, 0.85);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-card), var(--shadow-glow);
            overflow: hidden;
            position: relative;
        }

        .ds-term-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.75rem 1.25rem;
            border-bottom: 1px solid var(--ds-border-default);
            background: rgba(12, 13, 17, 0.5);
        }

        .ds-traffic-lights {
            display: flex;
            align-items: center;
            gap: 7px;
        }

        .ds-dot {
            width: 11px;
            height: 11px;
            border-radius: 50%;
        }
        .ds-dot.red { background: var(--ds-red); }
        .ds-dot.yellow { background: var(--ds-amber); }
        .ds-dot.green { background: var(--ds-green); }

        .ds-term-title {
            font-family: var(--font-mono);
            font-size: 12px;
            color: var(--ds-muted);
        }

        .ds-copy-btn {
            background: transparent;
            border: none;
            color: var(--ds-description);
            font-size: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 5px;
            transition: color 0.15s ease;
        }
        .ds-copy-btn:hover { color: #ffffff; }

        .ds-term-body {
            padding: 1.5rem;
            font-family: var(--font-mono);
            font-size: 13.5px;
            line-height: 1.8;
            color: var(--ds-primary);
            overflow-x: auto;
            max-height: 280px;
        }

        .ds-prompt-sym { color: var(--ds-brand); font-weight: 700; user-select: none; }
        .ds-code-comment { color: var(--ds-muted); }
        .ds-code-keyword { color: #f472b6; }
        .ds-code-string { color: #93c5fd; }
        .ds-code-num { color: #fcd34d; }

        /* ═══════════════════════════════════════════════════════════════════
           PILLAR & ARCHITECTURE CARDS (Core Capabilities)
           ═══════════════════════════════════════════════════════════════════ */
        .ds-section {
            padding: 6rem 0;
            position: relative;
        }

        .ds-section-header {
            max-width: 840px;
            margin: 0 auto 3.5rem;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 1.25rem;
        }

        .ds-text-heading1 {
            font-size: clamp(2rem, 4vw, 2.9rem);
            font-weight: 700;
            letter-spacing: -0.03em;
            line-height: 1.18;
            color: #ffffff;
        }

        .ds-grid-3 {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
        }

        .ds-card {
            background: var(--ds-surface-card);
            border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-md);
            padding: 2.25rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
            overflow: hidden;
        }
        .ds-card:hover {
            border-color: var(--ds-border-hover);
            transform: translateY(-3px);
            box-shadow: 0 12px 36px rgba(0, 0, 0, 0.4), 0 0 20px rgba(77, 136, 255, 0.1);
        }

        .ds-card-icon {
            color: var(--ds-primary);
            opacity: 0.85;
            margin-bottom: 1.5rem;
        }

        .ds-card-title {
            font-size: 1.3rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            color: #ffffff;
            margin-bottom: 0.75rem;
        }

        .ds-card-desc {
            font-size: 0.92rem;
            color: var(--ds-description);
            line-height: 1.65;
        }

        /* ═══════════════════════════════════════════════════════════════════
           INTERACTIVE SPLIT / TRAJECTORY SHOWCASE
           ═══════════════════════════════════════════════════════════════════ */
        .ds-split-grid {
            display: grid;
            grid-template-columns: 44fr 56fr;
            gap: 3.5rem;
            align-items: start;
            margin-top: 2rem;
        }

        .ds-feature-nav {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .ds-feature-item {
            padding: 1.5rem 1.75rem;
            border-radius: var(--radius-md);
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--ds-border-subtle);
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .ds-feature-item.active {
            background: rgba(77, 136, 255, 0.06);
            border-color: rgba(77, 136, 255, 0.35);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }
        .ds-feature-item:hover:not(.active) {
            background: rgba(255, 255, 255, 0.04);
            border-color: var(--ds-border-default);
        }

        .ds-feature-head {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.5rem;
        }

        .ds-feature-head h3 {
            font-size: 1.2rem;
            font-weight: 600;
            color: #ffffff;
        }

        .ds-feature-item p {
            font-size: 0.9rem;
            color: var(--ds-description);
            line-height: 1.6;
        }

        /* Interactive Showcase Preview Frame */
        .ds-preview-frame {
            background: var(--ds-surface-card);
            border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-lg);
            padding: 1.75rem;
            box-shadow: var(--shadow-card);
            min-height: 380px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        /* ═══════════════════════════════════════════════════════════════════
           DEVELOPER SANDBOX & TELEMETRY STUDIO (DeepSeek Dark Glass)
           ═══════════════════════════════════════════════════════════════════ */
        .ds-studio-tabs {
            display: flex;
            justify-content: center;
            gap: 1.5rem;
            margin-bottom: 2.5rem;
            border-bottom: 1px solid var(--ds-border-default);
        }

        .ds-studio-tab-btn {
            padding: 0.85rem 1.75rem;
            font-size: 1rem;
            font-weight: 600;
            color: var(--ds-description);
            background: transparent;
            border: none;
            border-bottom: 2px solid transparent;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-bottom: -1px;
        }
        .ds-studio-tab-btn:hover { color: #ffffff; }
        .ds-studio-tab-btn.active {
            color: #ffffff;
            border-bottom-color: var(--ds-brand);
            text-shadow: 0 0 12px var(--ds-brand-glow);
        }

        .ds-tab-pane { display: none; }
        .ds-tab-pane.active { display: block; animation: ds-fadeIn 0.25s ease-in-out; }
        @keyframes ds-fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

        .ds-sandbox-grid {
            display: grid;
            grid-template-columns: 1.3fr 0.7fr;
            gap: 2rem;
            align-items: start;
        }

        .ds-glass-panel {
            background: var(--ds-surface-card);
            border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-md);
            padding: 1.75rem;
            box-shadow: var(--shadow-card);
        }

        .ds-panel-eyebrow {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--ds-muted);
            margin-bottom: 1rem;
        }

        .ds-chip-row {
            display: flex;
            gap: 0.5rem;
            overflow-x: auto;
            padding-bottom: 0.75rem;
            margin-bottom: 1rem;
        }

        .ds-chip {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-pill);
            padding: 0.35rem 0.85rem;
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--ds-description);
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.15s ease;
        }
        .ds-chip:hover {
            background: rgba(77, 136, 255, 0.1);
            border-color: rgba(77, 136, 255, 0.4);
            color: #ffffff;
        }

        .ds-textarea {
            width: 100%;
            height: 140px;
            padding: 1rem;
            background: rgba(11, 12, 16, 0.8);
            border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-sm);
            font-family: var(--font-mono);
            font-size: 13.5px;
            color: #ffffff;
            line-height: 1.6;
            resize: vertical;
            outline: none;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .ds-textarea:focus {
            border-color: var(--ds-brand);
            box-shadow: 0 0 0 3px rgba(77, 136, 255, 0.15);
        }

        .ds-prompt-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 1rem;
        }

        .ds-token-badge {
            font-family: var(--font-mono);
            font-size: 12px;
            color: var(--ds-description);
        }

        /* Result Viewer */
        .ds-result-section {
            margin-top: 1.75rem;
            border-top: 1px solid var(--ds-border-default);
            padding-top: 1.5rem;
        }

        .ds-res-tabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.25rem;
        }

        .ds-res-tab-btn {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--ds-border-default);
            padding: 0.4rem 0.95rem;
            border-radius: var(--radius-sm);
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--ds-description);
            cursor: pointer;
            transition: all 0.15s ease;
        }
        .ds-res-tab-btn.active {
            background: var(--ds-brand);
            color: #ffffff;
            border-color: var(--ds-brand);
            box-shadow: 0 0 14px rgba(77, 136, 255, 0.35);
        }

        .ds-res-pane {
            display: none;
            background: rgba(11, 12, 16, 0.6);
            border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-sm);
            padding: 1.25rem;
            font-size: 0.9rem;
            line-height: 1.65;
        }
        .ds-res-pane.active { display: block; }

        .ds-diff-box {
            font-family: var(--font-mono);
            font-size: 12.5px;
            line-height: 1.65;
            max-height: 250px;
            overflow-y: auto;
        }
        .ds-diff-orig {
            color: #fca5a5;
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.2);
            padding: 0.6rem;
            border-radius: 6px;
            margin-bottom: 0.6rem;
        }
        .ds-diff-opt {
            color: #86efac;
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.2);
            padding: 0.6rem;
            border-radius: 6px;
        }

        .ds-diag-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
        }
        .ds-diag-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-sm);
            padding: 0.85rem 1rem;
        }
        .ds-diag-lbl { font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--ds-muted); font-weight: 700; }
        .ds-diag-val { font-size: 0.95rem; font-weight: 600; color: #ffffff; margin-top: 0.25rem; }

        /* Telemetry Right Panel */
        .ds-stat-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 0;
            border-bottom: 1px solid var(--ds-border-subtle);
            font-size: 0.9rem;
        }
        .ds-stat-row:last-child { border-bottom: none; }
        .ds-stat-name { color: var(--ds-description); font-weight: 500; }
        .ds-stat-val { font-weight: 600; color: #ffffff; text-align: right; }
        .ds-stat-val.brand { color: var(--ds-brand); }
        .ds-stat-val.green { color: var(--ds-green); }

        /* Impact Dashboard Grid */
        .ds-dash-summary-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.25rem;
            margin-bottom: 2rem;
        }
        .ds-summary-card {
            background: var(--ds-surface-card);
            border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-md);
            padding: 1.5rem;
            box-shadow: var(--shadow-subtle);
        }
        .ds-summary-lbl { font-size: 11px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.06em; color: var(--ds-muted); }
        .ds-summary-val { font-size: 1.75rem; font-weight: 700; color: #ffffff; margin-top: 0.5rem; }

        .ds-chart-box {
            background: var(--ds-surface-card);
            border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-md);
            padding: 2rem;
            margin-bottom: 2rem;
            height: 350px;
        }

        .ds-table-wrap {
            background: var(--ds-surface-card);
            border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-md);
            overflow-x: auto;
        }
        table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
        th, td { text-align: left; padding: 1.1rem 1.25rem; border-bottom: 1px solid var(--ds-border-subtle); }
        th { color: var(--ds-muted); font-weight: 700; text-transform: uppercase; font-size: 11px; letter-spacing: 0.06em; background: rgba(0, 0, 0, 0.25); }
        tr:last-child td { border-bottom: none; }
        tr:hover td { background: rgba(255, 255, 255, 0.02); }

        .ds-badge {
            padding: 0.25rem 0.6rem;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
        }
        .ds-badge.simple { background: rgba(77, 136, 255, 0.15); color: var(--ds-brand-light); border: 1px solid rgba(77, 136, 255, 0.3); }
        .ds-badge.complex { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }

        .ds-status-pill {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 12px;
            font-weight: 600;
        }
        .ds-status-pill.hit { color: var(--ds-green); }
        .ds-status-pill.miss { color: var(--ds-amber); }

        /* Modal */
        .ds-modal-backdrop {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.75);
            backdrop-filter: blur(8px);
            z-index: 200;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .ds-modal-backdrop.open { display: flex; }
        .ds-modal-card {
            background: var(--ds-surface-1);
            border: 1px solid var(--ds-border-default);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-card), var(--shadow-glow);
            max-width: 680px;
            width: 100%;
            max-height: 85vh;
            overflow-y: auto;
            padding: 2.25rem;
        }
        .ds-modal-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }
        .ds-modal-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: var(--ds-muted);
        }

        /* ═══════════════════════════════════════════════════════════════════
           FOOTER (DeepSeek Dark Footer)
           ═══════════════════════════════════════════════════════════════════ */
        .ds-footer {
            background: #090a0d;
            border-top: 1px solid var(--ds-border-default);
            padding: 5rem 0 4rem;
            color: var(--ds-description);
            position: relative;
            z-index: 10;
        }

        .ds-footer-grid {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1fr;
            gap: 3.5rem;
        }

        .ds-footer-brand h4 { font-size: 1.15rem; font-weight: 700; margin-bottom: 1rem; color: #ffffff; }
        .ds-footer-brand p { font-size: 0.88rem; color: var(--ds-description); line-height: 1.7; max-width: 320px; }

        .ds-footer-col h5 { font-size: 0.85rem; color: #ffffff; margin-bottom: 1.25rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; }
        .ds-footer-col ul { list-style: none; }
        .ds-footer-col li { margin-bottom: 0.75rem; }
        .ds-footer-col a { color: var(--ds-description); text-decoration: none; font-size: 0.88rem; transition: color 0.15s ease; }
        .ds-footer-col a:hover { color: #ffffff; }

        /* Responsive */
        @media (max-width: 1024px) {
            .ds-hero-grid, .ds-split-grid, .ds-sandbox-grid { grid-template-columns: 1fr; gap: 2.5rem; }
            .ds-grid-3 { grid-template-columns: 1fr; }
            .ds-dash-summary-grid { grid-template-columns: repeat(2, 1fr); }
            .ds-footer-grid { grid-template-columns: 1fr 1fr; gap: 2.5rem; }
        }

        @media (max-width: 768px) {
            .ds-nav-links { display: none; }
            .ds-dash-summary-grid { grid-template-columns: 1fr; }
            .ds-footer-grid { grid-template-columns: 1fr; }
            .ds-diag-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>

    <!-- Ambient Mesh & Canvas Particles -->
    <div class="ambient-mesh">
        <div class="ambient-orb orb-1"></div>
        <div class="ambient-orb orb-2"></div>
        <div class="ambient-orb orb-3"></div>
        <canvas id="hero-canvas"></canvas>
    </div>

    <!-- HEADER / NAVIGATION -->
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
                    <span>Semantic</span>
                    <span class="ds-pill-tag"><span class="ds-pill-tag-inner">Gateway</span></span>
                </div>
            </a>

            <nav class="ds-nav-links" aria-label="Main Navigation">
                <a href="#features" class="ds-nav-link">Architecture</a>
                <a href="#demo" class="ds-nav-link">Sandbox</a>
                <a href="#demo" class="ds-nav-link">Telemetry</a>
                <a href="#quickstart" class="ds-nav-link">Quickstart</a>
            </nav>

            <div class="ds-header-actions">
                <div class="ds-toggle-pill">
                    <button type="button" class="ds-toggle-btn is-active">Live Gateway</button>
                    <button type="button" class="ds-toggle-btn" onclick="openDocsModal()">Docs</button>
                </div>
                <a href="https://github.com/anothercodingguy/SemanticLLM" target="_blank" rel="noopener noreferrer" class="ds-btn-header" aria-label="GitHub Repository">
                    <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>
                </a>
            </div>
        </div>
    </header>

    <!-- HERO SECTION -->
    <main>
        <section class="ds-hero-section">
            <div class="ds-container">
                <div class="ds-hero-grid">
                    <!-- Left: Hero Copy -->
                    <div class="ds-hero-content">
                        <div class="ds-hero-badge">
                            <span><span class="ds-status-dot-live"></span> Developer Preview · Groq Llama 3.1 & 3.3 Connected</span>
                        </div>

                        <h1 class="ds-text-hero">
                            Everything is optimized.<br/>
                            <span class="ds-brand-gradient">Every token is cached.</span>
                        </h1>

                        <p class="ds-text-body">
                            DeepSeek-class speed and token economics for agent harnesses worldwide. Semantic Gateway intercepts multi-turn prompts before inference, serves semantic paraphrases from cache in sub-50ms, and routes simple vs. complex queries automatically.
                        </p>

                        <div class="ds-hero-cta-group">
                            <a href="#demo" class="ds-btn-primary">
                                Try Interactive Sandbox
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                            </a>
                            <button onclick="openDocsModal()" class="ds-btn-secondary">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
                                Integration Docs
                            </button>
                            <a href="https://github.com/anothercodingguy/SemanticLLM" target="_blank" rel="noopener noreferrer" class="ds-btn-secondary">
                                GitHub
                            </a>
                        </div>
                    </div>

                    <!-- Right: Tabbed Terminal Box -->
                    <div class="ds-terminal-container" id="quickstart">
                        <div class="ds-term-tabs">
                            <button class="ds-term-tab active" id="ttab-quick" onclick="switchTermTab('quick')">Quick start</button>
                            <button class="ds-term-tab" id="ttab-sdk" onclick="switchTermTab('sdk')">OpenAI SDK</button>
                            <button class="ds-term-tab" id="ttab-curl" onclick="switchTermTab('curl')">cURL</button>
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
                                    <div class="ds-code-comment"># Start the Semantic Gateway with auto-reload</div>
                                    <div><span class="ds-prompt-sym">$ </span>uvicorn main:app --host 0.0.0.0 --port 8000 --reload</div>
                                    <br/>
                                    <div style="color:var(--ds-green);">✓ Initialized Qdrant Vector Cache (384-dim FastEmbed)</div>
                                    <div style="color:var(--ds-green);">✓ Groq Llama 3.1 & 3.3 Router Connected</div>
                                    <div style="color:var(--ds-muted);">Listening on http://127.0.0.1:8000/v1/chat/completions ▋</div>
                                </div>

                                <div id="term-pane-sdk" style="display:none;">
                                    <div class="ds-code-comment"># Python OpenAI Drop-In Configuration</div>
                                    <div><span class="ds-code-keyword">from</span> openai <span class="ds-code-keyword">import</span> OpenAI</div>
                                    <br/>
                                    <div>client = OpenAI(base_url=<span class="ds-code-string">"http://localhost:8000/v1"</span>, api_key=<span class="ds-code-string">"not-required"</span>)</div>
                                    <div>res = client.chat.completions.create(model=<span class="ds-code-string">"llama-3.1-8b-instant"</span>, messages=[{<span class="ds-code-string">"role"</span>: <span class="ds-code-string">"user"</span>, <span class="ds-code-string">"content"</span>: <span class="ds-code-string">"Hello!"</span>}])</div>
                                    <div>print(res.choices[0].message.content)</div>
                                </div>

                                <div id="term-pane-curl" style="display:none;">
                                    <div class="ds-code-comment"># Direct HTTP API Completion</div>
                                    <div>curl -X POST http://localhost:8000/v1/chat/completions \</div>
                                    <div>  -H <span class="ds-code-string">"Content-Type: application/json"</span> \</div>
                                    <div>  -d <span class="ds-code-string">'{"messages":[{"role":"user","content":"What is semantic caching?"}]}'</span></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- ARCHITECTURE PILLARS ("Agent = Model + Gateway") -->
        <section class="ds-section" id="features">
            <div class="ds-container">
                <div class="ds-section-header">
                    <span class="ds-hero-badge">
                        <span>Agent = Model + Gateway</span>
                    </span>
                    <h2 class="ds-text-heading1">
                        Gateway keeps agents fast, cost-effective, and resilient
                    </h2>
                    <p class="ds-text-body">
                        The model is the soul of an agent. Semantic Gateway intercepts the raw context, eliminates repetitive boilerplate, and routes requests to the optimal compute tier.
                    </p>
                </div>

                <div class="ds-grid-3">
                    <!-- Pillar 1 -->
                    <div class="ds-card">
                        <div class="ds-card-icon">
                            <svg width="64" height="64" viewBox="0 0 72 72" fill="none">
                                <circle cx="36" cy="36" r="4" stroke="currentColor" stroke-width="1.2"></circle>
                                <circle cx="36" cy="36" r="1.5" fill="currentColor"></circle>
                                <ellipse cx="36" cy="36" rx="25" ry="11" stroke="currentColor" stroke-width="1" opacity="0.7" transform="rotate(90 36 36)"></ellipse>
                                <ellipse cx="36" cy="36" rx="25" ry="11" stroke="currentColor" stroke-width="1" opacity="0.7" transform="rotate(30 36 36)"></ellipse>
                                <ellipse cx="36" cy="36" rx="25" ry="11" stroke="currentColor" stroke-width="1" opacity="0.7" transform="rotate(150 36 36)"></ellipse>
                            </svg>
                        </div>
                        <h3 class="ds-card-title">Semantic Vector Cache</h3>
                        <p class="ds-card-desc">
                            Generates 384-dimensional dense vectors with FastEmbed. Catches semantically equivalent queries (`similarity >= 0.82`) with sub-50ms latency and $0.00 spend.
                        </p>
                    </div>

                    <!-- Pillar 2 -->
                    <div class="ds-card">
                        <div class="ds-card-icon">
                            <svg width="64" height="64" viewBox="0 0 72 72" fill="none">
                                <rect x="18" y="22" width="15" height="15" rx="3" stroke="currentColor" stroke-width="1.1" opacity="0.85"></rect>
                                <rect x="18" y="41" width="15" height="15" rx="3" stroke="currentColor" stroke-width="1.1" opacity="0.85"></rect>
                                <rect x="37" y="41" width="15" height="15" rx="3" stroke="currentColor" stroke-width="1.1" opacity="0.85"></rect>
                                <rect x="37" y="22" width="15" height="15" rx="3" stroke="currentColor" stroke-width="0.9" stroke-dasharray="2.5 2.5" opacity="0.45"></rect>
                                <rect x="47" y="12" width="15" height="15" rx="3" stroke="currentColor" stroke-width="1.2"></rect>
                                <circle cx="54.5" cy="19.5" r="1.4" fill="currentColor"></circle>
                            </svg>
                        </div>
                        <h3 class="ds-card-title">Context Deduplication</h3>
                        <p class="ds-card-desc">
                            Multi-stage compression cleans repeated log lines, RAG chunk overlap, and system boilerplate before inference, cutting input token volume by 30%–65%.
                        </p>
                    </div>

                    <!-- Pillar 3 -->
                    <div class="ds-card">
                        <div class="ds-card-icon">
                            <svg width="64" height="64" viewBox="0 0 72 72" fill="none">
                                <circle cx="36" cy="36" r="17" stroke="currentColor" stroke-width="0.9" stroke-dasharray="2 2.5" opacity="0.5"></circle>
                                <circle cx="36" cy="36" r="26" stroke="currentColor" stroke-width="0.9" opacity="0.7"></circle>
                                <circle cx="36" cy="36" r="4.5" stroke="currentColor" stroke-width="1.2"></circle>
                                <circle cx="36" cy="10" r="2.6" fill="currentColor"></circle>
                                <circle cx="58.5" cy="23" r="2.6" fill="currentColor"></circle>
                                <circle cx="58.5" cy="49" r="2.6" fill="currentColor"></circle>
                                <circle cx="36" cy="62" r="2.6" fill="currentColor"></circle>
                                <circle cx="13.5" cy="49" r="2.6" fill="currentColor"></circle>
                                <circle cx="13.5" cy="23" r="2.6" fill="currentColor"></circle>
                            </svg>
                        </div>
                        <h3 class="ds-card-title">Complexity Routing</h3>
                        <p class="ds-card-desc">
                            Evaluates reasoning requirements and code syntax to route cheap queries to Llama 8B ($0.05/M) and scale complex architecture queries to 70B ($0.59/M).
                        </p>
                    </div>
                </div>
            </div>
        </section>

        <!-- DESIGN APPROACH & TRAJECTORY SHOWCASE -->
        <section class="ds-section">
            <div class="ds-container">
                <div class="ds-section-header" style="text-align:left; align-items:flex-start; margin-bottom:2rem;">
                    <span class="ds-hero-badge">
                        <span>Design approach</span>
                    </span>
                    <h2 class="ds-text-heading1">
                        Everything is cached.<br/>Every run is traceable.
                    </h2>
                </div>

                <div class="ds-split-grid">
                    <!-- Left: Interactive Nav -->
                    <div class="ds-feature-nav">
                        <div class="ds-feature-item active" id="fitem-1" onclick="switchFeatureItem(1)">
                            <div class="ds-feature-head">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--ds-brand);"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
                                <h3>Sub-50ms Vector Cache</h3>
                            </div>
                            <p>Query vectors are mapped via cosine similarity. Identical semantic intents bypass provider compute completely.</p>
                        </div>

                        <div class="ds-feature-item" id="fitem-2" onclick="switchFeatureItem(2)">
                            <div class="ds-feature-head">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--ds-green);"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="9" x2="15" y2="9"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>
                                <h3>Context Compression Diff</h3>
                            </div>
                            <p>Inspect character and token reduction in real-time. View exact diffs of removed timestamps, logs, and duplicate chunks.</p>
                        </div>

                        <div class="ds-feature-item" id="fitem-3" onclick="switchFeatureItem(3)">
                            <div class="ds-feature-head">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--ds-purple);"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                                <h3>Complexity Router & Telemetry</h3>
                            </div>
                            <p>Real-time metrics track exact spend saved, rolling latency curves, and routed model tiers on every transaction.</p>
                        </div>
                    </div>

                    <!-- Right: Preview Display -->
                    <div class="ds-preview-frame">
                        <div id="fprev-1">
                            <div style="font-family:var(--font-mono); font-size:12px; color:var(--ds-brand); margin-bottom:0.75rem;">// Semantic Cache Vector Match</div>
                            <div style="background:rgba(0,0,0,0.5); border:1px solid var(--ds-border-default); border-radius:8px; padding:1.25rem; font-family:var(--font-mono); font-size:13px; line-height:1.7;">
                                <div style="color:var(--ds-muted);">Incoming: <span style="color:#ffffff;">"What happens if fetch_user cannot find the database row?"</span></div>
                                <div style="color:var(--ds-muted);">Cached: <span style="color:#ffffff;">"What does fetch_user return when the row is missing?"</span></div>
                                <br/>
                                <div>Vector Match Score: <span style="color:var(--ds-green); font-weight:bold;">83.9% (Threshold: 82.0%)</span></div>
                                <div>Status: <span style="color:var(--ds-green); font-weight:bold;">CACHE HIT</span> &middot; Latency: <span style="color:var(--ds-brand);">38ms</span> &middot; Inference Spend: <span style="color:var(--ds-green);">$0.00000</span></div>
                            </div>
                        </div>

                        <div id="fprev-2" style="display:none;">
                            <div style="font-family:var(--font-mono); font-size:12px; color:var(--ds-green); margin-bottom:0.75rem;">// Context Deduplication Engine</div>
                            <div style="background:rgba(0,0,0,0.5); border:1px solid var(--ds-border-default); border-radius:8px; padding:1.25rem; font-family:var(--font-mono); font-size:13px; line-height:1.7;">
                                <div class="ds-diff-orig">-[2026-08-16 12:00:00 INFO] User initiated login flow (Duplicate line removed)</div>
                                <div class="ds-diff-opt">+[User Query] Explain distributed authentication architecture with OAuth2.</div>
                                <br/>
                                <div>Original: <span style="color:#fca5a5;">91 tokens</span> &rarr; Optimized: <span style="color:#86efac;">59 tokens</span> (<span style="color:var(--ds-green); font-weight:bold;">35.2% reduction</span>)</div>
                            </div>
                        </div>

                        <div id="fprev-3" style="display:none;">
                            <div style="font-family:var(--font-mono); font-size:12px; color:var(--ds-purple); margin-bottom:0.75rem;">// Live Complexity Routing Decision</div>
                            <div style="background:rgba(0,0,0,0.5); border:1px solid var(--ds-border-default); border-radius:8px; padding:1.25rem; font-family:var(--font-mono); font-size:13px; line-height:1.7;">
                                <div>Query Classification: <span class="ds-badge complex">COMPLEX</span></div>
                                <div>Reason: <span style="color:#ffffff;">Detected code blocks and analytical architecture keywords</span></div>
                                <div>Routed Model: <span style="color:var(--ds-brand); font-weight:bold;">Groq llama-3.3-70b-versatile ($0.59/M)</span></div>
                                <div>Cost Saved vs Direct: <span style="color:var(--ds-green); font-weight:bold;">$0.00024</span></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- DEVELOPER STUDIO & LIVE TELEMETRY (SANDBOX & DASHBOARD) -->
        <section class="ds-section" id="demo">
            <div class="ds-container">
                <div class="ds-studio-tabs" role="tablist">
                    <button class="ds-studio-tab-btn active" id="tabbtn-sandbox" onclick="switchTab('sandbox')" role="tab" aria-selected="true" aria-controls="tab-sandbox">Interactive Sandbox</button>
                    <button class="ds-studio-tab-btn" id="tabbtn-analytics" onclick="switchTab('analytics')" role="tab" aria-selected="false" aria-controls="tab-analytics">Impact Dashboard</button>
                </div>

                <!-- Tab 1: Interactive Sandbox -->
                <div id="tab-sandbox" class="ds-tab-pane active" role="tabpanel" aria-labelledby="tabbtn-sandbox">
                    <div class="ds-sandbox-grid">
                        <!-- Left: Input & Inspector -->
                        <div class="ds-glass-panel">
                            <div class="ds-panel-eyebrow">
                                <span>1. Select Preset or Input Prompt</span>
                                <span class="ds-token-badge" id="prompt-char-count">0 chars · ~0 tokens</span>
                            </div>

                            <!-- Presets -->
                            <div class="ds-chip-row" aria-label="Preset Prompts">
                                <button type="button" class="ds-chip" onclick="loadPreset('simple')">⚡ Simple Lookup</button>
                                <button type="button" class="ds-chip" onclick="loadPreset('paraphrase')">🎯 Semantic Paraphrase (Cache Test)</button>
                                <button type="button" class="ds-chip" onclick="loadPreset('noisy')">🧹 Noisy Context / RAG</button>
                                <button type="button" class="ds-chip" onclick="loadPreset('complex')">🧠 Complex Architecture</button>
                            </div>

                            <textarea class="ds-textarea" id="chat-input" placeholder="Enter a prompt to test compression, semantic caching, and model routing..." oninput="updateCharCount()" onkeydown="handleKey(event)"></textarea>

                            <div class="ds-prompt-footer">
                                <div style="font-size:12px; color:var(--ds-muted);">
                                    Press <kbd style="background:rgba(255,255,255,0.06); padding:2px 6px; border:1px solid var(--ds-border-default); border-radius:4px; font-family:var(--font-mono);">Cmd/Ctrl+Enter</kbd>
                                </div>
                                <button class="ds-btn-primary" id="btn-send" onclick="sendMessage()">
                                    <span id="btn-spinner" style="display:none; width:14px; height:14px; border:2px solid #fff; border-top-color:transparent; border-radius:50%; animation:spin 0.8s linear infinite;"></span>
                                    <span id="btn-text">Compress & Route</span>
                                </button>
                            </div>

                            <!-- Error Box -->
                            <div id="error-alert" style="display:none; margin-top:1rem; padding:0.85rem 1rem; background:rgba(239, 68, 68, 0.15); border:1px solid rgba(239, 68, 68, 0.3); border-radius:var(--radius-sm); color:#fca5a5; font-size:13.5px;"></div>

                            <!-- Result Inspector -->
                            <div class="ds-result-section" id="result-container" style="display:none;">
                                <div class="ds-panel-eyebrow">
                                    <span>2. Gateway Output & Optimization Inspector</span>
                                </div>

                                <div class="ds-res-tabs">
                                    <button type="button" class="ds-res-tab-btn active" id="btn-res-output" onclick="switchResultTab('output')">Model Output</button>
                                    <button type="button" class="ds-res-tab-btn" id="btn-res-compression" onclick="switchResultTab('compression')">Context Compression (<span id="res-tab-comp-pct">0%</span>)</button>
                                    <button type="button" class="ds-res-tab-btn" id="btn-res-diag" onclick="switchResultTab('diag')">Routing & Cache Diagnostics</button>
                                </div>

                                <!-- Output Pane -->
                                <div class="ds-res-pane active" id="pane-output">
                                    <div id="res-text" style="color:var(--ds-primary); white-space:pre-wrap;"></div>
                                </div>

                                <!-- Compression Diff Pane -->
                                <div class="ds-res-pane" id="pane-compression">
                                    <div style="margin-bottom:0.75rem; font-weight:600; color:#ffffff;" id="res-comp-summary"></div>
                                    <div class="ds-diff-box">
                                        <div class="ds-diff-orig">
                                            <div style="font-size:11px; font-weight:bold; margin-bottom:0.25rem;">ORIGINAL CONTEXT (<span id="diff-orig-tokens">0</span> tokens)</div>
                                            <div id="diff-orig-text"></div>
                                        </div>
                                        <div class="ds-diff-opt">
                                            <div style="font-size:11px; font-weight:bold; margin-bottom:0.25rem;">OPTIMIZED CONTEXT (<span id="diff-opt-tokens">0</span> tokens — <span id="diff-saved-tokens">0</span> saved)</div>
                                            <div id="diff-opt-text"></div>
                                        </div>
                                    </div>
                                    <ul id="res-savings-notes" style="margin-top:0.75rem; padding-left:1.25rem; font-size:12.5px; color:var(--ds-description);"></ul>
                                </div>

                                <!-- Diagnostics Pane -->
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
                            </div>
                        </div>

                        <!-- Right: Telemetry Panel -->
                        <div class="ds-glass-panel">
                            <div class="ds-panel-eyebrow">
                                <span>TOKEN & INFERENCE IMPACT</span>
                                <span style="font-size:11px; color:var(--ds-green); font-weight:600;"><span class="ds-status-dot-live" style="display:inline-block; vertical-align:middle; margin-right:4px;"></span> LIVE REAL-TIME</span>
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

                <!-- Tab 2: Impact Dashboard -->
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
                <h3 style="font-size:1.35rem; font-weight:700; color:#ffffff;">Semantic Gateway Integration Guide</h3>
                <button class="ds-modal-close" onclick="closeDocsModal()">&times;</button>
            </div>
            <p style="color:var(--ds-description); margin-bottom:1.5rem; font-size:0.95rem;">
                Semantic Gateway acts as a high-performance proxy in front of Groq and local LLMs. Drop it into any OpenAI-compatible client library by changing the base URL.
            </p>

            <h4 style="font-size:0.95rem; font-weight:700; margin-bottom:0.5rem; color:#ffffff;">Python OpenAI SDK Configuration</h4>
            <div style="background:rgba(0,0,0,0.5); border:1px solid var(--ds-border-default); border-radius:8px; padding:1rem; font-family:var(--font-mono); font-size:12.5px; color:#cbd5e1; margin-bottom:1.5rem;">
<span class="ds-code-keyword">from</span> openai <span class="ds-code-keyword">import</span> OpenAI

client = OpenAI(
    base_url=<span class="ds-code-string">"http://localhost:8000/v1"</span>,
    api_key=<span class="ds-code-string">"not-required"</span>  <span class="ds-code-comment"># Server-side auth</span>
)

response = client.chat.completions.create(
    model=<span class="ds-code-string">"llama-3.1-8b-instant"</span>,
    messages=[{<span class="ds-code-string">"role"</span>: <span class="ds-code-string">"user"</span>, <span class="ds-code-string">"content"</span>: <span class="ds-code-string">"Hello!"</span>}]
)
print(response.choices[0].message.content)
            </div>

            <h4 style="font-size:0.95rem; font-weight:700; margin-bottom:0.5rem; color:#ffffff;">cURL Example</h4>
            <div style="background:rgba(0,0,0,0.5); border:1px solid var(--ds-border-default); border-radius:8px; padding:1rem; font-family:var(--font-mono); font-size:12.5px; color:#cbd5e1;">
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "What is semantic caching?"}]
  }'
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
                    <p>High-performance prompt compression, sub-50ms semantic vector caching, and cost-aware model routing for agent harnesses.</p>
                    <p style="margin-top:1rem; color:var(--ds-muted); font-size:0.8rem;">Apache 2.0 Open Source</p>
                </div>
                <div class="ds-footer-col">
                    <h5>Navigation</h5>
                    <ul>
                        <li><a href="#features">Architecture</a></li>
                        <li><a href="#demo">Interactive Sandbox</a></li>
                        <li><a href="#demo">Telemetry Dashboard</a></li>
                        <li><a href="#quickstart">Quickstart</a></li>
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
                    <h5>Compute</h5>
                    <ul>
                        <li><a href="#features">384-Dim FastEmbed Vectors</a></li>
                        <li><a href="#features">Groq Llama 3.1 & 3.3</a></li>
                        <li><a href="#features">Ollama Fallback</a></li>
                        <li><a href="#features">Context Deduplication</a></li>
                    </ul>
                </div>
            </div>
        </div>
    </footer>

    <!-- STARFIELD PARTICLE CANVAS & JS LOGIC -->
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

                // Draw connecting lines
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

                // Draw particles
                stars.forEach(s => {
                    s.x += s.vx;
                    s.y += s.vy;
                    if (s.x < 0) s.x = w;
                    if (s.x > w) s.x = 0;
                    if (s.y < 0) s.y = h;
                    if (s.y > h) s.y = 0;

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

        const PRESETS = {
            simple: "What does fetch_user return when the row is missing?",
            paraphrase: "What happens if fetch_user cannot find the database row?",
            noisy: "System Context & Retrieval Output:\n[2026-08-16 12:00:00 INFO] User initiated authentication flow\n[2026-08-16 12:00:00 INFO] User initiated authentication flow\n[2026-08-16 12:00:01 DEBUG] Connected to Postgres pool (4 active)\n[2026-08-16 12:00:01 DEBUG] Connected to Postgres pool (4 active)\n\nUser Question:\nHow do I configure connection pooling for high concurrency?",
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
            document.getElementById('term-pane-sdk').style.display = tabId === 'sdk' ? 'block' : 'none';
            document.getElementById('term-pane-curl').style.display = tabId === 'curl' ? 'block' : 'none';
        }

        function switchFeatureItem(num) {
            document.querySelectorAll('.ds-feature-item').forEach(el => el.classList.remove('active'));
            document.getElementById('fitem-' + num).classList.add('active');

            document.getElementById('fprev-1').style.display = num === 1 ? 'block' : 'none';
            document.getElementById('fprev-2').style.display = num === 2 ? 'block' : 'none';
            document.getElementById('fprev-3').style.display = num === 3 ? 'block' : 'none';
        }

        function copyTermCode() {
            let text = '';
            if (document.getElementById('term-pane-quick').style.display !== 'none') {
                text = 'uvicorn main:app --host 0.0.0.0 --port 8000 --reload';
            } else if (document.getElementById('term-pane-sdk').style.display !== 'none') {
                text = 'from openai import OpenAI\n\nclient = OpenAI(base_url="http://localhost:8000/v1", api_key="not-required")\nres = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": "Hello!"}])\nprint(res.choices[0].message.content)';
            } else {
                text = 'curl -X POST http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" -d \'{"messages":[{"role":"user","content":"What is semantic caching?"}]}\'';
            }
            copyText(text);
            const copyLabel = document.getElementById('copy-text');
            copyLabel.textContent = 'Copied!';
            setTimeout(() => { copyLabel.textContent = 'Copy'; }, 2000);
        }

        function copyText(txt) {
            navigator.clipboard.writeText(txt);
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

            const ctx = document.getElementById('latencyChart').getContext('2d');
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
                    ? `<span style="color:var(--ds-green); font-weight:bold;">HIT (${cache.similarity}% similarity)</span>`
                    : `<span style="color:var(--ds-amber); font-weight:bold;">MISS</span> (Threshold: ${cache.threshold || 82}%)`;

                document.getElementById('diag-model').textContent = `${routing.model || data.model} [${routing.complexity || 'SIMPLE'}]`;
                document.getElementById('diag-latency').textContent = `${latency.total_ms || 0}ms (Cache: ${latency.cache_lookup_ms || 0}ms, Upstream: ${latency.upstream_inference_ms || 0}ms)`;
                document.getElementById('diag-cost').innerHTML = `<span style="color:var(--ds-green); font-weight:bold;">Saved $${(cost.cost_saved || 0).toFixed(5)}</span> (Spent $${(cost.actual_spent || 0).toFixed(5)})`;

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
