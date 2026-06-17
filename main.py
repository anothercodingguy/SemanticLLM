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
    expose_headers=["X-Cache-Lookup"],  # Expose this custom header for CORS requests
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
            --bg-color: #0b0f19;
            --card-bg: rgba(255, 255, 255, 0.03);
            --card-border: rgba(255, 255, 255, 0.08);
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.15);
            --success: #10b981;
            --success-glow: rgba(16, 185, 129, 0.15);
            --warning: #f59e0b;
            --danger: #ef4444;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background: radial-gradient(circle at top right, #1e1b4b 0%, #0f172a 50%, #090d16 100%);
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
            padding-bottom: 1rem;
        }

        h1 {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #a5b4fc 0%, #6366f1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Tabs Navigation */
        .tabs-nav {
            display: flex;
            gap: 1rem;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 0.5rem;
        }

        .tab-btn {
            background: none;
            border: none;
            color: var(--text-muted);
            font-family: inherit;
            font-size: 1rem;
            font-weight: 600;
            padding: 0.5rem 1rem;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.3s ease;
        }

        .tab-btn.active {
            color: #fff;
            background: var(--primary);
            box-shadow: 0 4px 12px var(--primary-glow);
        }

        .tab-btn:hover:not(.active) {
            color: #fff;
            background: rgba(255, 255, 255, 0.05);
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        /* Analytics Tab CSS */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .metric-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            backdrop-filter: blur(12px);
            padding: 1.5rem;
            border-radius: 16px;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            transition: all 0.3s ease;
        }

        .metric-card:hover {
            border-color: rgba(99, 102, 241, 0.3);
            transform: translateY(-4px);
        }

        .metric-title {
            font-size: 0.875rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .metric-value {
            font-size: 2.25rem;
            font-weight: 700;
        }

        .metric-card.saved .metric-value { color: var(--success); }
        .metric-card.spent .metric-value { color: var(--warning); }
        .metric-card.hitrate .metric-value { color: #38bdf8; }

        .dashboard-body {
            display: grid;
            grid-template-columns: 1fr;
            gap: 2rem;
        }

        @media (min-width: 900px) {
            .dashboard-body {
                grid-template-columns: 1fr 1.2fr;
            }
        }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            backdrop-filter: blur(12px);
            border-radius: 16px;
            padding: 1.5rem;
            height: 100%;
        }

        .card-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            border-left: 4px solid var(--primary);
            padding-left: 0.75rem;
        }

        .chart-container {
            position: relative;
            height: 300px;
            width: 100%;
        }

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
            padding: 1rem;
            border-bottom: 1px solid var(--card-border);
            font-size: 0.875rem;
        }

        th {
            color: var(--text-muted);
            font-weight: 600;
            background: rgba(0, 0, 0, 0.2);
            position: sticky;
            top: 0;
            z-index: 10;
        }

        tr:hover {
            background: rgba(255, 255, 255, 0.01);
        }

        .badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
        }

        .badge.hit {
            background: var(--success-glow);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .badge.miss {
            background: rgba(239, 68, 68, 0.15);
            color: var(--danger);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }

        .badge.simple {
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
        }

        .badge.complex {
            background: rgba(168, 85, 247, 0.15);
            color: #c084fc;
        }

        .prompt-text {
            max-width: 200px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* Chat Tab CSS */
        .chat-layout {
            display: flex;
            flex-direction: column;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
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
            padding: 0.85rem 1.25rem;
            border-radius: 14px;
            line-height: 1.5;
            font-size: 0.95rem;
        }

        .message.user .msg-bubble {
            background: var(--primary);
            color: #fff;
            border-bottom-right-radius: 2px;
            box-shadow: 0 4px 12px var(--primary-glow);
        }

        .message.assistant .msg-bubble {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-main);
            border-bottom-left-radius: 2px;
            border: 1px solid var(--card-border);
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
            gap: 1rem;
            padding: 1.5rem;
            background: rgba(0, 0, 0, 0.2);
            border-top: 1px solid var(--card-border);
        }

        .chat-input {
            flex: 1;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--card-border);
            color: #fff;
            border-radius: 8px;
            padding: 0.85rem 1.25rem;
            font-family: inherit;
            font-size: 0.95rem;
            outline: none;
            transition: all 0.3s ease;
        }

        .chat-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 2px var(--primary-glow);
        }

        .btn-send {
            background: var(--primary);
            color: #fff;
            border: none;
            padding: 0.85rem 1.75rem;
            border-radius: 8px;
            font-family: inherit;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px var(--primary-glow);
        }

        .btn-send:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(99, 102, 241, 0.35);
        }

        .btn-send:disabled {
            background: var(--text-muted);
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.1);
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.2);
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
                <div class="metric-card saved">
                    <div class="metric-title">Total Cost Saved</div>
                    <div class="metric-value" id="val-saved">$0.000000</div>
                </div>
                <div class="metric-card spent">
                    <div class="metric-title">Total Cost Spent</div>
                    <div class="metric-value" id="val-spent">$0.000000</div>
                </div>
                <div class="metric-card hitrate">
                    <div class="metric-title">Cache Hit Rate</div>
                    <div class="metric-value" id="val-hitrate">0.00%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Average Latency</div>
                    <div class="metric-value" id="val-latency" style="color: #a7f3d0;">0.00 ms</div>
                </div>
            </div>

            <div class="dashboard-body">
                <div class="card">
                    <div class="card-title">Latency comparison</div>
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
                    <div class="message assistant">
                        <div class="msg-bubble">
                            Hello! I am connected to the **Semantic LLM Gateway**. Send me any query to test the intent routing (SIMPLE vs COMPLEX) and semantic caching!
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
                document.getElementById('val-latency').textContent = `${data.avg_latency.toFixed(2)} ms`;

                const tbody = document.getElementById('queries-tbody');
                tbody.innerHTML = '';
                
                if (data.queries.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No queries recorded yet.</td></tr>';
                } else {
                    data.queries.forEach(q => {
                        const tr = document.createElement('tr');
                        
                        const cacheBadge = q.is_cache_hit === 1 
                            ? '<span class="badge hit">HIT</span>' 
                            : '<span class="badge miss">MISS</span>';
                            
                        const complexityBadge = q.complexity === 'COMPLEX'
                            ? '<span class="badge complex">COMPLEX</span>'
                            : '<span class="badge simple">SIMPLE</span>';

                        tr.innerHTML = `
                            <td class="prompt-text" title="${escapeHtml(q.prompt)}">${escapeHtml(q.prompt)}</td>
                            <td>${complexityBadge}</td>
                            <td style="font-family: monospace; color: #cbd5e1;">${q.model_routed}</td>
                            <td>${cacheBadge}</td>
                            <td style="font-weight: 600;">${q.latency_ms.toFixed(1)} ms</td>
                        `;
                        tbody.appendChild(tr);
                    });
                }

                updateChart(data.queries);
                
            } catch (error) {
                console.error('Error fetching metrics:', error);
            }
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
            let hitSum = 0, hitCount = 0;
            let missSum = 0, missCount = 0;

            queries.forEach(q => {
                if (q.is_cache_hit === 1) {
                    hitSum += q.latency_ms;
                    hitCount++;
                } else {
                    missSum += q.latency_ms;
                    missCount++;
                }
            });

            const avgHit = hitCount > 0 ? hitSum / hitCount : 0;
            const avgMiss = missCount > 0 ? missSum / missCount : 0;

            const ctx = document.getElementById('latencyChart').getContext('2d');
            
            if (latencyChart) {
                latencyChart.destroy();
            }

            latencyChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Cache Hit', 'Cache Miss (Live)'],
                    datasets: [{
                        label: 'Average Latency (ms)',
                        data: [avgHit, avgMiss],
                        backgroundColor: [
                            'rgba(16, 185, 129, 0.4)',
                            'rgba(99, 102, 241, 0.4)'
                        ],
                        borderColor: [
                            '#10b981',
                            '#6366f1'
                        ],
                        borderWidth: 2,
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { color: '#94a3b8' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#94a3b8' }
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
            bubble.innerHTML = escapeHtml(text).replace(/\n/g, '<br/>');
            msgDiv.appendChild(bubble);

            if (meta) {
                const info = document.createElement('div');
                info.className = 'msg-info';
                
                const cacheClass = meta.cache === 'HIT' ? 'hit' : 'miss';
                info.innerHTML = `
                    <span class="badge ${cacheClass}">${meta.cache}</span>
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
