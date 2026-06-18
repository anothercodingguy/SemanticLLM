from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from api.router import router as chat_router
from services.cache import init_cache
from services.metrics import get_metrics_summary
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup Qdrant collection on startup if it doesn't exist
    await init_cache()
    yield

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
    Serves the modern, unified HTML/JS Dashboard & Chat Playground.
    """
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Semantic LLM Gateway & Sandbox</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-color: #09090b;
            --card-bg: #18181b;
            --card-border: #27272a;
            --primary: #f4f4f5;
            --primary-muted: #a1a1aa;
            --success: #10b981;
            --warning: #d97706;
            --danger: #ef4444;
            --text-main: #f4f4f5;
            --text-muted: #71717a;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg-color);
            color: var(--text-main);
            min-height: 100vh;
            padding: 2rem 1rem;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .container {
            width: 100%;
            max-width: 1200px;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 1.5rem;
            margin-bottom: 0.5rem;
        }

        h1 {
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--text-main);
            letter-spacing: -0.02em;
        }

        /* Tabs Navigation */
        .tabs-nav {
            display: flex;
            gap: 0.5rem;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 0.75rem;
        }

        .tab-btn {
            background: none;
            border: 1px solid transparent;
            color: var(--text-muted);
            font-family: inherit;
            font-size: 0.875rem;
            font-weight: 500;
            padding: 0.5rem 1rem;
            cursor: pointer;
            border-radius: 6px;
            transition: all 0.2s ease;
        }

        .tab-btn.active {
            color: #09090b;
            background: var(--primary);
            border-color: var(--primary);
        }

        .tab-btn:hover:not(.active) {
            color: var(--text-main);
            background: rgba(255, 255, 255, 0.05);
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        /* Metrics Cards Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.25rem;
            margin-bottom: 1.5rem;
        }

        .metric-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            padding: 1.25rem 1.5rem;
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            transition: all 0.2s ease;
        }

        .metric-card:hover {
            border-color: #3f3f46;
            transform: translateY(-2px);
        }

        .metric-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .metric-title {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600;
        }

        .metric-value-container {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 0.5rem;
        }

        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.03em;
        }

        .value-trend {
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.15rem 0.45rem;
            border-radius: 4px;
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
        }

        .value-trend.green {
            background: rgba(16, 185, 129, 0.1);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.2);
        }

        .metric-desc {
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        /* Circular Doughnut Progress */
        .circular-progress {
            position: relative;
            width: 32px;
            height: 32px;
        }
        .circular-progress svg {
            transform: rotate(-90deg);
            width: 100%;
            height: 100%;
        }
        .circle-bg {
            fill: none;
            stroke: rgba(255, 255, 255, 0.03);
            stroke-width: 4;
        }
        .circle {
            fill: none;
            stroke: var(--primary-muted);
            stroke-width: 4;
            stroke-linecap: round;
            transition: stroke-dasharray 0.3s ease;
        }

        /* Dashboard Content Cards */
        .dashboard-body {
            display: grid;
            grid-template-columns: 1fr;
            gap: 1.5rem;
        }

        @media (min-width: 1024px) {
            .dashboard-body {
                grid-template-columns: 1.2fr 1.3fr;
            }
        }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
        }

        .card-title {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            border-left: 2px solid var(--primary-muted);
            padding-left: 0.75rem;
            color: var(--text-main);
        }

        .chart-container {
            position: relative;
            height: 300px;
            width: 100%;
        }

        /* Query Log Table Styles */
        .table-container {
            max-height: 400px;
            overflow-y: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }

        th, td {
            padding: 0.85rem 0.75rem;
            border-bottom: 1px solid var(--card-border);
            font-size: 0.85rem;
        }

        th {
            color: var(--text-muted);
            font-weight: 600;
            background: var(--card-bg);
            position: sticky;
            top: 0;
            z-index: 10;
        }

        tr:hover {
            background: rgba(255, 255, 255, 0.01);
        }

        /* Badges & Dots */
        .badge {
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: capitalize;
        }

        .badge.simple {
            background: rgba(161, 161, 170, 0.1);
            color: #a1a1aa;
            border: 1px solid rgba(161, 161, 170, 0.2);
        }

        .badge.advanced {
            background: rgba(99, 102, 241, 0.1);
            color: #a5b4fc;
            border: 1px solid rgba(99, 102, 241, 0.2);
        }

        .status-dot {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            font-weight: 700;
            font-size: 0.75rem;
        }

        .status-dot::before {
            content: '';
            display: inline-block;
            width: 5px;
            height: 5px;
            border-radius: 50%;
        }

        .status-dot.hit {
            color: var(--success);
        }
        .status-dot.hit::before {
            background: var(--success);
        }

        .status-dot.miss {
            color: var(--warning);
        }
        .status-dot.miss::before {
            background: var(--warning);
        }

        .prompt-text {
            max-width: 160px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--text-main);
        }

        /* Chat Tab CSS */
        .chat-layout {
            display: flex;
            flex-direction: column;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            height: 600px;
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
            max-width: 80%;
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }

        .message.user {
            align-self: flex-end;
        }

        .message.assistant {
            align-self: flex-start;
        }

        .msg-bubble {
            padding: 0.8rem 1.2rem;
            border-radius: 8px;
            line-height: 1.5;
            font-size: 0.9rem;
        }

        .message.user .msg-bubble {
            background: var(--primary);
            color: #09090b;
        }

        .message.assistant .msg-bubble {
            background: var(--bg-color);
            color: var(--text-main);
            border: 1px solid var(--card-border);
        }

        .message.system-message {
            align-self: stretch;
            max-width: 100%;
        }

        .message.system-message .msg-bubble {
            background: transparent;
            border: 1px dashed var(--card-border);
            color: var(--text-muted);
            font-size: 0.875rem;
            text-align: center;
        }

        .msg-info {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        }

        .chat-input-area {
            display: flex;
            gap: 0.75rem;
            padding: 1.25rem;
            background: rgba(0, 0, 0, 0.15);
            border-top: 1px solid var(--card-border);
        }

        .chat-input {
            flex: 1;
            background: var(--bg-color);
            border: 1px solid var(--card-border);
            color: #fff;
            border-radius: 6px;
            padding: 0.8rem 1.2rem;
            font-family: inherit;
            font-size: 0.9rem;
            outline: none;
            transition: all 0.2s ease;
        }

        .chat-input:focus {
            border-color: #52525b;
        }

        .btn-send {
            background: var(--primary);
            color: #09090b;
            border: 1px solid var(--primary);
            padding: 0.8rem 1.5rem;
            border-radius: 6px;
            font-family: inherit;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-send:hover {
            background: #e4e4e7;
            border-color: #e4e4e7;
        }

        .btn-send:disabled {
            background: #27272a;
            border-color: #27272a;
            color: var(--text-muted);
            cursor: not-allowed;
        }

        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 6px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.05);
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.1);
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>Semantic LLM Gateway & Sandbox</h1>
                <p style="color: var(--text-muted); margin-top: 0.25rem;">Cost-Aware Routing & Semantic Cache Playground</p>
            </div>
            <div style="font-size: 0.875rem; display: flex; align-items: center; gap: 0.5rem; background: var(--card-bg); padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid var(--card-border);">
                <span style="display:inline-block; width:8px; height:8px; background:var(--success); border-radius:50%;"></span>
                Online (Render)
            </div>
        </header>

        <!-- Tabs Navigation -->
        <div class="tabs-nav">
            <button class="tab-btn active" onclick="switchTab('analytics')">Analytics & Logs</button>
            <button class="tab-btn" onclick="switchTab('chat')">Chat Sandbox Playground</button>
        </div>

        <!-- Analytics Tab -->
        <div id="tab-analytics" class="tab-content active">
            <div class="metrics-grid">
                
                <!-- 1. Total Cost Saved -->
                <div class="metric-card saved">
                    <div class="metric-header">
                        <span class="metric-title">Total Cost Saved</span>
                        <span class="metric-icon">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--success);"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
                        </span>
                    </div>
                    <div class="metric-value-container">
                        <span class="metric-value" id="val-saved">$0.000000</span>
                        <span class="value-trend green">↗</span>
                    </div>
                    <div class="metric-desc">Estimated saved by cache hits</div>
                </div>

                <!-- 2. Total Cost Spent -->
                <div class="metric-card spent">
                    <div class="metric-header">
                        <span class="metric-title">Total Cost Spent</span>
                        <span class="metric-icon">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--warning);">
                                <ellipse cx="12" cy="6" rx="8" ry="3"></ellipse>
                                <path d="M4 6v8c0 1.66 3.58 3 8 3s8-1.34 8-3V6"></path>
                                <path d="M4 11c0 1.66 3.58 3 8 3s8-1.34 8-3"></path>
                            </svg>
                        </span>
                    </div>
                    <div class="metric-value" id="val-spent">$0.000000</div>
                    <div class="metric-desc">Total API spend on upstream models</div>
                </div>

                <!-- 3. Cache Hit Rate -->
                <div class="metric-card hitrate">
                    <div class="metric-header">
                        <span class="metric-title">Cache Hit Rate</span>
                    </div>
                    <div class="metric-value-container">
                        <span class="metric-value" id="val-hitrate">0.00%</span>
                        <div class="circular-progress">
                            <svg viewBox="0 0 36 36">
                                <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                                <path class="circle" id="hitrate-circle" stroke-dasharray="0, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                            </svg>
                        </div>
                    </div>
                    <div class="metric-desc">Semantically cached queries vs. total</div>
                </div>

                <!-- 4. Average Latency -->
                <div class="metric-card latency">
                    <div class="metric-header">
                        <span class="metric-title">Average Latency</span>
                        <span class="metric-icon">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #6366f1;"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                        </span>
                    </div>
                    <div class="metric-value-container" style="justify-content: flex-start; gap: 0.5rem; margin: 0.25rem 0; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 0.25rem;">
                            <span class="metric-value" id="val-latency-cached" style="font-size: 1.5rem; color: #ffffff;">0ms</span>
                            <span class="value-trend green" style="font-size: 0.7rem; padding: 0.1rem 0.3rem; font-weight: 600;">Cached</span>
                        </div>
                        <span style="color: var(--text-muted); font-size: 1.25rem;">/</span>
                        <div style="display: flex; align-items: center; gap: 0.25rem;">
                            <span class="metric-value" id="val-latency-direct" style="font-size: 1.5rem; color: #ffffff;">0ms</span>
                            <span style="font-size: 0.7rem; padding: 0.1rem 0.3rem; background: rgba(255, 255, 255, 0.05); color: var(--text-muted); border: 1px solid var(--card-border); border-radius: 4px; font-weight: 600;">Direct</span>
                        </div>
                    </div>
                    <div class="metric-desc">Mean response time comparison</div>
                </div>

            </div>

            <div class="dashboard-body">
                <div class="card">
                    <div class="card-title">Latency Comparison</div>
                    <div class="chart-container">
                        <canvas id="latencyChart"></canvas>
                    </div>
                </div>

                <div class="card">
                    <div class="card-title">Query Log</div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Prompt</th>
                                    <th>Complexity</th>
                                    <th>Model/Route</th>
                                    <th>Cache</th>
                                    <th>Latency</th>
                                </tr>
                            </thead>
                            <tbody id="queries-tbody">
                                <!-- Populated dynamically -->
                            </tbody>
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
                            Hello! I am connected to the <strong>Semantic LLM Gateway</strong>. Send me any query to test the intent routing (SIMPLE vs COMPLEX) and semantic caching!
                        </div>
                    </div>
                </div>
                <div class="chat-input-area">
                    <input type="text" class="chat-input" id="chat-input" placeholder="Type a message to test gateway..." onkeydown="handleKey(event)" />
                    <button class="btn-send" id="btn-send" onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let latencyChart = null;
        let activeTab = 'analytics';
        let chatHistory = [];

        function switchTab(tabId) {
            activeTab = tabId;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(btn => btn.textContent.toLowerCase().includes(tabId));
            if (activeBtn) activeBtn.classList.add('active');
            
            document.getElementById(`tab-${tabId}`).classList.add('active');
            
            if (tabId === 'analytics') {
                fetchMetrics();
            }
        }

        async function fetchMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                
                document.getElementById('val-saved').textContent = `$${data.total_saved.toFixed(6)}`;
                document.getElementById('val-spent').textContent = `$${data.total_spent.toFixed(6)}`;
                document.getElementById('val-hitrate').textContent = `${data.hit_rate.toFixed(2)}%`;
                
                // Update circle path
                const percent = Math.min(100, Math.max(0, data.hit_rate));
                document.getElementById('hitrate-circle').setAttribute('stroke-dasharray', `${percent}, 100`);

                // Update split latencies
                document.getElementById('val-latency-cached').textContent = `${Math.round(data.avg_latency_hit)}ms`;
                document.getElementById('val-latency-direct').textContent = `${Math.round(data.avg_latency_miss)}ms`;

                const tbody = document.getElementById('queries-tbody');
                tbody.innerHTML = '';
                
                if (data.queries.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 2rem;">No queries recorded yet. Make some requests in the Sandbox!</td></tr>';
                } else {
                    data.queries.forEach(q => {
                        const tr = document.createElement('tr');
                        
                        const cacheBadge = q.is_cache_hit === 1 
                            ? '<span class="status-dot hit">HIT</span>' 
                            : '<span class="status-dot miss">MISS</span>';
                            
                        const complexityBadge = q.complexity === 'COMPLEX'
                            ? '<span class="badge advanced">Advanced</span>'
                            : '<span class="badge simple">Simple</span>';

                        tr.innerHTML = `
                            <td class="prompt-text" title="${escapeHtml(q.prompt)}">${escapeHtml(q.prompt)}</td>
                            <td>${complexityBadge}</td>
                            <td style="color: #cbd5e1;">${formatModelRoute(q.model_routed)}</td>
                            <td>${cacheBadge}</td>
                            <td style="font-weight: 600; color: #f1f5f9;">${Math.round(q.latency_ms)}ms</td>
                        `;
                        tbody.appendChild(tr);
                    });
                }

                updateChart(data.queries);
                
            } catch (error) {
                console.error('Error fetching metrics:', error);
            }
        }

        function formatModelRoute(model) {
            if (!model) return 'Unknown';
            if (model.startsWith("llama-3.1-8b")) {
                return "<strong>Groq</strong> Llama3.1-8B";
            }
            if (model.startsWith("llama-3.3-70b")) {
                return "<strong>Groq</strong> Llama3.3-70B";
            }
            if (model.startsWith("ollama")) {
                return "<strong>Ollama</strong> Fallback";
            }
            if (model.includes("-")) {
                const parts = model.split("-");
                return "<strong>" + parts[0].charAt(0).toUpperCase() + parts[0].slice(1) + "</strong> " + parts.slice(1).join(" ");
            }
            return "<strong>Model</strong> " + model;
        }

        function escapeHtml(text) {
            return text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        function updateChart(queries) {
            const chronologicalQueries = [...queries].reverse();
            const labels = [];
            const hitData = [];
            const missData = [];

            chronologicalQueries.forEach((q, idx) => {
                const timeStr = new Date(q.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                labels.push(timeStr);
                
                if (q.is_cache_hit === 1) {
                    hitData.push(q.latency_ms);
                    missData.push(null);
                } else {
                    missData.push(q.latency_ms);
                    hitData.push(null);
                }
            });

            const ctx = document.getElementById('latencyChart').getContext('2d');
            
            if (latencyChart) {
                latencyChart.destroy();
            }

            // Create gradients for fill
            const indigoGrad = ctx.createLinearGradient(0, 0, 0, 300);
            indigoGrad.addColorStop(0, 'rgba(99, 102, 241, 0.15)');
            indigoGrad.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

            const amberGrad = ctx.createLinearGradient(0, 0, 0, 300);
            amberGrad.addColorStop(0, 'rgba(217, 119, 6, 0.15)');
            amberGrad.addColorStop(1, 'rgba(217, 119, 6, 0.0)');

            latencyChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels.length > 0 ? labels : ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00'],
                    datasets: [
                        {
                            label: 'Cache HIT',
                            data: hitData.length > 0 ? hitData : [80, 110, 90, 120, 80, 100, 75],
                            borderColor: '#6366f1',
                            backgroundColor: indigoGrad,
                            borderWidth: 2,
                            tension: 0.4,
                            fill: true,
                            spanGaps: true,
                            pointBackgroundColor: '#6366f1',
                            pointHoverRadius: 6
                        },
                        {
                            label: 'Cache MISS',
                            data: missData.length > 0 ? missData : [230, 380, 260, 310, 480, 470, 350],
                            borderColor: '#d97706',
                            backgroundColor: amberGrad,
                            borderWidth: 2,
                            tension: 0.4,
                            fill: true,
                            spanGaps: true,
                            pointBackgroundColor: '#d97706',
                            pointHoverRadius: 6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#a1a1aa',
                                font: { family: 'Outfit', size: 11 }
                            }
                        }
                    },
                    scales: {
                        y: {
                            title: {
                                display: true,
                                text: 'Latency (ms)',
                                color: '#71717a'
                            },
                            grid: { color: '#27272a' },
                            ticks: { color: '#71717a' },
                            beginAtZero: true
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Timeline',
                                color: '#71717a'
                            },
                            grid: { display: false },
                            ticks: { color: '#71717a' }
                        }
                    }
                }
            });
        }

        // Chat Sandbox Logic
        function handleKey(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        }

        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const prompt = input.value.trim();
            if (!prompt) return;

            // Clear input
            input.value = '';

            // Add user bubble
            appendMessage('user', prompt);
            
            // Add typing indicator
            const typingId = appendTypingIndicator();

            chatHistory.push({ role: 'user', content: prompt });

            const sendBtn = document.getElementById('btn-send');
            const inputField = document.getElementById('chat-input');
            sendBtn.disabled = true;
            inputField.disabled = true;

            const startTime = performance.now();

            try {
                const response = await fetch('/v1/chat/completions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        messages: chatHistory
                    })
                });

                const latencyMs = performance.now() - startTime;
                
                removeTypingIndicator(typingId);

                if (!response.ok) {
                    let errDetail = `Server returned code ${response.status}`;
                    try {
                        const errJson = await response.json();
                        if (errJson && errJson.detail) {
                            errDetail = errJson.detail;
                        }
                    } catch (e) {}
                    throw new Error(errDetail);
                }

                const data = await response.json();
                const assistantMessage = data.choices[0].message.content;
                const cacheLookup = response.headers.get('X-Cache-Lookup') || 'MISS';
                const modelRouted = data.model;
                const usage = data.usage || { prompt_tokens: 0, completion_tokens: 0 };

                chatHistory.push({ role: 'assistant', content: assistantMessage });

                // Append response
                appendMessage('assistant', assistantMessage, {
                    latency: latencyMs,
                    cache: cacheLookup,
                    model: modelRouted,
                    tokens: usage.prompt_tokens + usage.completion_tokens
                });

                // Refresh metrics in background
                fetchMetrics();

            } catch (error) {
                removeTypingIndicator(typingId);
                appendMessage('assistant', `⚠️ **Error connecting to LLM Gateway**: ${error.message}. Make sure your backend settings are configured.`);
            } finally {
                sendBtn.disabled = false;
                inputField.disabled = false;
                inputField.focus();
            }
        }

        function appendMessage(sender, text, meta = null) {
            const container = document.getElementById('chat-messages');
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${sender}`;

            const bubble = document.createElement('div');
            bubble.className = 'msg-bubble';
            bubble.innerHTML = escapeHtml(text).replace(/\\n/g, '<br/>');
            msgDiv.appendChild(bubble);

            if (meta) {
                const info = document.createElement('div');
                info.className = 'msg-info';
                
                const cacheClass = meta.cache === 'HIT' ? 'hit' : 'miss';
                info.innerHTML = `
                    <span class="status-dot ${cacheClass}">${meta.cache}</span>
                    <span>Route: <strong>${meta.model}</strong></span>
                    <span>Latency: <strong>${meta.latency.toFixed(0)}ms</strong></span>
                    <span>Tokens: <strong>${meta.tokens}</strong></span>
                `;
                msgDiv.appendChild(info);
            }

            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
        }

        function appendTypingIndicator() {
            const container = document.getElementById('chat-messages');
            const msgDiv = document.createElement('div');
            const id = 'typing-' + Date.now();
            msgDiv.className = 'message assistant';
            msgDiv.id = id;

            const bubble = document.createElement('div');
            bubble.className = 'msg-bubble';
            bubble.innerHTML = '<span style="color: var(--text-muted);">Gateway routing query...</span>';
            msgDiv.appendChild(bubble);

            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
            return id;
        }

        function removeTypingIndicator(id) {
            const el = document.getElementById(id);
            if (el) el.remove();
        }

        // Initial fetch
        fetchMetrics();
        setInterval(fetchMetrics, 15000);
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)
