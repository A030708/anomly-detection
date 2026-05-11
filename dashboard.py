import os
from flask import Flask, render_template_string, jsonify, request, session, redirect, url_for
from supabase import create_client, Client
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24) 

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# --- SECURITY MODULE ---
WEBHOOK_API_KEY = "sentinel-secure-key-123"
DEMO_USER = {"admin": "password"}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        provided_key = request.headers.get('X-API-Key')
        if provided_key != WEBHOOK_API_KEY:
            return jsonify({"error": "Unauthorized webhook"}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- LOGIN PAGE HTML ---
LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sentinel AI Login</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body { margin:0; padding:0; background:#020617; color:#f8fafc; font-family:'Inter',sans-serif; display:flex; height:100vh; align-items:center; justify-content:center; }
        .login-box { background:#0f172a; border:1px solid #334155; padding:2.5rem; border-radius:1rem; width:350px; box-shadow: 0 0 20px rgba(6,182,212,0.1); }
        .logo { text-align:center; font-size:1.5rem; font-weight:700; margin-bottom:2rem; color:#06b6d4; }
        input { width:100%; padding:0.75rem; margin-bottom:1rem; background:#1e293b; border:1px solid #334155; color:white; border-radius:0.5rem; box-sizing:border-box; }
        input:focus { outline:none; border-color:#06b6d4; }
        button { width:100%; padding:0.75rem; background:#06b6d4; color:black; font-weight:600; border:none; border-radius:0.5rem; cursor:pointer; }
        button:hover { background:#0891b2; }
        .error { color:#ef4444; font-size:0.85rem; text-align:center; margin-top:1rem; }
    </style>
</head>
<body>
    <div class="login-box">
        <div class="logo">🛡️ SENTINEL AI</div>
        {% if error %}<div class="error">Invalid credentials. Access denied.</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">AUTHENTICATE</button>
        </form>
    </div>
</body>
</html>
'''

# --- DASHBOARD HTML (Premium UI) ---
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Log Intelligence | Command Center</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --bg-main: #020617; --bg-card: #0f172a; --border: #1e293b; --text-main: #f8fafc; --text-muted: #64748b; --accent-cyan: #06b6d4; --accent-red: #ef4444; --accent-yellow: #f59e0b; --accent-green: #10b981; --accent-purple: #8b5cf6; }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: var(--bg-main); color: var(--text-main); font-family: 'Inter', sans-serif; }
        .navbar { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(12px); border-bottom: 1px solid var(--border); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 50; }
        .logo { font-size: 1.25rem; font-weight: 700; display: flex; align-items: center; gap: 0.75rem; }
        .logo i { color: var(--accent-cyan); text-shadow: 0 0 10px rgba(6, 182, 212, 0.5); }
        .status-badge { display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; color: var(--text-muted); }
        .pulse-dot { width: 8px; height: 8px; background: var(--accent-green); border-radius: 50%; box-shadow: 0 0 8px var(--accent-green); animation: pulse 2s infinite; }
        @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(1.2); } 100% { opacity: 1; transform: scale(1); } }
        .dashboard-container { padding: 1.5rem 2rem; display: grid; gap: 1.5rem; }
        .card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 0.75rem; overflow: hidden; }
        .card-header { padding: 1rem 1.25rem; border-bottom: 1px solid var(--border); font-weight: 600; display: flex; justify-content: space-between; align-items: center; font-size: 0.95rem; }
        .card-body { padding: 1.25rem; }
        .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; }
        .kpi-value { font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem; }
        .kpi-label { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; }
        .main-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; }
        .chart-sub-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
        .terminal { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; height: 450px; overflow-y: auto; background: #030712; padding: 1rem; }
        .terminal::-webkit-scrollbar { width: 6px; }
        .terminal::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
        .log-line { padding: 0.5rem; border-bottom: 1px solid rgba(30, 41, 59, 0.5); display: flex; gap: 1rem; }
        .log-ts { color: var(--text-muted); white-space: nowrap; }
        .log-level { font-weight: 600; min-width: 60px; }
        .log-msg { color: #cbd5e1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .anomaly-badge { color: var(--accent-yellow); font-size: 0.7rem; border: 1px solid var(--accent-yellow); padding: 0 4px; border-radius: 4px; height: fit-content; }
        .alert-list { max-height: 250px; overflow-y: auto; }
        .alert-item { padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 0.75rem; border-left: 4px solid; }
        .alert-critical { background: rgba(239, 68, 68, 0.1); border-color: var(--accent-red); }
        .ai-card { padding: 1rem; border-radius: 0.5rem; margin-bottom: 0.75rem; background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.2); }
        .ai-severity { font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 9999px; }
        .sev-critical { background: rgba(239,68,68,0.2); color: #fca5a5; }
        .pagination { display: flex; justify-content: center; gap: 0.5rem; padding: 1rem; border-top: 1px solid var(--border); }
        .btn { padding: 0.5rem 1rem; border-radius: 0.375rem; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-main); cursor: pointer; text-decoration: none; }
        .btn:hover { background: #1e293b; }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo"><i class="fa-solid fa-shield-halved"></i><span>SENTINEL AI</span></div>
        <div class="status-badge">
            <div class="pulse-dot"></div>
            <span>System Online</span>
            <span style="margin-left: 1rem; color: var(--text-main);" id="live-clock">--:--:--</span>
            <a href="/logout" class="btn" style="margin-left: 1rem; padding: 0.25rem 0.75rem; font-size: 0.8rem;">Logout</a>
        </div>
    </div>
    <div class="dashboard-container">
        <div class="kpi-grid">
            <div class="card"><div class="card-body"><div class="kpi-value" id="stat-total">0</div><div class="kpi-label">Total Ingested</div></div></div>
            <div class="card"><div class="card-body"><div class="kpi-value" style="color: var(--accent-yellow);" id="stat-anomalies">0</div><div class="kpi-label">Anomalies Flagged</div></div></div>
            <div class="card"><div class="card-body"><div class="kpi-value" style="color: var(--accent-purple);" id="stat-analyzed">0</div><div class="kpi-label">AI Analyzed</div></div></div>
            <div class="card"><div class="card-body"><div class="kpi-value" style="color: var(--accent-red);" id="stat-alerts">0</div><div class="kpi-label">Active Alerts</div></div></div>
        </div>
        <div class="main-grid">
            <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                <div class="chart-sub-grid">
                    <div class="card"><div class="card-header">Log Distribution</div><div class="card-body" style="height: 200px; display:flex; align-items:center; justify-content:center;"><canvas id="doughnutChart"></canvas></div></div>
                    <div class="card"><div class="card-header">Anomaly Spikes</div><div class="card-body" style="height: 200px;"><canvas id="lineChart"></canvas></div></div>
                </div>
                <div class="card" style="flex: 1;">
                    <div class="card-header"><span><i class="fa-solid fa-terminal" style="color:var(--accent-green); margin-right:8px;"></i>Live Log Stream</span><span id="page-info" style="font-size:0.8rem; color:var(--text-muted);">Page 1</span></div>
                    <div id="log-stream" class="terminal"></div>
                    <div class="pagination">
                        <button class="btn" onclick="changePage(-1)">Prev</button>
                        <button class="btn" onclick="changePage(1)">Next</button>
                    </div>
                </div>
            </div>
            <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                <div class="card">
                    <div class="card-header" style="background: rgba(239,68,68,0.05); color: #fca5a5;">Threat Alerts</div>
                    <div class="card-body alert-list" id="alerts-panel"><p style="text-align:center; color:var(--text-muted); font-size:0.85rem; padding:2rem 0;">No active threats 🛡️</p></div>
                </div>
                <div class="card" style="flex: 1;">
                    <div class="card-header" style="background: rgba(139,92,246,0.05); color: #c4b5fd;">AI Intelligence Feed</div>
                    <div class="card-body alert-list" id="analysis-panel" style="max-height: 450px;"><p style="text-align:center; color:var(--text-muted); font-size:0.85rem; padding:2rem 0;">Waiting for anomalies...</p></div>
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        let currentPage = 1; const perPage = 40; let dChart, lChart;
        setInterval(() => { document.getElementById('live-clock').innerText = new Date().toLocaleTimeString(); }, 1000);
        
        // Cookie Auth for internal API calls
        async function secureFetch(url) { return fetch(url).then(r => r.json()); }

        async function loadData() { await Promise.all([fetchLogs(), fetchChartData(), fetchAnalysis(), fetchAlerts(), fetchStats()]); }

        async function fetchLogs() {
            const from = (currentPage - 1) * perPage; const to = from + perPage - 1;
            const data = await secureFetch(`/api/logs?from=${from}&to=${to}`);
            const container = document.getElementById('log-stream'); container.innerHTML = '';
            if(!data.length) { container.innerHTML = '<p style="text-align:center; color:#475569; padding:2rem;">No logs found.</p>'; return; }
            data.forEach(log => {
                const colors = { ERROR: '#f87171', WARNING: '#fbbf24', INFO: '#60a5fa', DEBUG: '#94a3b8', CRITICAL: '#ff4d4f' };
                const div = document.createElement('div'); div.className = 'log-line';
                const time = new Date(log.timestamp).toLocaleTimeString();
                div.innerHTML = `<span class="log-ts">${time}</span><span class="log-level" style="color: ${colors[log.log_level]}">[${log.log_level}]</span><span style="color:#94a3b8; min-width:100px;">[${log.source}]</span>${log.is_anomaly ? '<span class="anomaly-badge">ANOMALY</span>' : '<span style="width:60px"></span>'}<span class="log-msg"></span>`;
                div.querySelector('.log-msg').textContent = log.message; // XSS Safe
                container.appendChild(div);
            });
            document.getElementById('page-info').innerText = `Page ${currentPage}`;
        }

        async function fetchChartData() {
            const data = await secureFetch('/api/chart_data');
            const ctx1 = document.getElementById('doughnutChart').getContext('2d');
            if(dChart) dChart.destroy();
            dChart = new Chart(ctx1, { type: 'doughnut', data: { labels: Object.keys(data.levels), datasets: [{ data: Object.values(data.levels), backgroundColor: ['#3b82f6', '#eab308', '#ef4444', '#991b1b', '#64748b'], borderWidth: 0 }] }, options: { responsive: true, maintainAspectRatio: false, cutout: '70%', plugins: { legend: { position: 'right', labels: { color: '#cbd5e1' } } } } });
            const ctx2 = document.getElementById('lineChart').getContext('2d');
            if(lChart) lChart.destroy();
            const gradient = ctx2.createLinearGradient(0, 0, 0, 200); gradient.addColorStop(0, 'rgba(239, 68, 68, 0.5)'); gradient.addColorStop(1, 'rgba(239, 68, 68, 0.0)');
            lChart = new Chart(ctx2, { type: 'line', data: { labels: Object.keys(data.timeline), datasets: [{ data: Object.values(data.timeline), borderColor: '#ef4444', backgroundColor: gradient, fill: true, tension: 0.4, pointRadius: 3 }] }, options: { responsive: true, maintainAspectRatio: false, scales: { x: { display: false }, y: { beginAtZero: true, ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } } }, plugins: { legend: { display: false } } } });
        }

        async function fetchAnalysis() {
            const data = await secureFetch('/api/analysis');
            const container = document.getElementById('analysis-panel'); container.innerHTML = '';
            if(!data.length) { container.innerHTML = '<p style="text-align:center; color:#475569; padding:2rem 0;">No AI analysis yet.</p>'; return; }
            data.slice(0, 8).forEach(a => {
                const div = document.createElement('div'); div.className = 'ai-card';
                div.innerHTML = `<div style="display:flex; justify-content:space-between; margin-bottom:8px;"><span class="ai-severity sev-${a.severity.toLowerCase()}">${a.severity}</span><span style="font-size:0.75rem; color:var(--text-muted);">${Math.round(a.confidence_score * 100)}% Conf</span></div><p style="font-size:0.85rem; margin-bottom:8px;"><strong>Cause:</strong> ${a.root_cause}</p><div style="font-size:0.8rem; color:#94a3b8;"><strong>Fix:</strong> <ul style="margin-top:4px; padding-left:20px;">${a.recommended_actions.map(act => `<li>${act}</li>`).join('')}</ul></div>`;
                container.appendChild(div);
            });
        }

        async function fetchAlerts() {
            const data = await secureFetch('/api/alerts');
            const container = document.getElementById('alerts-panel'); container.innerHTML = '';
            if(!data.length) { container.innerHTML = '<p style="text-align:center; color:var(--text-muted); padding:2rem 0;">No active threats 🛡️</p>'; return; }
            data.forEach(alert => {
                const div = document.createElement('div'); div.className = `alert-item alert-${alert.severity.toLowerCase()}`;
                div.innerHTML = `<div style="font-weight:700; font-size:0.8rem; margin-bottom:4px; color: ${alert.severity==='Critical'?'#f87171':'#fdba74'}">${alert.severity}</div><p style="font-size:0.85rem; color:#cbd5e1;">${alert.message}</p>`;
                container.appendChild(div);
            });
        }

        async function fetchStats() {
            const data = await secureFetch('/api/stats');
            document.getElementById('stat-total').innerText = data.total_logs.toLocaleString();
            document.getElementById('stat-anomalies').innerText = data.anomalies.toLocaleString();
            document.getElementById('stat-analyzed').innerText = data.analyzed.toLocaleString();
            document.getElementById('stat-alerts').innerText = data.alerts.toLocaleString();
        }

        function changePage(dir) { const p = currentPage + dir; if(p > 0) { currentPage = p; fetchLogs(); } }
        loadData(); setInterval(loadData, 4000);
    </script>
</body>
</html>
'''

# --- ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        if DEMO_USER.get(user) == pwd:
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template_string(LOGIN_HTML, error=True)
    return render_template_string(LOGIN_HTML, error=False)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/ingest', methods=['POST'])
@require_api_key
def ingest_log():
    data = request.json
    logs = data if isinstance(data, list) else [data]
    for log in logs:
        level = log.get('level', 'INFO').upper()
        is_anomaly = level in ['ERROR', 'CRITICAL']
        supabase.table("logs").insert({
            "log_level": level,
            "message": log.get('message', ''),
            "source": log.get('source', 'unknown'),
            "is_anomaly": is_anomaly,
            "structured_data": log
        }).execute()
    return jsonify({"status": "ingested"}), 201

@app.route('/api/logs')
@login_required
def get_logs():
    from_val = request.args.get('from', 0, type=int)
    to_val = request.args.get('to', 39, type=int)
    if to_val - from_val > 100: to_val = from_val + 100
    res = supabase.table("logs").select("*").order("timestamp", desc=True).range(from_val, to_val).execute()
    return jsonify(res.data)

@app.route('/api/analysis')
@login_required
def get_analysis():
    res = supabase.table("analysis").select("*").order("created_at", desc=True).limit(20).execute()
    return jsonify(res.data)

@app.route('/api/alerts')
@login_required
def get_alerts():
    res = supabase.table("alerts").select("*").eq("is_resolved", False).order("created_at", desc=True).limit(10).execute()
    return jsonify(res.data)

@app.route('/api/stats')
@login_required
def get_stats():
    l = supabase.table("logs").select("id", count="exact").execute()
    a = supabase.table("logs").select("id", count="exact").eq("is_anomaly", True).execute()
    an = supabase.table("analysis").select("id", count="exact").execute()
    al = supabase.table("alerts").select("id", count="exact").eq("is_resolved", False).execute()
    return jsonify({"total_logs": l.count, "anomalies": a.count, "analyzed": an.count, "alerts": al.count})

@app.route('/api/chart_data')
@login_required
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
    return jsonify({ "levels": level_counts, "timeline": dict(sorted(anomaly_timeline.items())) })

if __name__ == '__main__':
    print("\n🛡️  SENTINEL AI SECURE COMMAND CENTER")
    print("🔒 Login -> Username: admin | Password: password")
    print("🚀 Open http://localhost:5000\n")
    app.run(debug=True, port=5000)
