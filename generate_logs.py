import time
import random
import os

LOG_FILE = "app.log"

LOG_SAMPLES = [
    "[INFO] [auth-svc] User login successful for uid-9281",
    "[ERROR] [payment-gw] Failed to parse JSON payload: Unexpected token",
    "[WARNING] [user-db] Connection pool exhausted, waiting 500ms",
    "[INFO] [nginx] HTTP GET /api/v1/users 200 OK 45ms",
    "[ERROR] [redis-cache] Database query timeout after 3000ms",
    "[CRITICAL] [core-api] Memory usage at 89%, triggering emergency GC",
    "[WARNING] [auth-svc] Invalid JWT signature detected",
    "[INFO] [nginx] HTTP POST /api/v1/login 401 Unauthorized 120ms",
    '{"timestamp": "2024-05-11T10:00:00Z", "level": "ERROR", "message": "Disk space low on /var/log", "source": "system-monitor"}'
]

def generate_logs():
    print(f"Generating logs to {LOG_FILE}... Press Ctrl+C to stop.")
    while True:
        log = random.choice(LOG_SAMPLES)
        with open(LOG_FILE, "a") as f:
            f.write(log + "\n")
        print(f"Added: {log[:50]}...")
        time.sleep(random.uniform(1, 5))

if __name__ == "__main__":
    generate_logs()
