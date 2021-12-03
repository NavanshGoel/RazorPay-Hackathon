from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import razorpay
from datetime import datetime
import time
import requests
import json
import math

app = Flask(__name__)
app.secret_key = 'secret101'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login.html')
def login():
    return render_template('login.html')


@app.route('/forgot-password.html')
def forgot_password():
    return render_template('forgot-password.html')


@app.route('/register.html')
def register():
    return render_template('register.html')


@app.route('/dashboard.html')
def dashboard():
    return render_template('dashboard.html')


@app.route("/seller", methods=['GET', 'POST'])
def home():
    req = requests.get(
        'https://raw.githubusercontent.com/ashank2603/RazorPay-Hackathon/main/items.json')
    data = json.loads(req.content)
    return render_template('seller.html', data=data['items'])


@app.route("/cart", methods=['GET', 'POST'])
def send_data():
    if request.method == 'POST':
        cust_name = request.form.get("cust_name")
        cust_phone = request.form.get("cust_phone")
        cust_email = request.form.get("cust_email")
        selected_item = request.form.get("itemCheck")
    return render_template('cart.html', cust_name=cust_name, cust_phone=cust_phone, cust_email=cust_email, selected_item=selected_item)


@app.route('/profile.html')
def profile():
    return render_template('profile.html')


@app.route('/topgrossing.html')
def topgrossing():
    # Replace with your own key ID and secret
    client = razorpay.Client(
        auth=("rzp_test_qnyYZxk8GJnsJ7", "0rmq8sSoXM6DXtQHrEGlpRwJ"))
    js = client.invoice.fetch_all()
    d = dict()
    for i in js['items']:
        for j in i['line_items']:
            num_days = calcDays(i['date'])
            if num_days <= 30:
                quant_last_30_days = j['quantity']
            else:
                quant_last_30_days = 0

            if j['name'] not in d:
                d[j['name']] = [j['description'], j['amount'],
                                j['quantity'], quant_last_30_days, j['net_amount']*j['quantity']/100]
            else:
                d[j['name']][2] += j['quantity']
                d[j['name']][2] += quant_last_30_days
                d[j['name']][4] += j['net_amount']*j['quantity']/100
    return render_template('topgrossing.html', d=d)


def calcDays(ts):
    curr = int(time.time())
    g = ts-curr
    num_days = math.floor(g/1000/60/60/24)
    return num_days


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run(debug=True)
