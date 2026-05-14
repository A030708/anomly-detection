import os, csv, io, smtplib
from flask import Flask, render_template_string, jsonify, request, session, redirect, url_for, Response
from flask_socketio import SocketIO, emit
from supabase import create_client, Client
from dotenv import load_dotenv
from functools import wraps
import threading
import time
import json
from groq import Groq
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


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
        is_github = request.headers.get('User-Agent', '').startswith('GitHub-Hookshot')
        if not is_github and provided_key != WEBHOOK_API_KEY:
            return jsonify({"error": "Unauthorized webhook"}), 401
        return f(*args, **kwargs)
    return decorated_function

def send_alert_email(subject, html_body):
    sender = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")
    to_email = os.getenv("ALERT_RECIPIENT", sender)
    if not sender or not password or not to_email: return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"], msg["From"], msg["To"] = subject, sender, to_email
        msg.attach(MIMEText(html_body, "html"))
        s = smtplib.SMTP("smtp.gmail.com", 587); s.starttls()
        s.login(sender, password)
        s.sendmail(sender, to_email, msg.as_string()); s.quit()
        print(f"   📧 [Email] Alert sent to {to_email}")
    except Exception as e:
        print(f"   ⚠️ [Email] Error: {e}")

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
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
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
        .btn { padding: 0.5rem 1rem; border-radius: 0.375rem; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-main); cursor: pointer; text-decoration: none; font-size: 0.85rem; }
        .btn:hover { background: #1e293b; }
        .btn-sm { padding: 0.25rem 0.5rem; font-size: 0.7rem; }
        .btn-green { border-color: var(--accent-green); color: var(--accent-green); }
        .btn-green:hover { background: rgba(16,185,129,0.15); }
        .btn-cyan { border-color: var(--accent-cyan); color: var(--accent-cyan); }
        .search-bar { display: flex; gap: 0.5rem; padding: 0.75rem 1.25rem; border-bottom: 1px solid var(--border); }
        .search-bar input { flex: 1; padding: 0.5rem 0.75rem; background: #030712; border: 1px solid var(--border); color: white; border-radius: 0.375rem; font-size: 0.8rem; font-family: 'Inter', sans-serif; }
        .search-bar input:focus { outline: none; border-color: var(--accent-cyan); }
        .search-bar select { padding: 0.5rem; background: #030712; border: 1px solid var(--border); color: white; border-radius: 0.375rem; font-size: 0.8rem; }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo"><i class="fa-solid fa-shield-halved"></i><span>SENTINEL AI</span></div>
        <div class="status-badge">
            <div class="pulse-dot"></div>
            <span>System Online</span>
            <span style="margin-left: 1rem; color: var(--text-main);" id="live-clock">--:--:--</span>
            <a href="/analytics" class="btn btn-sm" style="margin-left: 0.75rem;"><i class="fa-solid fa-chart-line" style="margin-right:4px"></i>Analytics</a>
            <a href="/api/export/csv" class="btn btn-sm btn-cyan" style="margin-left: 0.5rem;"><i class="fa-solid fa-download" style="margin-right:4px"></i>CSV</a>
            <a href="/logout" class="btn btn-sm" style="margin-left: 0.5rem;">Logout</a>
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
                    <div class="search-bar">
                        <input type="text" id="search-input" placeholder="Search logs..." onkeyup="if(event.key==='Enter')searchLogs()">
                        <select id="level-filter" onchange="searchLogs()">
                            <option value="">All Levels</option>
                            <option value="INFO">INFO</option>
                            <option value="WARNING">WARNING</option>
                            <option value="ERROR">ERROR</option>
                            <option value="CRITICAL">CRITICAL</option>
                            <option value="DEBUG">DEBUG</option>
                        </select>
                        <button class="btn btn-sm" onclick="searchLogs()"><i class="fa-solid fa-search"></i></button>
                        <button class="btn btn-sm" onclick="clearSearch()" title="Clear"><i class="fa-solid fa-xmark"></i></button>
                    </div>
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
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
    <script>
        let currentPage = 1; const perPage = 40; let dChart, lChart;
        setInterval(() => { document.getElementById('live-clock').innerText = new Date().toLocaleTimeString(); }, 1000);

        // --- Socket.IO Real-Time Connection ---
        const socket = io();

        socket.on('connect', () => {
            console.log('⚡ Real-time connected');
            document.querySelector('.pulse-dot').style.background = '#10b981';
        });

        socket.on('disconnect', () => {
            console.log('🔌 Real-time disconnected');
            document.querySelector('.pulse-dot').style.background = '#ef4444';
        });

        // When a new log arrives, prepend it instantly to the terminal
        socket.on('new_log', (log) => {
            const container = document.getElementById('log-stream');
            const colors = { ERROR: '#f87171', WARNING: '#fbbf24', INFO: '#60a5fa', DEBUG: '#94a3b8', CRITICAL: '#ff4d4f' };
            const div = document.createElement('div');
            div.className = 'log-line';
            div.style.animation = 'fadeIn 0.4s ease';
            const time = new Date(log.timestamp).toLocaleTimeString();
            div.innerHTML = `<span class="log-ts">${time}</span><span class="log-level" style="color:${colors[log.log_level]}">[${log.log_level}]</span><span style="color:#94a3b8; min-width:100px;">[${log.source}]</span>${log.is_anomaly ? '<span class="anomaly-badge">ANOMALY</span>' : '<span style="width:60px"></span>'}<span class="log-msg"></span>`;
            div.querySelector('.log-msg').textContent = log.message;
            container.insertBefore(div, container.firstChild);
            // Keep terminal from growing too large
            while (container.children.length > 80) container.removeChild(container.lastChild);
            fetchStats(); // Update KPI counters
        });

        // When AI detects a threat, show alert banner instantly
        socket.on('new_alert', (alert) => {
            const container = document.getElementById('alerts-panel');
            // Remove "No active threats" placeholder if present
            const placeholder = container.querySelector('p');
            if (placeholder) placeholder.remove();
            const div = document.createElement('div');
            div.className = `alert-item alert-critical`;
            div.style.animation = 'fadeIn 0.4s ease';
            div.innerHTML = `<div style="display:flex; justify-content:space-between; align-items:center;"><div><div style="font-weight:700; font-size:0.8rem; margin-bottom:4px; color:#f87171">🚨 ${alert.severity}</div><p style="font-size:0.85rem; color:#cbd5e1;">${alert.message}</p></div></div>`;
            container.insertBefore(div, container.firstChild);
            fetchStats();
        });

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
            if(!data.length) { container.innerHTML = '<p style="text-align:center; color:var(--text-muted); padding:2rem 0;">No active threats &#x1f6e1;&#xfe0f;</p>'; return; }
            data.forEach(alert => {
                const div = document.createElement('div'); div.className = `alert-item alert-${alert.severity.toLowerCase()}`;
                div.innerHTML = `<div style="display:flex; justify-content:space-between; align-items:center;"><div><div style="font-weight:700; font-size:0.8rem; margin-bottom:4px; color: ${alert.severity==='Critical'?'#f87171':'#fdba74'}">${alert.severity}</div><p style="font-size:0.85rem; color:#cbd5e1;">${alert.message}</p></div><button class="btn btn-sm btn-green" onclick="resolveAlert(${alert.id})">&#x2713; Resolve</button></div>`;
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

        async function resolveAlert(id) {
            await fetch(`/api/alerts/${id}/resolve`, {method:'POST'});
            fetchAlerts(); fetchStats();
        }

        async function searchLogs() {
            const q = document.getElementById('search-input').value;
            const level = document.getElementById('level-filter').value;
            let url = '/api/logs/search?';
            if(q) url += `q=${encodeURIComponent(q)}&`;
            if(level) url += `level=${level}`;
            const data = await secureFetch(url);
            const container = document.getElementById('log-stream'); container.innerHTML = '';
            if(!data.length) { container.innerHTML = '<p style="text-align:center; color:#475569; padding:2rem;">No results.</p>'; return; }
            data.forEach(log => {
                const colors = { ERROR: '#f87171', WARNING: '#fbbf24', INFO: '#60a5fa', DEBUG: '#94a3b8', CRITICAL: '#ff4d4f' };
                const div = document.createElement('div'); div.className = 'log-line';
                div.innerHTML = `<span class="log-ts">${new Date(log.timestamp).toLocaleTimeString()}</span><span class="log-level" style="color: ${colors[log.log_level]}">[${log.log_level}]</span><span style="color:#94a3b8; min-width:100px;">[${log.source}]</span>${log.is_anomaly ? '<span class="anomaly-badge">ANOMALY</span>' : '<span style="width:60px"></span>'}<span class="log-msg"></span>`;
                div.querySelector('.log-msg').textContent = log.message;
                container.appendChild(div);
            });
            document.getElementById('page-info').innerText = 'Search Results';
        }

        function clearSearch() {
            document.getElementById('search-input').value = '';
            document.getElementById('level-filter').value = '';
            currentPage = 1; fetchLogs();
        }

        function changePage(dir) { const p = currentPage + dir; if(p > 0) { currentPage = p; fetchLogs(); } }

        // Initial load + slow poll for charts only (30s fallback)
        loadData();
        setInterval(() => { fetchChartData(); fetchAnalysis(); }, 30000);
    </script>
</body>
</html>
'''

# --- ANALYTICS PAGE HTML ---
ANALYTICS_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentinel AI | Analytics</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root{--bg-main:#020617;--bg-card:#0f172a;--border:#1e293b;--text-main:#f8fafc;--text-muted:#64748b;--cyan:#06b6d4;--red:#ef4444;--yellow:#f59e0b;--green:#10b981;--purple:#8b5cf6}
        *{box-sizing:border-box;margin:0;padding:0}
        body{background:var(--bg-main);color:var(--text-main);font-family:'Inter',sans-serif}
        .navbar{background:rgba(15,23,42,0.9);backdrop-filter:blur(12px);border-bottom:1px solid var(--border);padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:50}
        .logo{font-size:1.2rem;font-weight:700;display:flex;align-items:center;gap:0.75rem;color:var(--cyan)}
        .btn{padding:0.4rem 0.9rem;border-radius:0.375rem;border:1px solid var(--border);background:var(--bg-card);color:var(--text-main);cursor:pointer;text-decoration:none;font-size:0.85rem}
        .btn:hover{background:#1e293b}
        .page{padding:2rem;display:grid;gap:1.5rem}
        .kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:1.5rem}
        .kpi-card{background:var(--bg-card);border:1px solid var(--border);border-radius:0.75rem;padding:1.25rem;animation:fadeUp 0.4s ease both}
        .kpi-val{font-size:2rem;font-weight:700}
        .kpi-lbl{font-size:0.75rem;color:var(--text-muted);text-transform:uppercase;margin-top:4px}
        .kpi-sub{font-size:0.8rem;margin-top:8px;color:var(--text-muted)}
        .chart-grid{display:grid;grid-template-columns:2fr 1fr;gap:1.5rem}
        .chart-row{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem}
        .card{background:var(--bg-card);border:1px solid var(--border);border-radius:0.75rem;overflow:hidden;animation:fadeUp 0.4s ease both}
        .card-header{padding:1rem 1.25rem;border-bottom:1px solid var(--border);font-weight:600;font-size:0.9rem;display:flex;align-items:center;gap:0.5rem}
        .card-body{padding:1.25rem}
        .source-row{display:flex;align-items:center;gap:0.75rem;padding:0.5rem 0;border-bottom:1px solid var(--border)}
        .source-bar-bg{flex:1;height:6px;background:#1e293b;border-radius:9999px;overflow:hidden}
        .source-bar{height:100%;background:var(--cyan);border-radius:9999px;transition:width 0.6s ease}
        @keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
    </style>
</head>
<body>
<div class="navbar">
    <div class="logo"><i class="fa-solid fa-chart-line"></i> Analytics</div>
    <div style="display:flex;gap:0.75rem;align-items:center;">
        <a href="/" class="btn"><i class="fa-solid fa-arrow-left" style="margin-right:4px"></i>Dashboard</a>
        <a href="/logout" class="btn">Logout</a>
    </div>
</div>
<div class="page">
    <div class="kpi-row">
        <div class="kpi-card" style="border-left:3px solid var(--cyan)">
            <div class="kpi-val" id="a-total" style="color:var(--cyan)">—</div>
            <div class="kpi-lbl">Total Logs</div>
            <div class="kpi-sub" id="a-total-sub"></div>
        </div>
        <div class="kpi-card" style="border-left:3px solid var(--yellow)">
            <div class="kpi-val" id="a-anomalies" style="color:var(--yellow)">—</div>
            <div class="kpi-lbl">Anomalies Detected</div>
            <div class="kpi-sub" id="a-anomaly-rate"></div>
        </div>
        <div class="kpi-card" style="border-left:3px solid var(--red)">
            <div class="kpi-val" id="a-critical" style="color:var(--red)">—</div>
            <div class="kpi-lbl">Critical Events</div>
            <div class="kpi-sub">Requires attention</div>
        </div>
        <div class="kpi-card" style="border-left:3px solid var(--green)">
            <div class="kpi-val" id="a-sources" style="color:var(--green)">—</div>
            <div class="kpi-lbl">Unique Sources</div>
            <div class="kpi-sub">Active integrations</div>
        </div>
    </div>
    <div class="chart-grid">
        <div class="card">
            <div class="card-header"><i class="fa-solid fa-chart-area" style="color:var(--cyan)"></i> 7-Day Log Volume Trend</div>
            <div class="card-body" style="height:280px"><canvas id="trendChart"></canvas></div>
        </div>
        <div class="card">
            <div class="card-header"><i class="fa-solid fa-circle-half-stroke" style="color:var(--purple)"></i> Severity Breakdown</div>
            <div class="card-body" style="height:280px;display:flex;align-items:center;justify-content:center"><canvas id="sevChart"></canvas></div>
        </div>
    </div>
    <div class="chart-row">
        <div class="card">
            <div class="card-header"><i class="fa-solid fa-tower-broadcast" style="color:var(--yellow)"></i> Top Log Sources</div>
            <div class="card-body" id="sources-list"></div>
        </div>
        <div class="card">
            <div class="card-header"><i class="fa-solid fa-chart-bar" style="color:var(--red)"></i> Anomalies by Hour</div>
            <div class="card-body" style="height:240px"><canvas id="hourChart"></canvas></div>
        </div>
    </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    let tC,sC,hC;
    const COLORS={INFO:'#3b82f6',WARNING:'#eab308',ERROR:'#ef4444',CRITICAL:'#991b1b',DEBUG:'#64748b'};
    async function loadAnalytics(){
        const d=await fetch('/api/analytics_data').then(r=>r.json());
        document.getElementById('a-total').innerText=d.total.toLocaleString();
        document.getElementById('a-total-sub').innerText=d.today_count+' today';
        document.getElementById('a-anomalies').innerText=d.anomaly_count.toLocaleString();
        document.getElementById('a-anomaly-rate').innerText=d.anomaly_rate+'% anomaly rate';
        document.getElementById('a-critical').innerText=d.critical_count.toLocaleString();
        document.getElementById('a-sources').innerText=d.source_count.toLocaleString();
        // Trend
        const c1=document.getElementById('trendChart').getContext('2d');
        if(tC)tC.destroy();
        const g=c1.createLinearGradient(0,0,0,280);g.addColorStop(0,'rgba(6,182,212,0.35)');g.addColorStop(1,'rgba(6,182,212,0)');
        tC=new Chart(c1,{type:'line',data:{labels:d.trend_labels,datasets:[{label:'All Logs',data:d.trend_all,borderColor:'#06b6d4',backgroundColor:g,fill:true,tension:0.4,pointRadius:4},{label:'Anomalies',data:d.trend_anomalies,borderColor:'#ef4444',backgroundColor:'transparent',fill:false,tension:0.4,pointRadius:3,borderDash:[4,4]}]},options:{responsive:true,maintainAspectRatio:false,scales:{x:{ticks:{color:'#64748b'},grid:{color:'rgba(255,255,255,0.04)'}},y:{beginAtZero:true,ticks:{color:'#64748b'},grid:{color:'rgba(255,255,255,0.04)'}}},plugins:{legend:{labels:{color:'#cbd5e1'}}}}});
        // Severity donut
        const c2=document.getElementById('sevChart').getContext('2d');
        if(sC)sC.destroy();
        const sk=Object.keys(d.severity),sv=Object.values(d.severity);
        sC=new Chart(c2,{type:'doughnut',data:{labels:sk,datasets:[{data:sv,backgroundColor:sk.map(k=>COLORS[k]||'#94a3b8'),borderWidth:0,hoverOffset:6}]},options:{responsive:true,maintainAspectRatio:false,cutout:'68%',plugins:{legend:{position:'bottom',labels:{color:'#cbd5e1',padding:12,font:{size:11}}}}}});
        // Top sources
        const sl=document.getElementById('sources-list');sl.innerHTML='';
        const mx=Math.max(...Object.values(d.sources),1);
        Object.entries(d.sources).slice(0,8).forEach(([src,cnt])=>{
            sl.innerHTML+=`<div class="source-row"><span style="min-width:130px;font-size:0.82rem;color:#94a3b8;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${src}</span><div class="source-bar-bg"><div class="source-bar" style="width:${Math.round(cnt/mx*100)}%"></div></div><span style="min-width:36px;text-align:right;font-size:0.82rem;font-weight:600">${cnt}</span></div>`;
        });
        // Hourly bar
        const c3=document.getElementById('hourChart').getContext('2d');
        if(hC)hC.destroy();
        const hg=c3.createLinearGradient(0,0,0,240);hg.addColorStop(0,'rgba(239,68,68,0.6)');hg.addColorStop(1,'rgba(239,68,68,0.05)');
        hC=new Chart(c3,{type:'bar',data:{labels:d.hour_labels,datasets:[{label:'Anomalies',data:d.hour_data,backgroundColor:hg,borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,scales:{x:{ticks:{color:'#64748b',maxRotation:0},grid:{display:false}},y:{beginAtZero:true,ticks:{color:'#64748b'},grid:{color:'rgba(255,255,255,0.04)'}}},plugins:{legend:{display:false}}}});
    }
    loadAnalytics();setInterval(loadAnalytics,30000);
</script>
</body></html>
'''

# --- AUTOMATED AI BACKGROUND WORKER ---
def auto_analyze_anomalies():
    """Runs in the background every 15 seconds to analyze new anomalies with LLM"""
    print("🧠 [AI Worker] Checking for new anomalies...")
    
    try:
        # 1. Find logs that are anomalies
        logs_res = supabase.table("logs") \
            .select("id, log_level, source, message") \
            .eq("is_anomaly", True) \
            .order("timestamp", desc=True) \
            .limit(10) \
            .execute()
        
        # 2. Get IDs that are already analyzed
        analysis_res = supabase.table("analysis").select("log_id").execute()
        analyzed_ids = {item['log_id'] for item in analysis_res.data}
        
        new_anomalies = [log for log in logs_res.data if log['id'] not in analyzed_ids]
        
        if new_anomalies:
            for log in new_anomalies:
                print(f"🤖 [AI Worker] Analyzing Log ID {log['id']} from {log['source']}...")
                
                try:
                    response = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": f"Analyze this log. Respond ONLY in JSON with keys: root_cause, severity (Critical/High/Medium/Low), recommended_actions (list). Log: {log['message']}"}],
                        temperature=0.1,
                        max_tokens=200,
                        response_format={"type": "json_object"}
                    )
                    result = json.loads(response.choices[0].message.content)
                except Exception as e:
                    print(f"   ⚠️ [AI Worker] LLM Error: {e}")
                    result = {"root_cause": "LLM Analysis Failed", "severity": "Low", "recommended_actions": ["Manual review required"]}
                
                # 3. Save Analysis
                supabase.table("analysis").insert({
                    "log_id": log['id'],
                    "root_cause": result.get("root_cause", "Unknown"),
                    "severity": result.get("severity", "Medium"),
                    "recommended_actions": result.get("recommended_actions", []),
                    "confidence_score": 0.9
                }).execute()
                
                # 4. Create Alert if needed
                if result.get("severity") in ["Critical", "High"]:
                    supabase.table("alerts").insert({
                        "log_id": log['id'],
                        "severity": result.get("severity"),
                        "message": f"[{log['source']}] {result.get('root_cause')}",
                        "is_resolved": False
                    }).execute()
                    print(f"   🚨 [AI Worker] ALERT CREATED: {result.get('severity')}")
                    # 🔴 REAL-TIME: push alert to all dashboards
                    socketio.emit('new_alert', {
                        "severity": result.get("severity"),
                        "message": f"[{log['source']}] {result.get('root_cause')}",
                        "root_cause": result.get("root_cause"),
                        "recommended_actions": result.get("recommended_actions", [])
                    })
                    # Send email alert
                    send_alert_email(
                        f"🚨 Sentinel AI Alert: {result.get('severity')}",
                        f"<h2>{result.get('severity')} Threat Detected</h2><p><b>Source:</b> {log['source']}</p><p><b>Root Cause:</b> {result.get('root_cause')}</p><p><b>Actions:</b></p><ul>{''.join(f'<li>{a}</li>' for a in result.get('recommended_actions',[]))}</ul>"
                    )
    except Exception as e:
        print(f"❌ [AI Worker] Global Error: {e}")

    threading.Timer(15.0, auto_analyze_anomalies).start()

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

@app.route('/api/ingest', methods=['GET', 'POST'], strict_slashes=False)
@require_api_key
def ingest_log():
    # Use silent=True to prevent 415 errors if content-type isn't application/json
    data = request.get_json(silent=True)
    
    # If it's not JSON, check if it's form data (like GitHub's x-www-form-urlencoded)
    if not data:
        if 'payload' in request.form:
            try:
                data = json.loads(request.form['payload'])
            except:
                data = request.form.to_dict()
        else:
            data = request.form.to_dict()

    if not data:
        data = {}
    logs_to_insert = []

    # CHECK 1: Is this from our Fake Flipkart? (It sends a simple dict)
    if 'level' in data and 'source' in data:
        logs_to_insert.append(data)
    
    # CHECK 2: Is this from GitHub? (It sends a complex dict with 'sender' and 'ref')
    elif 'sender' in data and ('ref' in data or 'pull_request' in data):
        action = request.headers.get('X-GitHub-Event', 'unknown')
        user = data.get('sender', {}).get('login', 'unknown_user')
        repo = data.get('repository', {}).get('name', 'unknown_repo')
        
        # Translate GitHub event into Sentinel log
        level = "INFO"
        message = ""
        
        if action == "push":
            branch = data.get('ref', '').replace('refs/heads/', '')
            commits = data.get('commits', [])
            message = f"[{user}] pushed {len(commits)} commit(s) to '{branch}' in {repo}"
            
            # Scan commit messages for dangerous actions
            for commit in commits:
                commit_msg = commit.get('message', '').lower()
                if any(word in commit_msg for word in ['password', 'secret', 'token', 'api_key', 'credentials']):
                    level = "CRITICAL"
                    message += f" | 🚨 POSSIBLE SECRET LEAK in commit: {commit_msg}"
                elif any(word in commit_msg for word in ['hotfix', 'urgent', 'force', 'hack']):
                    if level != "CRITICAL": level = "WARNING"
                    message += f" | ⚠️ Risky commit: {commit_msg}"
                    
        elif action == "delete":
            branch = data.get('ref', '').replace('refs/heads/', '')
            message = f"[{user}] DELETED branch '{branch}' in {repo}"
            level = "WARNING"
        elif action == "pull_request":
            pr_action = data.get('action', '')
            branch = data.get('pull_request', {}).get('base', {}).get('ref', 'unknown')
            message = f"[{user}] {pr_action} a Pull Request in {repo}"
            if pr_action == "closed" and data.get('pull_request', {}).get('merged'):
                message = f"[{user}] MERGED a Pull Request into '{branch}' in {repo}"
        
        if message:
            logs_to_insert.append({
                "level": level,
                "source": "github-webhook",
                "message": message,
                "is_anomaly": level in ['ERROR', 'CRITICAL']
            })

    # SAVE TO DATABASE
    for log in logs_to_insert:
        level = log.get('level', 'INFO').upper()
        is_anomaly = log.get('is_anomaly', level in ['ERROR', 'CRITICAL'])
        try:
            supabase.table("logs").insert({
                "log_level": level,
                "message": log.get('message', ''),
                "source": log.get('source', 'unknown'),
                "is_anomaly": is_anomaly,
                "structured_data": log
            }).execute()
            # 🔴 REAL-TIME: push new log to all connected dashboards instantly
            socketio.emit('new_log', {
                "log_level": level,
                "message": log.get('message', ''),
                "source": log.get('source', 'unknown'),
                "is_anomaly": is_anomaly,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"status": "ingested", "count": len(logs_to_insert)}), 201

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

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    supabase.table("alerts").update({"is_resolved": True}).eq("id", alert_id).execute()
    return jsonify({"status": "resolved"}), 200

@app.route('/api/logs/search')
@login_required
def search_logs():
    q = request.args.get('q', '')
    level = request.args.get('level', '')
    query = supabase.table("logs").select("*").order("timestamp", desc=True).limit(50)
    if level: query = query.eq("log_level", level)
    if q: query = query.ilike("message", f"%{q}%")
    return jsonify(query.execute().data)

@app.route('/api/export/csv')
@login_required
def export_csv():
    logs = supabase.table("logs").select("timestamp,log_level,source,message,is_anomaly").order("timestamp", desc=True).limit(1000).execute()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["timestamp","log_level","source","message","is_anomaly"])
    writer.writeheader()
    writer.writerows(logs.data)
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=sentinel_report.csv'})

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

@app.route('/analytics')
@login_required
def analytics_page():
    return render_template_string(ANALYTICS_HTML)

@app.route('/api/analytics_data')
@login_required
def analytics_data():
    from datetime import datetime, timedelta, timezone
    # Fetch last 1000 logs for aggregation
    res = supabase.table("logs").select("timestamp, log_level, source, is_anomaly").order("timestamp", desc=True).limit(1000).execute()
    logs = res.data

    # Totals
    total = len(logs)
    anomaly_count = sum(1 for l in logs if l.get("is_anomaly"))
    critical_count = sum(1 for l in logs if l.get("log_level") == "CRITICAL")
    anomaly_rate = round(anomaly_count / total * 100, 1) if total else 0

    # Unique sources
    sources_count = {}
    for l in logs:
        src = l.get("source", "unknown")
        sources_count[src] = sources_count.get(src, 0) + 1
    source_count = len(sources_count)
    sources_sorted = dict(sorted(sources_count.items(), key=lambda x: x[1], reverse=True))

    # Severity breakdown
    severity = {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0, "DEBUG": 0}
    for l in logs:
        lvl = l.get("log_level", "INFO")
        if lvl in severity: severity[lvl] += 1

    # 7-day trend
    today = datetime.now(timezone.utc).date()
    trend_labels, trend_all, trend_anomalies = [], [], []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.isoformat()
        trend_labels.append(day.strftime("%b %d"))
        day_logs = [l for l in logs if l.get("timestamp", "")[:10] == day_str]
        trend_all.append(len(day_logs))
        trend_anomalies.append(sum(1 for l in day_logs if l.get("is_anomaly")))

    # Today count
    today_count = trend_all[-1] if trend_all else 0

    # Anomalies by hour (last 24h)
    hour_data = [0] * 24
    hour_labels = [f"{h:02d}:00" for h in range(24)]
    for l in logs:
        ts = l.get("timestamp", "")
        if ts and l.get("is_anomaly"):
            try:
                hour = int(ts[11:13])
                hour_data[hour] += 1
            except: pass

    return jsonify({
        "total": total, "today_count": today_count,
        "anomaly_count": anomaly_count, "anomaly_rate": anomaly_rate,
        "critical_count": critical_count, "source_count": source_count,
        "severity": severity, "sources": sources_sorted,
        "trend_labels": trend_labels, "trend_all": trend_all,
        "trend_anomalies": trend_anomalies,
        "hour_labels": hour_labels, "hour_data": hour_data
    })

# --- START BACKGROUND AI WORKER ---
# This ensures the AI starts even when running on Render/Gunicorn
def start_ai_worker():
    print("🧠 [System] Starting AI Anomaly Analyzer...")
    threading.Thread(target=auto_analyze_anomalies, daemon=True).start()

# We use a simple check to make sure it only starts once per process
# This prevents it from starting twice in local debug mode
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not os.environ.get("FLASK_DEBUG"):
    start_ai_worker()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
