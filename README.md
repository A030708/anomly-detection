# 🛡️ Sentinel AI: Autonomous Log Intelligence Platform

Sentinel AI is a production-grade, autonomous SIEM (Security Information and Event Management) system designed to ingest, analyze, and mitigate security threats in real-time. It features a premium dark-mode dashboard, an autonomous AI background worker powered by Llama-3, and multi-source ingestion capabilities.

![Sentinel Dashboard Mockup](https://raw.githubusercontent.com/A030708/anomly-detection/main/dashboard_preview.png) *(Note: Add your own screenshot here!)*

---

## 🚀 Core Features

### 1. 🧠 Autonomous AI Intelligence
*   **Background Worker**: A dedicated thread in the dashboard automatically monitors incoming anomalies.
*   **Llama-3 Analysis**: Integrated with **Groq API** to perform deep root-cause analysis on logs in real-time.
*   **Self-Healing Intelligence**: The AI generates recommended actions and severity scores, populating the Intelligence Feed automatically.

### 2. 🛒 Microservices & Honeypots
*   **Mini-Flipkart Demo**: Includes a secondary application that simulates a real e-commerce store.
*   **Security Traps**: Wired with "honeypot" logic to detect inventory manipulation (negative quantities) and payment fraud (brute-force card attempts).

### 3. 🌍 Multi-Source Webhook Ingestion
*   **Universal API**: A hardened `/api/ingest` endpoint protected by X-API-Key authentication.
*   **GitHub Integration**: Natively supports GitHub Webhooks to monitor real-time pushes, PRs, and branch deletions directly alongside application logs.

### 4. 🔒 Enterprise-Grade Security
*   **Authentication**: Full session-based login system for the Command Center.
*   **XSS Protection**: Sanitized DOM manipulation to prevent malicious script injection via log payloads.
*   **Cloud Ready**: Fully container-ready and optimized for deployment on platforms like Render or Heroku.

---

## 🛠️ Technology Stack

*   **Backend**: Python, Flask, Gunicorn
*   **Database**: Supabase (PostgreSQL)
*   **AI Engine**: Groq (Llama-3.3-70b-versatile)
*   **Frontend**: Vanilla JS, Chart.js, FontAwesome, Tailwind-inspired CSS
*   **Infrastructure**: Ngrok (for local webhooks), Render (Cloud Hosting)

---

## 🏁 Getting Started

### 1. Prerequisites
*   Python 3.10+
*   Supabase Account (Free tier works perfectly)
*   Groq API Key (Free, lighting-fast AI)

### 2. Installation
```bash
git clone https://github.com/A030708/anomly-detection.git
cd anomly-detection
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GROQ_API_KEY=your_groq_api_key
DASHBOARD_API_KEY=sentinel-secure-key-123
```

### 4. Run the Platform
1. **Start the Dashboard**: `python dashboard.py`
2. **Start the Store**: `python fake_flipkart.py`
3. **Login**: `http://localhost:5000` (User: `admin`, Pass: `password`)

---

## 🛡️ Security Demo Scenarios
*   **Trigger Anomaly**: Try to add `-5` items to your cart in the Flipkart app.
*   **Trigger Fraud**: Fail 3 credit card payments in a row.
*   **Check Dashboard**: Watch the AI thread identify the hack and suggest a fix within 15 seconds.

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.

**Author**: [A030708](https://github.com/A030708)
