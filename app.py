from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import razorpay
from datetime import datetime
import time

app = Flask(__name__)
app.secret_key = 'secret101'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard.html')
def dashboard():
    return render_template('dashboard.html')


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
            if j['name'] not in d:
                ts = i['date']
                curr = int(time.time())
                g = ts-curr
                if g > 0:
                    continue
                f = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')
                d[j['name']] = [j['description'], j['amount'],
                                j['quantity'], f, j['net_amount']*j['quantity']/100]
            else:
                d[j['name']][2] += j['quantity']
                d[j['name']][4] += j['net_amount']*j['quantity']/100
    return render_template('topgrossing.html', d=d)


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run(debug=True)
