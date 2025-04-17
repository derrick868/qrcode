from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import base64
import requests
from datetime import datetime

load_dotenv()

app = Flask(__name__)

# Load credentials from .env
MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
MPESA_BASE_URL = os.getenv("MPESA_BASE_URL", "https://sandbox.safaricom.co.ke")
CALLBACK_URL = os.getenv("CALLBACK_URL", "https://qrcode-n9ap.onrender.com/callback")

# Generate access token
def get_access_token():
    url = f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET))
    response.raise_for_status()
    return response.json()['access_token']

# STK Push function
def lipa_na_mpesa(phone, amount):
    access_token = get_access_token()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password_str = MPESA_SHORTCODE + MPESA_PASSKEY + timestamp
    password = base64.b64encode(password_str.encode()).decode()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": "QR-Payment",
        "TransactionDesc": "Payment from QR Code"
    }

    url = f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

    
import qrcode
from io import BytesIO
from flask import send_file, request, redirect, url_for

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        method = request.form.get('method')
        number = request.form.get('number')
        data = {
            "method": method,
            "number": number
        }

        qr = qrcode.make(data)
        buf = BytesIO()
        qr.save(buf)
        buf.seek(0)

        return send_file(buf, mimetype='image/png')

    return render_template('generate.html')

# Homepage
@app.route('/')
def index():
    return render_template('scan.html')

# Payment route
@app.route('/pay', methods=['POST'])
def pay():
    data = request.get_json()
    phone = data.get('phone')
    amount = int(data.get('amount'))

    try:
        response = lipa_na_mpesa(phone, amount)
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Run the app
if __name__ == '__main__':
    # Dynamically bind to the port specified by the environment (Render platform)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
