import os, json, time, threading, smtplib, hmac, hashlib
from flask import Flask, render_template_string, jsonify, request, session, redirect, url_for
from supabase import create_client, Client
from dotenv import load_dotenv
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from groq import Groq

load_dotenv()

app = Flask(__name__)
app.secret_key = "super_secret_saas_key_change_in_production"

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- HELPERS ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session: return redirect(url_for('auth_page'))
        return f(*args, **kwargs)
    return decorated

def send_email(subject, html_body, to_email):
    if not to_email: return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"], msg["From"], msg["To"] = subject, os.getenv("EMAIL_ADDRESS"), to_email
        msg.attach(MIMEText(html_body, "html"))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD"))
        server.sendmail(os.getenv("EMAIL_ADDRESS"), to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Email error: {e}")

# --- AUTH UI (Beautiful Login/Register) ---
AUTH_HTML = '''
<!DOCTYPE html>
<html><head><title>Sentinel AI SaaS</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
<style>
    body{margin:0;padding:0;background:#020617;color:#f8fafc;font-family:'Inter',sans-serif;display:flex;height:100vh;align-items:center;justify-content:center}
    .auth-container{background:#0f172a;border:1px solid #334155;border-radius:1rem;width:400px;padding:40px;box-shadow:0 0 30px rgba(6,182,212,0.1)}
    .logo{text-align:center;font-size:1.5rem;font-weight:700;color:#06b6d4;margin-bottom:30px}
    .tabs{display:flex;margin-bottom:25px;border-bottom:1px solid #334155}
    .tab{flex:1;text-align:center;padding:10px;cursor:pointer;color:#64748b;border-bottom:2px solid transparent;font-weight:600}
    .tab.active{color:#06b6d4;border-bottom-color:#06b6d4}
    .form-container{display:none}.form-container.active{display:block}
    input{width:100%;padding:12px;margin-bottom:15px;background:#1e293b;border:1px solid #334155;color:white;border-radius:8px;box-sizing:border-box;font-size:14px}
    input:focus{outline:none;border-color:#06b6d4}
    button{width:100%;padding:12px;background:#06b6d4;color:#020617;font-weight:700;border:none;border-radius:8px;cursor:pointer;font-size:14px}
    button:hover{background:#0891b2}
    .error{color:#f87171;font-size:13px;text-align:center;margin-top:10px;background:rgba(239,68,68,0.1);padding:10px;border-radius:5px}
    .hint{color:#475569;font-size:12px;text-align:center;margin-top:15px}
</style></head><body>
<div class="auth-container">
    <div class="logo">🛡️ SENTINEL AI</div>
    <div class="tabs">
        <div class="tab active" onclick="switchTab('login')">LOG IN</div>
        <div class="tab" onclick="switchTab('register')">REGISTER</div>
    </div>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    
    <div id="login-form" class="form-container active">
        <form method="POST" action="/auth?mode=login">
            <input type="email" name="email" placeholder="Official Email (e.g., you@company.com)" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">AUTHENTICATE</button>
        </form>
    </div>
    
    <div id="register-form" class="form-container">
        <form method="POST" action="/auth?mode=register">
            <input type="email" name="email" placeholder="Official Email (e.g., alice@target.com)" required>
            <input type="password" name="password" placeholder="Create Password" required>
            <button type="submit">CREATE WORKSPACE</button>
            <div class="hint">Workspace is auto-generated from your email domain!</div>
        </form>
    </div>
</div>
<script>
function switchTab(mode) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.form-container').forEach(f => f.classList.remove('active'));
    if(mode === 'login') {
        document.querySelectorAll('.tab')[0].classList.add('active');
        document.getElementById('login-form').classList.add('active');
    } else {
        document.querySelectorAll('.tab')[1].classList.add('active');
        document.getElementById('register-form').classList.add('active');
    }
}
// Keep tab active on error
{% if mode == 'register' %} switchTab('register'); {% endif %}
</script>
</body></html>'''

# --- DASHBOARD UI (Added Settings Modal) ---
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Command Center</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
:root{--bg-main:#020617;--bg-card:#0f172a;--border:#1e293b;--text-main:#f8fafc;--text-muted:#64748b;--accent-cyan:#06b6d4;--accent-red:#ef4444;--accent-yellow:#f59e0b;--accent-green:#10b981;--accent-purple:#8b5cf6}
*{box-sizing:border-box;margin:0;padding:0}body{background:var(--bg-main);color:var(--text-main);font-family:'Inter',sans-serif}
.navbar{background:rgba(15,23,42,0.8);backdrop-filter:blur(12px);border-bottom:1px solid var(--border);padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:50}
.logo{font-size:1.25rem;font-weight:700;display:flex;align-items:center;gap:.75rem}.logo i{color:var(--accent-cyan);text-shadow:0 0 10px rgba(6,182,212,0.5)}
.status-badge{display:flex;align-items:center;gap:.5rem;font-size:.875rem;color:var(--text-muted)}
.pulse-dot{width:8px;height:8px;background:var(--accent-green);border-radius:50%;box-shadow:0 0 8px var(--accent-green);animation:pulse 2s infinite}
@keyframes pulse{0%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(1.2)}100%{opacity:1;transform:scale(1)}}
.dash-container{padding:1.5rem 2rem;display:grid;gap:1.5rem}
.card{background:var(--bg-card);border:1px solid var(--border);border-radius:.75rem;overflow:hidden}
.card-header{padding:1rem 1.25rem;border-bottom:1px solid var(--border);font-weight:600;display:flex;justify-content:space-between;align-items:center;font-size:.95rem}
.card-body{padding:1.25rem}
.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1.5rem}
.kpi-value{font-size:1.75rem;font-weight:700;margin-bottom:.25rem}
.kpi-label{font-size:.8rem;color:var(--text-muted);text-transform:uppercase}
.main-grid{display:grid;grid-template-columns:2fr 1fr;gap:1.5rem}
.chart-sub-grid{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem}
.terminal{font-family:'JetBrains Mono',monospace;font-size:.8rem;height:450px;overflow-y:auto;background:#030712;padding:1rem}
.terminal::-webkit-scrollbar{width:6px}.terminal::-webkit-scrollbar-thumb{background:#334155;border-radius:3px}
.log-line{padding:.5rem;border-bottom:1px solid rgba(30,41,59,0.5);display:flex;gap:1rem}
.log-ts{color:var(--text-muted);white-space:nowrap}.log-level{font-weight:600;min-width:60px}
.log-msg{color:#cbd5e1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.anomaly-badge{color:var(--accent-yellow);font-size:.7rem;border:1px solid var(--accent-yellow);padding:0 4px;border-radius:4px;height:fit-content}
.alert-list{max-height:250px;overflow-y:auto}
.alert-item{padding:.75rem;border-radius:.5rem;margin-bottom:.75rem;border-left:4px solid;background:rgba(239,68,68,0.1);border-color:var(--accent-red)}
.ai-card{padding:1rem;border-radius:.5rem;margin-bottom:.75rem;background:rgba(139,92,246,0.05);border:1px solid rgba(139,92,246,0.2)}
.ai-severity{font-size:.7rem;font-weight:700;padding:2px 8px;border-radius:9999px;background:rgba(239,68,68,0.2);color:#fca5a5}
.pagination{display:flex;justify-content:center;gap:.5rem;padding:1rem;border-top:1px solid var(--border)}
.btn{padding:.5rem 1rem;border-radius:.375rem;border:1px solid var(--border);background:var(--bg-card);color:var(--text-main);cursor:pointer;text-decoration:none;font-size:14px}
.btn:hover{background:#1e293b}
.settings-modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:100;justify-content:center;align-items:center}
.settings-modal.active{display:flex}
.settings-box{background:var(--bg-card);border:1px solid var(--border);padding:2rem;border-radius:1rem;width:400px}
.settings-box input{width:100%;padding:10px;margin:10px 0;background:#1e293b;border:1px solid var(--border);color:white;border-radius:5px;box-sizing:border-box}
.settings-box button{width:100%;padding:10px;background:var(--accent-cyan);color:black;border:none;border-radius:5px;font-weight:bold;margin-top:10px;cursor:pointer}
</style></head><body>
<div class="navbar">
    <div class="logo"><i class="fa-solid fa-shield-halved"></i><span>SENTINEL AI</span></div>
    <div class="status-badge">
        <div class="pulse-dot"></div>
        <span style="color:var(--text-main)">Workspace: {{ workspace }}</span>
        <span style="margin-left:1rem;color:var(--text-main)" id="live-clock">--:--:--</span>
        <i class="fa-solid fa-gear" style="cursor:pointer;margin-left:1rem" onclick="toggleSettings()"></i>
        <a href="/logout" class="btn" style="margin-left:.5rem;padding:.25rem .75rem;font-size:.8rem">Logout</a>
    </div>
</div>

<!-- Settings Modal -->
<div class="settings-modal" id="settingsModal">
    <div class="settings-box">
        <h3 style="margin-bottom:20px">⚙️ Workspace Integrations</h3>
        <label style="font-size:12px;color:#94a3b8">Send Alert Emails To:</label>
        <input type="email" id="alertEmailInput" placeholder="security@company.com">
        <label style="font-size:12px;color:#94a3b8">Your API Key (Give this to your apps):</label>
        <input type="text" id="apiKeyInput" readonly style="color:var(--accent-cyan); cursor:not-allowed">
        <button onclick="saveSettings()">SAVE SETTINGS</button>
        <button onclick="toggleSettings()" style="background:transparent;border:1px solid var(--border);color:white;margin-top:5px">CLOSE</button>
    </div>
</div>

<div class="dash-container">
    <div class="kpi-grid">
        <div class="card"><div class="card-body"><div class="kpi-value" id="stat-total">0</div><div class="kpi-label">Total Ingested</div></div></div>
        <div class="card"><div class="card-body"><div class="kpi-value" style="color:var(--accent-yellow)" id="stat-anomalies">0</div><div class="kpi-label">Anomalies Flagged</div></div></div>
        <div class="card"><div class="card-body"><div class="kpi-value" style="color:var(--accent-purple)" id="stat-analyzed">0</div><div class="kpi-label">AI Analyzed</div></div></div>
        <div class="card"><div class="card-body"><div class="kpi-value" style="color:var(--accent-red)" id="stat-alerts">0</div><div class="kpi-label">Active Alerts</div></div></div>
    </div>
    <div class="main-grid">
        <div style="display:flex;flex-direction:column;gap:1.5rem">
            <div class="chart-sub-grid">
                <div class="card"><div class="card-header">Log Distribution</div><div class="card-body" style="height:200px;display:flex;align-items:center;justify-content:center"><canvas id="doughnutChart"></canvas></div></div>
                <div class="card"><div class="card-header">Anomaly Spikes</div><div class="card-body" style="height:200px"><canvas id="lineChart"></canvas></div></div>
            </div>
            <div class="card" style="flex:1">
                <div class="card-header"><span><i class="fa-solid fa-terminal" style="color:var(--accent-green);margin-right:8px"></i>Live Log Stream</span><span id="page-info" style="font-size:.8rem;color:var(--text-muted)">Page 1</span></div>
                <div id="log-stream" class="terminal"></div>
                <div class="pagination"><button class="btn" onclick="changePage(-1)">Prev</button><button class="btn" onclick="changePage(1)">Next</button></div>
            </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:1.5rem">
            <div class="card"><div class="card-header" style="background:rgba(239,68,68,0.05);color:#fca5a5">Threat Alerts</div><div class="card-body alert-list" id="alerts-panel"><p style="text-align:center;color:var(--text-muted);padding:2rem 0">No threats 🛡️</p></div></div>
            <div class="card" style="flex:1"><div class="card-header" style="background:rgba(139,92,246,0.05);color:#c4b5fd">AI Intelligence Feed</div><div class="card-body alert-list" id="analysis-panel" style="max-height:450px"><p style="text-align:center;color:var(--text-muted);padding:2rem 0">Waiting...</p></div></div>
        </div>
    </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
let currentPage=1;const perPage=40;let dChart,lChart;
setInterval(()=>{document.getElementById('live-clock').innerText=new Date().toLocaleTimeString()},1000);
async function secureFetch(url){return fetch(url).then(r=>r.json())}
async function loadData(){await Promise.all([fetchLogs(),fetchChartData(),fetchAnalysis(),fetchAlerts(),fetchStats(),loadSettings()])}

async function fetchLogs(){
    const from=(currentPage-1)*perPage;const to=from+perPage-1;const data=await secureFetch(`/api/logs?from=${from}&to=${to}`);
    const c=document.getElementById('log-stream');c.innerHTML='';
    if(!data.length){c.innerHTML='<p style="text-align:center;color:#475569;padding:2rem">No logs.</p>';return}
    data.forEach(log=>{const colors={ERROR:'#f87171',WARNING:'#fbbf24',INFO:'#60a5fa',DEBUG:'#94a3b8',CRITICAL:'#ff4d4f'};const d=document.createElement('div');d.className='log-line';d.innerHTML=`<span class="log-ts">${new Date(log.timestamp).toLocaleTimeString()}</span><span class="log-level" style="color:${colors[log.log_level]}">[${log.log_level}]</span><span style="color:#94a3b8;min-width:100px">[${log.source}]</span>${log.is_anomaly?'<span class="anomaly-badge">ANOMALY</span>':'<span style="width:60px"></span>'}<span class="log-msg"></span>`;d.querySelector('.log-msg').textContent=log.message;c.appendChild(d)});
    document.getElementById('page-info').innerText=`Page ${currentPage}`;
}
async function fetchChartData(){
    const data=await secureFetch('/api/chart_data');
    const ctx1=document.getElementById('doughnutChart').getContext('2d');if(dChart)dChart.destroy();
    dChart=new Chart(ctx1,{type:'doughnut',data:{labels:Object.keys(data.levels),datasets:[{data:Object.values(data.levels),backgroundColor:['#3b82f6','#eab308','#ef4444','#991b1b','#64748b'],borderWidth:0}]},options:{responsive:true,maintainAspectRatio:false,cutout:'70%',plugins:{legend:{position:'right',labels:{color:'#cbd5e1'}}}}});
    const ctx2=document.getElementById('lineChart').getContext('2d');if(lChart)lChart.destroy();
    const g=ctx2.createLinearGradient(0,0,0,200);g.addColorStop(0,'rgba(239,68,68,0.5)');g.addColorStop(1,'rgba(239,68,68,0.0)');
    lChart=new Chart(ctx2,{type:'line',data:{labels:Object.keys(data.timeline),datasets:[{data:Object.values(data.timeline),borderColor:'#ef4444',backgroundColor:g,fill:true,tension:.4,pointRadius:3}]},options:{responsive:true,maintainAspectRatio:false,scales:{x:{display:false},y:{beginAtZero:true,ticks:{color:'#64748b'},grid:{color:'rgba(255,255,255,0.05)'}}},plugins:{legend:{display:false}}}});
}
async function fetchAnalysis(){const data=await secureFetch('/api/analysis');const c=document.getElementById('analysis-panel');c.innerHTML='';if(!data.length){c.innerHTML='<p style="text-align:center;color:#475569;padding:2rem">None.</p>';return}data.slice(0,8).forEach(a=>{const d=document.createElement('div');d.className='ai-card';d.innerHTML=`<div style="display:flex;justify-content:space-between;margin-bottom:8px"><span class="ai-severity">${a.severity}</span><span style="font-size:.75rem;color:var(--text-muted)">${Math.round(a.confidence_score*100)}%</span></div><p style="font-size:.85rem;margin-bottom:8px"><strong>Cause:</strong> ${a.root_cause}</p><div style="font-size:.8rem;color:#94a3b8"><strong>Fix:</strong><ul style="margin-top:4px;padding-left:20px">${a.recommended_actions.map(a=>`<li>${a}</li>`).join('')}</ul></div>`;c.appendChild(d)})}
async function fetchAlerts(){const data=await secureFetch('/api/alerts');const c=document.getElementById('alerts-panel');c.innerHTML='';if(!data.length){c.innerHTML='<p style="text-align:center;color:var(--text-muted);padding:2rem">No threats 🛡️</p>';return}data.forEach(a=>{const d=document.createElement('div');d.className='alert-item';d.innerHTML=`<div style="font-weight:700;font-size:.8rem;margin-bottom:4px;color:#f87171">${a.severity}</div><p style="font-size:.85rem;color:#cbd5e1">${a.message}</p>`;c.appendChild(d)})}
async function fetchStats(){const data=await secureFetch('/api/stats');document.getElementById('stat-total').innerText=data.total_logs.toLocaleString();document.getElementById('stat-anomalies').innerText=data.anomalies.toLocaleString();document.getElementById('stat-analyzed').innerText=data.analyzed.toLocaleString();document.getElementById('stat-alerts').innerText=data.alerts.toLocaleString()}
async function loadSettings(){const data=await secureFetch('/api/settings');document.getElementById('alertEmailInput').value=data.alert_email||'';document.getElementById('apiKeyInput').value=data.api_key}
function toggleSettings(){document.getElementById('settingsModal').classList.toggle('active')}
async function saveSettings(){
    const email = document.getElementById('alertEmailInput').value;
    if(!email) return alert("Please enter an email");
    const res = await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({alert_email:email})});
    if(res.ok) { alert("Settings Saved Successfully!"); toggleSettings(); }
    else { alert("Error saving settings. Check console."); }
}
function changePage(dir){const p=currentPage+dir;if(p>0){currentPage=p;fetchLogs()}}
loadData();setInterval(loadData,4000);
</script></body></html>'''

# --- ROUTES ---
@app.route('/auth', methods=['GET', 'POST'])
def auth_page():
    error = None
    mode = request.args.get('mode', 'login')
    
    if request.method == 'POST':
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        domain = email.split('@')[1] if '@' in email else None

        if mode == 'register':
            # THE MAGIC TRICK: Find or Create Workspace
            ws_res = supabase.table("workspaces").select("*").eq("domain", domain).execute()
            if not ws_res.data:
                # Auto-generate API Key for new workspace
                new_key = f"sk_{domain.split('.')[0]}_{os.urandom(8).hex()}"
                ws_res = supabase.table("workspaces").insert({"domain": domain, "name": f"{domain.split('.')[0].title()} Workspace", "api_key": new_key}).execute()
            
            workspace_id = ws_res.data[0]['id']
            
            # Create User
            try:
                supabase.table("users").insert({"email": email, "password_hash": generate_password_hash(password), "workspace_id": workspace_id, "role": "admin"}).execute()
            except: 
                error = "Email already registered."

        if mode == 'login' or (mode == 'register' and not error):
            user_res = supabase.table("users").select("*, workspaces(*)").eq("email", email).execute()
            user = user_res.data[0] if user_res.data else None
            
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['workspace_id'] = user['workspace_id']
                session['workspace_name'] = user['workspaces']['name']
                session['role'] = user['role']
                return redirect(url_for('index'))
            else:
                error = "Invalid credentials."

    return render_template_string(AUTH_HTML, error=error, mode=mode)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth_page'))

@app.route('/')
@login_required
def index():
    return render_template_string(DASHBOARD_HTML, workspace=session.get('workspace_name'))

# --- SETTINGS API ---
@app.route('/api/settings')
@login_required
def get_settings():
    res = supabase.table("workspaces").select("api_key, alert_email").eq("id", session['workspace_id']).execute()
    return jsonify(res.data[0]) if res.data else jsonify({}), 200

@app.route('/api/settings', methods=['POST'])
@login_required
def save_settings():
    data = request.json
    supabase.table("workspaces").update({"alert_email": data.get('alert_email')}).eq("id", session['workspace_id']).execute()
    return jsonify({"status": "saved"}), 200

# --- UNIFIED INGESTION (SaaS Walled) ---
@app.route('/api/ingest', methods=['POST'])
def ingest_log():
    # 1. Authenticate via API Key
    api_key = request.headers.get('X-API-Key') or request.headers.get('X-Hub-Signature-256', "").split('=')[-1]
    ws_res = supabase.table("workspaces").select("id, alert_email").eq("api_key", api_key).execute()
    if not ws_res.data: return jsonify({"error": "Invalid API Key"}), 401
    
    ws_id = ws_res.data[0]['id']
    data = request.json
    logs = []

    # 2. Parse Flipkart vs GitHub
    if 'level' in data: # Flipkart
        logs.append({"log_level": data['level'], "source": data.get('source'), "message": data.get('message'), "is_anomaly": data.get('level','').upper() in ['ERROR', 'CRITICAL']})
    elif 'sender' in data: # GitHub
        action = request.headers.get('X-GitHub-Event', 'push')
        user = data.get('sender',{}).get('login',''); repo = data.get('repository',{}).get('name','')
        msg = f"[{user}] pushed {len(data.get('commits',[]))} commit(s) to {repo}" if action=='push' else f"[{user}] triggered {action} on {repo}"
        logs.append({"log_level": "INFO", "source": "github-webhook", "message": msg, "is_anomaly": False})

    # 3. Insert with Workspace Wall
    for log in logs:
        supabase.table("logs").insert({**log, "workspace_id": ws_id}).execute()
    return jsonify({"status": "ingested"}), 201

# --- DATA APIs (SaaS Isolated) ---
@app.route('/api/logs')
@login_required
def get_logs():
    f,t = request.args.get('from',0,type=int), request.args.get('to',39,type=int)
    if t-f>100: t=f+100
    res = supabase.table("logs").select("*").eq("workspace_id", session['workspace_id']).order("timestamp", desc=True).range(f,t).execute()
    return jsonify(res.data)

@app.route('/api/analysis')
@login_required
def get_analysis():
    res = supabase.table("analysis").select("*").eq("workspace_id", session['workspace_id']).order("created_at", desc=True).limit(20).execute()
    return jsonify(res.data)

@app.route('/api/alerts')
@login_required
def get_alerts():
    res = supabase.table("alerts").select("*").eq("workspace_id", session['workspace_id']).eq("is_resolved", False).order("created_at", desc=True).limit(10).execute()
    return jsonify(res.data)

@app.route('/api/stats')
@login_required
def get_stats():
    ws = session['workspace_id']
    l = supabase.table("logs").select("id", count="exact").eq("workspace_id", ws).execute()
    a = supabase.table("logs").select("id", count="exact").eq("workspace_id", ws).eq("is_anomaly", True).execute()
    an = supabase.table("analysis").select("id", count="exact").eq("workspace_id", ws).execute()
    al = supabase.table("alerts").select("id", count="exact").eq("workspace_id", ws).eq("is_resolved", False).execute()
    return jsonify({"total_logs": l.count, "anomalies": a.count, "analyzed": an.count, "alerts": al.count})

@app.route('/api/chart_data')
@login_required
def chart_data():
    res = supabase.table("logs").select("timestamp, log_level, is_anomaly").eq("workspace_id", session['workspace_id']).order("timestamp", desc=True).limit(200).execute()
    levels, timeline = {"INFO":0,"WARNING":0,"ERROR":0,"CRITICAL":0,"DEBUG":0}, {}
    for log in res.data:
        lvl = log.get("log_level","INFO")
        if lvl in levels: levels[lvl] += 1
        if log.get("is_anomaly"): ts = log.get("timestamp","")[:16]; timeline[ts] = timeline.get(ts,0) + 1
    return jsonify({"levels": levels, "timeline": dict(sorted(timeline.items()))})

# --- AUTO AI BACKGROUND WORKER (SaaS Aware) ---
def auto_analyze():
    print("🧠 [AI] Scanning workspaces for anomalies...")
    # Find unanalyzed anomalies across ALL workspaces
    logs_res = supabase.table("logs").select("id, workspace_id, message, source").eq("is_anomaly", True).order("timestamp", desc=True).limit(10).execute()
    analyzed_ids = [r['log_id'] for r in supabase.table("analysis").select("log_id").execute().data]
    
    for log in [l for l in logs_res.data if l['id'] not in analyzed_ids]:
        try:
            resp = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":f"Analyze log, return JSON: root_cause, severity (Critical/High/Medium/Low), recommended_actions (list). Log: {log['message']}"}], temperature=0.1, max_tokens=200, response_format={"type":"json_object"})
            result = json.loads(resp.choices[0].message.content)
        except: result = {"root_cause":"LLM Error","severity":"Low","recommended_actions":["Review manually"]}
        
        supabase.table("analysis").insert({"log_id":log['id'],"workspace_id":log['workspace_id'],"root_cause":result.get("root_cause"),"severity":result.get("severity"),"recommended_actions":result.get("recommended_actions",[]),"confidence_score":0.9}).execute()
        
        if result.get("severity") in ["Critical","High"]:
            # DYNAMIC EMAIL: Look up THIS specific workspace's email
            ws = supabase.table("workspaces").select("alert_email, name").eq("id", log['workspace_id']).execute().data[0]
            supabase.table("alerts").insert({"workspace_id":log['workspace_id'],"severity":result.get("severity"),"message":f"[{ws['name']}] {result.get('root_cause')}","is_resolved":False}).execute()
            
            if ws['alert_email']:
                send_email(f"🚨 Sentinel Alert: {result.get('severity')}", f"<h3>{result.get('root_cause')}</h3><p>Workspace: {ws['name']}</p>", ws['alert_email'])
    threading.Timer(15.0, auto_analyze).start()

if __name__ == '__main__':
    threading.Thread(target=auto_analyze, daemon=True).start()
    print("\n🛡️ SENTINEL AI SAAS PLATFORM")
    print("🚀 Open http://localhost:5000\n")
    app.run(debug=True, port=5000, use_reloader=False)
