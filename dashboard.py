import os
from flask import Flask, render_template_string, jsonify, request
from supabase import create_client, Client
from dotenv import load_dotenv
from log_parser import LogParser

load_dotenv()
parser = LogParser()

app = Flask(__name__)
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

from functools import wraps

# --- SECURITY MODULE ---
DASHBOARD_API_KEY = os.getenv("DASHBOARD_API_KEY", "sentinel-secure-key-123")

def require_api_key(f):
    """Decorator to require API key for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        provided_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if provided_key != DASHBOARD_API_KEY:
            return jsonify({"error": "Unauthorized. Invalid or missing API key."}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- PREMIUM DARK MODE DASHBOARD TEMPLATE ---
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Log Intelligence | Command Center</title>
    <!-- Fonts & Icons -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-main: #020617;
            --bg-card: #0f172a;
            --bg-card-hover: #1e293b;
            --border: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #64748b;
            --accent-cyan: #06b6d4;
            --accent-red: #ef4444;
            --accent-yellow: #f59e0b;
            --accent-green: #10b981;
            --accent-purple: #8b5cf6;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: var(--bg-main); color: var(--text-main); font-family: 'Inter', sans-serif; }
        
        /* Navbar */
        .navbar {
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 50;
        }
        .logo { font-size: 1.25rem; font-weight: 700; display: flex; align-items: center; gap: 0.75rem; }
        .logo i { color: var(--accent-cyan); text-shadow: 0 0 10px rgba(6, 182, 212, 0.5); }
        .status-badge { display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; color: var(--text-muted); }
        .pulse-dot { width: 8px; height: 8px; background: var(--accent-green); border-radius: 50%; box-shadow: 0 0 8px var(--accent-green); animation: pulse 2s infinite; }
        @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(1.2); } 100% { opacity: 1; transform: scale(1); } }

        /* Layout */
        .dashboard-container { padding: 1.5rem 2rem; display: grid; gap: 1.5rem; }
        
        /* Cards */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            overflow: hidden;
            transition: border-color 0.3s;
        }
        .card:hover { border-color: #334155; }
        .card-header {
            padding: 1rem 1.25rem;
            border-bottom: 1px solid var(--border);
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.95rem;
        }
        .card-body { padding: 1.25rem; }

        /* KPI Grid */
        .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; }
        .kpi-card { text-align: left; }
        .kpi-icon { width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; font-size: 1.1rem; }
        .kpi-value { font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem; }
        .kpi-label { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }

        /* Main Grid */
        .main-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; }
        .chart-sub-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }

        /* Terminal Logs */
        .terminal {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            height: 450px;
            overflow-y: auto;
            background: #030712;
            padding: 1rem;
        }
        .terminal::-webkit-scrollbar { width: 6px; }
        .terminal::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
        .log-line { padding: 0.5rem; border-bottom: 1px solid rgba(30, 41, 59, 0.5); display: flex; gap: 1rem; }
        .log-ts { color: var(--text-muted); white-space: nowrap; }
        .log-level { font-weight: 600; min-width: 60px; }
        .log-msg { color: #cbd5e1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .anomaly-badge { color: var(--accent-yellow); font-size: 0.7rem; border: 1px solid var(--accent-yellow); padding: 0 4px; border-radius: 4px; height: fit-content; }

        /* Alerts & AI */
        .alert-list { max-height: 250px; overflow-y: auto; }
        .alert-item { padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 0.75rem; border-left: 4px solid; }
        .alert-critical { background: rgba(239, 68, 68, 0.1); border-color: var(--accent-red); }
        .alert-high { background: rgba(249, 115, 22, 0.1); border-color: #f97316; }
        
        .ai-card { padding: 1rem; border-radius: 0.5rem; margin-bottom: 0.75rem; background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.2); }
        .ai-severity { font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 9999px; }
        .sev-critical { background: rgba(239,68,68,0.2); color: #fca5a5; }
        .sev-high { background: rgba(249,115,22,0.2); color: #fdba74; }

        .pagination { display: flex; justify-content: center; gap: 0.5rem; padding: 1rem; border-top: 1px solid var(--border); }
        .btn { padding: 0.5rem 1rem; border-radius: 0.375rem; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-main); cursor: pointer; transition: 0.2s; }
        .btn:hover { background: var(--bg-card-hover); }
    </style>
</head>
<body>

    <div class="navbar">
        <div class="logo">
            <i class="fa-solid fa-shield-halved"></i>
            <span>SENTINEL AI</span>
        </div>
        <div class="status-badge">
            <div class="pulse-dot"></div>
            <span>System Online</span>
            <span style="margin-left: 1rem; color: var(--text-main);" id="live-clock">--:--:--</span>
        </div>
    </div>

    <div class="dashboard-container">
        
        <!-- KPI Row -->
        <div class="kpi-grid">
            <div class="card kpi-card">
                <div class="card-body">
                    <div class="kpi-icon" style="background: rgba(6, 182, 212, 0.1); color: var(--accent-cyan);"><i class="fa-solid fa-server"></i></div>
                    <div class="kpi-value" id="stat-total">0</div>
                    <div class="kpi-label">Total Ingested</div>
                </div>
            </div>
            <div class="card kpi-card">
                <div class="card-body">
                    <div class="kpi-icon" style="background: rgba(245, 158, 11, 0.1); color: var(--accent-yellow);"><i class="fa-solid fa-triangle-exclamation"></i></div>
                    <div class="kpi-value" style="color: var(--accent-yellow);" id="stat-anomalies">0</div>
                    <div class="kpi-label">Anomalies Flagged</div>
                </div>
            </div>
            <div class="card kpi-card">
                <div class="card-body">
                    <div class="kpi-icon" style="background: rgba(139, 92, 246, 0.1); color: var(--accent-purple);"><i class="fa-solid fa-brain"></i></div>
                    <div class="kpi-value" style="color: var(--accent-purple);" id="stat-analyzed">0</div>
                    <div class="kpi-label">AI Analyzed</div>
                </div>
            </div>
            <div class="card kpi-card">
                <div class="card-body">
                    <div class="kpi-icon" style="background: rgba(239, 68, 68, 0.1); color: var(--accent-red);"><i class="fa-solid fa-bell"></i></div>
                    <div class="kpi-value" style="color: var(--accent-red);" id="stat-alerts">0</div>
                    <div class="kpi-label">Active Alerts</div>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="main-grid">
            
            <!-- Left Column -->
            <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                
                <!-- Charts -->
                <div class="chart-sub-grid">
                    <div class="card">
                        <div class="card-header"><span><i class="fa-solid fa-chart-pie" style="color:var(--accent-cyan); margin-right:8px;"></i>Log Distribution</span></div>
                        <div class="card-body" style="height: 200px; display:flex; align-items:center; justify-content:center;">
                            <canvas id="doughnutChart"></canvas>
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-header"><span><i class="fa-solid fa-chart-line" style="color:var(--accent-red); margin-right:8px;"></i>Anomaly Spikes</span></div>
                        <div class="card-body" style="height: 200px;">
                            <canvas id="lineChart"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Live Logs -->
                <div class="card" style="flex: 1;">
                    <div class="card-header">
                        <span><i class="fa-solid fa-terminal" style="color:var(--accent-green); margin-right:8px;"></i>Live Log Stream</span>
                        <span id="page-info" style="font-size:0.8rem; color:var(--text-muted);">Page 1</span>
                    </div>
                    <div id="log-stream" class="terminal"></div>
                    <div class="pagination">
                        <button class="btn" onclick="changePage(-1)"><i class="fa-solid fa-chevron-left"></i> Prev</button>
                        <button class="btn" onclick="changePage(1)">Next <i class="fa-solid fa-chevron-right"></i></button>
                    </div>
                </div>
            </div>

            <!-- Right Column -->
            <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                
                <!-- Active Alerts -->
                <div class="card">
                    <div class="card-header" style="background: rgba(239,68,68,0.05); color: #fca5a5;">
                        <span><i class="fa-solid fa-circle-exclamation" style="margin-right:8px;"></i>Threat Alerts</span>
                    </div>
                    <div class="card-body alert-list" id="alerts-panel">
                        <p style="text-align:center; color:var(--text-muted); font-size:0.85rem; padding:2rem 0;">No active threats 🛡️</p>
                    </div>
                </div>

                <!-- AI Analysis -->
                <div class="card" style="flex: 1;">
                    <div class="card-header" style="background: rgba(139,92,246,0.05); color: #c4b5fd;">
                        <span><i class="fa-solid fa-microchip" style="margin-right:8px;"></i>AI Intelligence Feed</span>
                    </div>
                    <div class="card-body alert-list" id="analysis-panel" style="max-height: 450px;">
                        <p style="text-align:center; color:var(--text-muted); font-size:0.85rem; padding:2rem 0;">Waiting for anomalies...</p>
                    </div>
                </div>

            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        let currentPage = 1;
        const perPage = 40;
        let dChart, lChart;

        // --- SECURITY: Universal Secure Fetch ---
        const API_KEY = 'sentinel-secure-key-123';
        async function secureFetch(url) {
            const res = await fetch(url, {
                headers: { 'X-API-Key': API_KEY }
            });
            if (res.status === 401) {
                console.error("Security: Invalid API Key");
                return null;
            }
            return res.json();
        }

        // Live Clock
        setInterval(() => {
            const now = new Date();
            document.getElementById('live-clock').innerText = now.toLocaleTimeString();
        }, 1000);

        // Data Fetching
        // Security Configuration
        async function loadData() {
            await Promise.all([fetchLogs(), fetchChartData(), fetchAnalysis(), fetchAlerts(), fetchStats()]);
        }

        async function fetchLogs() {
            const from = (currentPage - 1) * perPage;
            const to = from + perPage - 1;
            const data = await secureFetch('/api/logs?from=' + from + '&to=' + to);
            if (!data) return;
            const container = document.getElementById('log-stream');
            container.innerHTML = '';
            
            if(!data.length) { container.innerHTML = '<p style="text-align:center; color:#475569; padding:2rem;">No logs found.</p>'; return; }

            data.forEach(log => {
                const colors = { ERROR: '#f87171', WARNING: '#fbbf24', INFO: '#60a5fa', DEBUG: '#94a3b8', CRITICAL: '#ff4d4f' };
                const div = document.createElement('div');
                div.className = 'log-line';
                const time = new Date(log.timestamp).toLocaleTimeString();
                
                // SECURITY FIX: Using separate elements to prevent XSS
                const ts = document.createElement('span');
                ts.className = 'log-ts';
                ts.textContent = time;

                const lvl = document.createElement('span');
                lvl.className = 'log-level';
                lvl.style.color = colors[log.log_level] || '#94a3b8';
                lvl.textContent = '[' + log.log_level + ']';

                const src = document.createElement('span');
                src.style.cssText = 'color:#94a3b8; min-width:100px; overflow:hidden; text-overflow:ellipsis;';
                src.textContent = '[' + log.source + ']';

                const msg = document.createElement('span');
                msg.className = 'log-msg';
                msg.textContent = log.message;

                div.appendChild(ts);
                div.appendChild(lvl);
                div.appendChild(src);
                if(log.is_anomaly) {
                    const badge = document.createElement('span');
                    badge.className = 'anomaly-badge';
                    badge.textContent = 'ANOMALY';
                    div.appendChild(badge);
                }
                div.appendChild(msg);
                container.appendChild(div);
            });
            document.getElementById('page-info').innerText = 'Page ' + currentPage;
        }

        async function fetchChartData() {
            const data = await secureFetch('/api/chart_data');
            if (!data) return;
            drawDoughnut(data.levels);
            drawLine(data.timeline);
        }

        async function fetchAnalysis() {
            const data = await secureFetch('/api/analysis');
            if (!data) return;
            const container = document.getElementById('analysis-panel');
            container.innerHTML = '';
            if(!data.length) { container.innerHTML = '<p style="text-align:center; color:#475569; font-size:0.85rem; padding:2rem 0;">No AI analysis yet.</p>'; return; }

            data.slice(0, 8).forEach(a => {
                const div = document.createElement('div');
                div.className = 'ai-card';
                div.innerHTML = 
                    '<div style="display:flex; justify-content:space-between; margin-bottom:8px;">' +
                        '<span class="ai-severity sev-' + a.severity.toLowerCase() + '">' + a.severity + '</span>' +
                        '<span style="font-size:0.75rem; color:var(--text-muted);">' + Math.round(a.confidence_score * 100) + '% Confidence</span>' +
                    '</div>' +
                    '<p style="font-size:0.85rem; margin-bottom:8px;"><strong>Root Cause:</strong> ' + a.root_cause + '</p>' +
                    '<div style="font-size:0.8rem; color:#94a3b8;">' +
                        '<strong>Fix:</strong> ' +
                        '<ul style="margin-top:4px; padding-left:20px; list-style-type: disc;">' +
                            a.recommended_actions.map(function(act) { return '<li>' + act + '</li>'; }).join('') +
                        '</ul>' +
                    '</div>';
                container.appendChild(div);
            });
        }

        async function fetchAlerts() {
            const data = await secureFetch('/api/alerts');
            if (!data) return;
            const container = document.getElementById('alerts-panel');
            container.innerHTML = '';
            if(!data.length) { container.innerHTML = '<p style="text-align:center; color:var(--text-muted); font-size:0.85rem; padding:2rem 0;">No active threats 🛡️</p>'; return; }

            data.forEach(alert => {
                const div = document.createElement('div');
                div.className = 'alert-item alert-' + alert.severity.toLowerCase();
                div.innerHTML = 
                    '<div style="font-weight:700; font-size:0.8rem; margin-bottom:4px; color: ' + (alert.severity === 'Critical' ? '#f87171' : '#fdba74') + '">' + alert.severity.toUpperCase() + '</div>' +
                    '<p style="font-size:0.85rem; color:#cbd5e1;">' + alert.message + '</p>';
                container.appendChild(div);
            });
        }

        async function fetchStats() {
            const data = await secureFetch('/api/stats');
            if (!data) return;
            document.getElementById('stat-total').innerText = data.total_logs.toLocaleString();
            document.getElementById('stat-anomalies').innerText = data.anomalies.toLocaleString();
            document.getElementById('stat-analyzed').innerText = data.analyzed.toLocaleString();
            document.getElementById('stat-alerts').innerText = data.alerts.toLocaleString();
        }

        function changePage(dir) {
            const newPage = currentPage + dir;
            if(newPage > 0) { currentPage = newPage; fetchLogs(); }
        }

        // Chart Drawing
        function drawDoughnut(levels) {
            const ctx = document.getElementById('doughnutChart').getContext('2d');
            if(dChart) dChart.destroy();
            dChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(levels),
                    datasets: [{ data: Object.values(levels), backgroundColor: ['#3b82f6', '#eab308', '#ef4444', '#991b1b', '#64748b'], borderWidth: 0 }]
                },
                options: { responsive: true, maintainAspectRatio: false, cutout: '70%', plugins: { legend: { position: 'right', labels: { color: '#cbd5e1', boxWidth: 12, padding: 15 } } } }
            });
        }

        function drawLine(timeline) {
            const ctx = document.getElementById('lineChart').getContext('2d');
            if(lChart) lChart.destroy();
            const gradient = ctx.createLinearGradient(0, 0, 0, 200);
            gradient.addColorStop(0, 'rgba(239, 68, 68, 0.5)');
            gradient.addColorStop(1, 'rgba(239, 68, 68, 0.0)');
            
            lChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: Object.keys(timeline),
                    datasets: [{ data: Object.values(timeline), borderColor: '#ef4444', backgroundColor: gradient, fill: true, tension: 0.4, pointRadius: 3, pointBackgroundColor: '#ef4444' }]
                },
                options: { responsive: true, maintainAspectRatio: false, scales: { x: { display: false }, y: { beginAtZero: true, ticks: { color: '#64748b', stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.05)' } } }, plugins: { legend: { display: false } } }
            });
        }

        // Init
        loadData();
        setInterval(loadData, 4000);
    </script>
</body>
</html>
'''

# --- PYTHON API ROUTES ---

@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/logs')
@require_api_key
def get_logs():
    from_val = request.args.get('from', 0, type=int)
    to_val = request.args.get('to', 39, type=int)
    
    if to_val - from_val > 100:
        to_val = from_val + 100
        
    res = supabase.table("logs").select("*").order("timestamp", desc=True).range(from_val, to_val).execute()
    return jsonify(res.data)

@app.route('/api/analysis')
@require_api_key
def get_analysis():
    res = supabase.table("analysis").select("*").order("created_at", desc=True).limit(20).execute()
    return jsonify(res.data)

@app.route('/api/alerts')
@require_api_key
def get_alerts():
    res = supabase.table("alerts").select("*").eq("is_resolved", False).order("created_at", desc=True).limit(10).execute()
    return jsonify(res.data)

@app.route('/api/stats')
@require_api_key
def get_stats():
    logs_count = supabase.table("logs").select("id", count="exact").execute().count
    alerts_count = supabase.table("alerts").select("id", count="exact").eq("is_resolved", False).execute().count
    anomalies_count = supabase.table("logs").select("id", count="exact").eq("is_anomaly", True).execute().count
    analysis_count = supabase.table("analysis").select("id", count="exact").execute().count
    
    return jsonify({
        "total_logs": logs_count,
        "anomalies": anomalies_count,
        "analyzed": analysis_count,
        "alerts": alerts_count
    })

@app.route('/api/chart_data')
@require_api_key
def chart_data():
    res = supabase.table("logs").select("timestamp, log_level, is_anomaly").order("timestamp", desc=True).limit(200).execute()
    logs = res.data

    level_counts = {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0, "DEBUG": 0}
    anomaly_timeline = {}

    for log in logs:
        lvl = log.get("log_level", "INFO")
        if lvl in level_counts: level_counts[lvl] += 1
        
        if log.get("is_anomaly"):
            ts = log.get("timestamp", "")[:16] 
            anomaly_timeline[ts] = anomaly_timeline.get(ts, 0) + 1

    sorted_timeline = dict(sorted(anomaly_timeline.items()))
    return jsonify({ "levels": level_counts, "timeline": sorted_timeline })

@app.route('/api/ingest', methods=['POST'])
@require_api_key
def ingest_log():
    """Real companies send logs to this endpoint"""
    data = request.json
    logs = data if isinstance(data, list) else [data]
    
    for log in logs:
        raw_str = log.get('message', str(log))
        parsed = parser.parse(raw_str)
        
        level = log.get('level', parsed.level)
        source = log.get('source', log.get('service', parsed.source))
        is_anomaly = level in ['ERROR', 'CRITICAL'] or parsed.is_anomaly
        
        supabase.table("logs").insert({
            "timestamp": parsed.timestamp.isoformat(),
            "log_level": level,
            "message": parsed.message,
            "source": source,
            "is_anomaly": is_anomaly,
            "structured_data": log
        }).execute()
        
    return jsonify({"status": "ingested", "count": len(logs)}), 201

if __name__ == '__main__':
    print("\n" + "="*40)
    print("🛡️  SENTINEL AI COMMAND CENTER")
    print("🚀 Open http://localhost:5000")
    print("="*40 + "\n")
    app.run(debug=True, port=5000)
