import requests
import time
import random
from datetime import datetime

SENTINEL_API_URL = "http://localhost:5000/api/ingest"

SERVICES = ["payment-gateway", "auth-service", "inventory-db", "user-api"]
LOG_MESSAGES = [
    {"level": "INFO", "message": "User login successful"},
    {"level": "INFO", "message": "Database query optimized"},
    {"level": "WARNING", "message": "High memory usage detected"},
    {"level": "ERROR", "message": "Connection timeout in payment-gateway"},
    {"level": "CRITICAL", "message": "Unauthorized access attempt blocked"},
    {"level": "ERROR", "message": "Failed to process transaction ID #TX9921"},
]

def send_fake_log():
    service = random.choice(SERVICES)
    log_template = random.choice(LOG_MESSAGES)
    
    payload = {
        "service": service,
        "level": log_template["level"],
        "message": f"[{service}] {log_template['message']}",
        "metadata": {
            "instance_id": f"i-{random.randint(1000, 9999)}",
            "region": "us-east-1"
        }
    }
    
    try:
        headers = {"X-API-Key": "sentinel-secure-key-123"}
        response = requests.post(SENTINEL_API_URL, json=payload, headers=headers)
        if response.status_code == 201:
            print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Ingested: {log_template['level']} from {service}")
        else:
            print(f"❌ Failed to ingest: {response.text}")
    except Exception as e:
        print(f"⚠️ Sentinel Dashboard not running? Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Fake Company Service Simulator...")
    print(f"📡 Sending logs to {SENTINEL_API_URL}")
    print("Press Ctrl+C to stop.\n")
    
    while True:
        send_fake_log()
        # Random interval between 1 and 5 seconds
        time.sleep(random.uniform(1, 5))
