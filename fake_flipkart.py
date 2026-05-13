from flask import Flask, render_template_string, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

SENTINEL_URL = "http://localhost:5000/api/ingest"
API_KEY = "sentinel-secure-key-123"
HEADERS = {"Content-Type": "application/json", "X-API-Key": API_KEY}

# Tracks bad behavior
failed_payments = 0

def send_to_sentinel(level, source, message):
    payload = {"level": level, "source": source, "message": message, "timestamp": datetime.now().isoformat()}
    try:
        requests.post(SENTINEL_URL, json=payload, headers=HEADERS, timeout=2)
    except:
        pass

FLIPKART_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Mini-Flipkart</title>
    <style>
        body { font-family: Arial; background: #f1f3f6; margin: 0; }
        .header { background: #2874f0; color: white; padding: 15px; display: flex; justify-content: space-between; }
        .product-list { display: flex; gap: 20px; padding: 20px; flex-wrap: wrap; justify-content: center; }
        .product { background: white; padding: 20px; border-radius: 8px; width: 200px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .product img { width: 100px; height: 100px; object-fit: contain; }
        .btn { background: #fb641b; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold; }
        input { padding: 10px; width: 90%; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; }
        .checkout-box { background: white; max-width: 400px; margin: 50px auto; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="header">
        <h2>Mini-Flipkart</h2>
        <div style="font-size: 0.9rem;">Normal Behavior = INFO | Hacking Attempt = CRITICAL</div>
    </div>

    <div class="product-list">
        <div class="product">
            <div style="font-size:50px">💻</div>
            <h3>MacBook Pro</h3>
            <p>$1999</p>
            <input type="number" id="qty-mac" value="1" min="1" style="width:50px">
            <button class="btn" onclick="addToCart('MacBook Pro', document.getElementById('qty-mac').value)">Add to Cart</button>
        </div>
        <div class="product">
            <div style="font-size:50px">📱</div>
            <h3>iPhone 15</h3>
            <p>$999</p>
            <input type="number" id="qty-iphone" value="1" min="1" style="width:50px">
            <button class="btn" onclick="addToCart('iPhone 15', document.getElementById('qty-iphone').value)">Add to Cart</button>
        </div>
    </div>

    <div class="checkout-box">
        <h3>Search Products</h3>
        <input type="text" id="search" placeholder="Search... (try ' OR 1=1 --)">
        <button class="btn" style="width:100%" onclick="searchProducts()">Search</button>
    </div>

    <div class="checkout-box">
        <h3>Leave a Review</h3>
        <input type="text" id="review" placeholder="Write your review... (try <script> tag)">
        <button class="btn" style="width:100%" onclick="submitReview()">Submit Review</button>
        <div id="reviews" style="margin-top:10px; font-size:0.9rem;"></div>
    </div>

    <div class="checkout-box">
        <h3>Checkout Payment</h3>
        <input type="text" id="coupon" placeholder="Coupon Code (try SAVE10)">
        <button class="btn" style="width:100%; margin-bottom:10px; background:#2874f0" onclick="applyCoupon()">Apply Coupon</button>
        <input type="text" id="card" placeholder="Card Number (4242... for success)">
        <button class="btn" style="width:100%" onclick="pay()">Pay Now</button>
    </div>

    <script>
        function addToCart(item, qty) {
            fetch('/api/cart', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({item: item, quantity: parseInt(qty)})
            }).then(r => r.json()).then(data => {
                alert(data.message);
                if(data.hacked) location.reload();
            });
        }

        function pay() {
            const card = document.getElementById('card').value;
            fetch('/api/pay', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({card: card})
            }).then(r => r.json()).then(data => {
                alert(data.message);
            });
        }

        function searchProducts() {
            const q = document.getElementById('search').value;
            fetch('/api/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query: q})
            }).then(r => r.json()).then(data => alert(data.message));
        }

        function submitReview() {
            const text = document.getElementById('review').value;
            fetch('/api/review', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({review: text})
            }).then(r => r.json()).then(data => {
                alert(data.message);
                if(data.safe) document.getElementById('reviews').innerText = 'Latest: ' + text;
            });
        }

        function applyCoupon() {
            const code = document.getElementById('coupon').value;
            fetch('/api/coupon', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({code: code})
            }).then(r => r.json()).then(data => alert(data.message));
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    send_to_sentinel("INFO", "flipkart-frontend", "User loaded Mini-Flipkart homepage.")
    return render_template_string(FLIPKART_HTML)

@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    data = request.json
    item = data.get('item')
    qty = data.get('quantity')

    # TRAP 1: Inventory Manipulation (Negative Quantities)
    if qty < 0 or qty > 100:
        send_to_sentinel("CRITICAL", "flipkart-backend", f"SECURITY BREACH: User injected invalid quantity '{qty}' for item {item}. Possible exploit.")
        return jsonify({"message": "🚨 SECURITY ALERT TRIGGERED! Sentinel AI notified.", "hacked": True})
    
    send_to_sentinel("INFO", "flipkart-backend", f"User added {qty}x {item} to cart.")
    return jsonify({"message": f"Added {qty}x {item} to cart!", "hacked": False})

@app.route('/api/pay', methods=['POST'])
def pay():
    global failed_payments
    data = request.json
    card = data.get('card')

    if card.startswith("4242"):
        failed_payments = 0
        send_to_sentinel("INFO", "flipkart-payments", "Payment processed via Stripe.")
        return jsonify({"message": "Payment Success! Order Placed."})
    
    failed_payments += 1
    send_to_sentinel("WARNING", "flipkart-payments", f"Payment declined for card ...{card[-4:]}")
    
    # TRAP 2: Fraud Detection (3 rapid fails)
    if failed_payments >= 3:
        send_to_sentinel("CRITICAL", "flipkart-fraud-system", f"FRAUD DETECTED: {failed_payments} failed attempts. IP flagged.")
        return jsonify({"message": "🚨 FRAUD DETECTED! Your IP has been locked."})
    
    return jsonify({"message": f"Card Declined. ({failed_payments}/3 attempts)"})

# TRAP 3: SQL Injection Detection
@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query', '')
    sql_patterns = ["'", '"', '--', ';', 'OR 1=1', 'DROP', 'UNION', 'SELECT', 'DELETE', 'INSERT']
    if any(p.lower() in query.lower() for p in sql_patterns):
        send_to_sentinel("CRITICAL", "flipkart-search", f"SQL INJECTION ATTEMPT: User searched '{query}'. Attack pattern detected.")
        return jsonify({"message": "🚨 SQL INJECTION DETECTED! Security team notified."})
    send_to_sentinel("INFO", "flipkart-search", f"User searched for '{query}'.")
    return jsonify({"message": f"Found 3 results for '{query}'"})

# TRAP 4: XSS Attack Detection
@app.route('/api/review', methods=['POST'])
def review():
    data = request.json
    text = data.get('review', '')
    xss_patterns = ['<script', 'javascript:', 'onerror', 'onload', '<img', '<iframe', 'eval(']
    if any(p.lower() in text.lower() for p in xss_patterns):
        send_to_sentinel("CRITICAL", "flipkart-reviews", f"XSS ATTACK ATTEMPT: User injected '{text[:100]}' into review field.")
        return jsonify({"message": "🚨 XSS ATTACK BLOCKED! Your session has been flagged.", "safe": False})
    send_to_sentinel("INFO", "flipkart-reviews", f"User submitted review: '{text[:50]}'.")
    return jsonify({"message": "Review submitted! Thank you.", "safe": True})

# TRAP 5: Coupon Abuse Detection
coupon_uses = {}
@app.route('/api/coupon', methods=['POST'])
def coupon():
    data = request.json
    code = data.get('code', '').upper()
    coupon_uses[code] = coupon_uses.get(code, 0) + 1
    
    if coupon_uses[code] > 3:
        send_to_sentinel("CRITICAL", "flipkart-promotions", f"COUPON ABUSE: Code '{code}' used {coupon_uses[code]} times. Exploitation detected.")
        return jsonify({"message": f"🚨 COUPON ABUSE DETECTED! Code '{code}' has been revoked."})
    
    if code == "SAVE10":
        send_to_sentinel("INFO", "flipkart-promotions", f"Coupon '{code}' applied successfully.")
        return jsonify({"message": "Coupon applied! 10% discount added."})
    
    send_to_sentinel("WARNING", "flipkart-promotions", f"Invalid coupon code '{code}' attempted.")
    return jsonify({"message": f"Invalid coupon code '{code}'."}) 

if __name__ == '__main__':
    print("\n🛒 MINI-FLIPKART STARTING...")
    print("🔗 Open http://localhost:5001")
    print("\n🎯 ATTACK DEMOS:")
    print("   1. Cart: Enter -5 quantity")
    print("   2. Payment: Fail 3 cards in a row")
    print("   3. Search: Type ' OR 1=1 --")
    print("   4. Review: Type <script>alert('xss')</script>")
    print("   5. Coupon: Use SAVE10 more than 3 times\n")
    app.run(port=5001)
