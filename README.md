# 🛡️ Sentinel AI: Real-Time Log Intelligence

Sentinel AI is a modern, AI-powered log analysis engine that transforms raw system logs into actionable security intelligence. It features real-time log tailing, smart LLM caching, and a premium dark-mode command center.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-green?logo=supabase)
![Groq](https://img.shields.io/badge/Groq-LLaMA3-orange?logo=groq)

## ✨ Key Features

- **Real-Time Ingestion:** Uses OS-level `watchdog` to tail log files instantly (no polling).
- **Universal Parser:** Auto-detects and parses JSON, Syslog, and standard log formats.
- **Cost-Effective AI:** Integrates Groq LLM with MD5-based caching to avoid analyzing duplicate errors.
- **Anomaly Detection:** Flags errors/criticals automatically before sending to the AI.
- **Premium Dashboard:** Datadog-inspired UI with live charts, terminal streams, and threat alerts.
- **Cloud Backend:** Fully managed PostgreSQL database via Supabase with optimized indexes.

## 🏗️ System Architecture

```text
[Log Files] ---> (Watchdog) ---> [Log Parser] ---> [Supabase DB]
                                                     |
                                                     v
                                               [Anomaly Filter]
                                                     |
                                                     v
                                          [Smart LLM Analyzer (Groq)]
                                                     | (With Caching)
                                                     v
                                                [Alerts Table]
                                                     |
                                                     v
                                          [Flask Dashboard (UI)]
```

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+
- A [Groq API Key](https://console.groq.com/keys)
- A [Supabase Project](https://supabase.com)

### 2. Installation
```bash
git clone https://github.com/yourusername/sentinel-ai.git
cd sentinel-ai
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuration
Rename `.env.example` to `.env` and add your keys:
```env
GROQ_API_KEY=gsk_your_key_here
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

### 4. Database Setup
Run the following SQL in your Supabase SQL Editor to create tables and performance indexes:
```sql
-- (Paste the SQL schema provided in schema.sql)
```

### 5. Run the System
Open **3 separate terminals**:

```bash
# Terminal 1: Start watching logs
python log_collector.py

# Terminal 2: Start the AI Analyzer
python llm_analyzer.py

# Terminal 3: Start the Web Dashboard
python dashboard.py
```
Open `http://localhost:5000` to view the Command Center.

To test, echo logs into your watched file:
```bash
echo '{"level": "ERROR", "source": "auth", "message": "Login failed"}' >> sample.log
```

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| Backend Framework | Flask |
| Real-time File Watching | Watchdog |
| Database | Supabase (PostgreSQL) |
| AI/LLM Engine | Groq (Llama 3.3 70B) |
| Frontend Charts | Chart.js |
| Styling | Custom CSS (Glassmorphism) |

## 📈 Future Roadmap
- [ ] Add user authentication (JWT)
- [ ] Docker containerization
- [ ] WebSocket integration for zero-latency UI updates
- [ ] Scikit-learn ML model for statistical anomaly detection
- [ ] Slack/PagerDuty webhook integrations
