import requests
import time
import random

# This is the company's backend code. It knows NOTHING about your dashboard's database.
# It only knows one thing: "If I crash, send an HTTP POST to this URL."

SENTINEL_WEBHOOK_URL = "http://localhost:5000/api/ingest"
API_KEY = "sentinel-secure-key-123" # Must match your dashboard.py key!

HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def send_log(level, source, message):
    """Helper function to send a log to Sentinel AI"""
    payload = {
        "level": level,
        "source": source,
        "message": message,
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S')
    }
    try:
        requests.post(SENTINEL_WEBHOOK_URL, json=payload, headers=HEADERS)
    except Exception as e:
        print(f"⚠️ Sentinel Dashboard not reachable: {e}")

def process_user_payment(user_id):
    """Simulating a real company function"""
    send_log("INFO", "payment-gateway", f"Processing payment for user {user_id}...")
    
    # Simulate a 20% chance of the database crashing
    if random.random() < 0.2:
        error_msg = "FATAL: PostgreSQL connection lost. Timeout after 30s waiting for response from db-cluster-01.internal"
        send_log("ERROR", "payment-gateway", error_msg)
        return False # Payment failed
    
    send_log("INFO", "payment-gateway", f"Payment successful for user {user_id}.")
    return True

if __name__ == "__main__":
    print("\n" + "="*40)
    print("🛒 Starting FakeCompany E-Commerce Backend...")
    print(f"📡 Sending traffic to Sentinel AI Webhook at {SENTINEL_WEBHOOK_URL}")
    print("="*40 + "\n")
    
    # Simulate infinite users checking out
    user_id = 1
    try:
        while True:
            print(f"User {user_id} checking out...")
            success = process_user_payment(user_id)
            
            if not success:
                print("   ❌ CRASH DETECTED! (Sent to Sentinel AI)")
            else:
                print("   ✅ Success")
                
            user_id += 1
            time.sleep(2) # Wait 2 seconds between users
    except KeyboardInterrupt:
        print("\n👋 Simulator stopped.")
