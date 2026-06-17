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
    Serves the modern, native HTML/JS dashboard at the base URL.
    """
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Semantic LLM Gateway Dashboard</title>
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
            padding: 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .container {
            width: 100%;
            max-width: 1200px;
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 1.5rem;
        }

        h1 {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #a5b4fc 0%, #6366f1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .btn-refresh {
            background: var(--primary);
            color: #fff;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-family: inherit;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 14px var(--primary-glow);
        }

        .btn-refresh:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.3);
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.5rem;
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
            position: relative;
            overflow: hidden;
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
                grid-template-columns: 1fr 1fr;
            }
        }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            backdrop-filter: blur(12px);
            border-radius: 16px;
            padding: 1.5rem;
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

        /* Queries Table */
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
            max-width: 250px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
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
                <h1>Semantic LLM Gateway & Proxy</h1>
                <p style="color: var(--text-muted); margin-top: 0.25rem;">Real-time Telemetry & Cost-Aware Routing</p>
            </div>
            <button class="btn-refresh" onclick="fetchMetrics()">Refresh Data</button>
        </header>

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
                <div class="card-title">Latency Comparison</div>
                <div class="chart-container">
                    <canvas id="latencyChart"></canvas>
                </div>
            </div>

            <div class="card">
                <div class="card-title">Recent Queries (Last 20)</div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Prompt</th>
                                <th>Complexity</th>
                                <th>Model / Route</th>
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

    <script>
        let latencyChart = null;

        async function fetchMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                
                // Update metrics values
                document.getElementById('val-saved').textContent = `$${data.total_saved.toFixed(6)}`;
                document.getElementById('val-spent').textContent = `$${data.total_spent.toFixed(6)}`;
                document.getElementById('val-hitrate').textContent = `${data.hit_rate.toFixed(2)}%`;
                document.getElementById('val-latency').textContent = `${data.avg_latency.toFixed(2)} ms`;

                // Update Table
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

                // Update Chart
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
                    labels: ['Cache Hit', 'Cache Miss (Live Groq/Ollama)'],
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

        fetchMetrics();
        setInterval(fetchMetrics, 10000);
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)
