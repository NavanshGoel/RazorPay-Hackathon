from flask import Flask, render_template, request, redirect
import razorpay
import time
import requests
import json
import env
import pyodbc

app = Flask(__name__)
app.secret_key = 'secret101'

conn = pyodbc.connect('DRIVER='+env.driver+';SERVER=tcp:'+env.server +
                      ';PORT=1433;DATABASE='+env.database+';UID='+env.username+';PWD=' + env.password)
cursor = conn.cursor()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login.html')
def login():
    return render_template('login.html')


@app.route('/validation', methods=['GET', 'POST'])
def validation():
    if request.method == 'POST':
        username = request.form['email']
        password = request.form['password']
        cursor.execute(
            "SELECT * FROM utable WHERE email = ? AND password = ?", username, password)
        row = cursor.fetchone()
        if row:
            return redirect('/dashboard.html')
        else:
            return render_template('login.html', err="Invalid Credentials")


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
def get_data():
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
        selected_item = request.form.getlist("itemCheck")
        qty = request.form.getlist('qty')
        amt = request.form.getlist('amt')
        final_amt = []
        for i in range(0, len(qty)):
            final_amt.append(int(qty[i]) * int(amt[i]))

        final_amt = [i for i in final_amt if i != 0]
        total_amt = 0
        for i in final_amt:
            total_amt = total_amt + i
    return render_template('cart.html', cust_name=cust_name, cust_phone=cust_phone, cust_email=cust_email, selected_item=selected_item, final_amt=final_amt, total_amt=total_amt)


@app.route('/profile.html')
def profile():
    return render_template('profile.html')


@app.route('/validation1', methods=['GET', 'POST'])
def validation1():
    if request.method == 'POST':
        cust_name = request.form.get("cust_name")
        cust_phone = request.form.get("cust_phone")
        cust_email = request.form.get("cust_email")
        selected_item = request.form.getlist("itemCheck")
        qty = request.form.getlist('qty')
        amt = request.form.getlist('amt')
        final_amt = []
        for i in range(0, len(qty)):
            final_amt.append(int(qty[i]) * int(amt[i]))

        final_amt = [i for i in final_amt if i != 0]
        ts = int(time.time())
        cursor.execute(
            "INSERT INTO orders(cust_name, cust_phone, cust_email, selected_item, qty, amt, final_amt, ts) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", cust_name, cust_phone, cust_email, selected_item, qty, amt, final_amt, ts)
        conn.commit()
        return redirect('/profile.html', done="Updated Successfully")


@app.route('/topgrossing.html')
def topgrossing():
    # Replace with your own key ID and secret
    client = razorpay.Client(
        auth=(env.key, env.keyid))
    js = client.invoice.fetch_all()
    d = dict()
    for i in js['items']:
        for j in i['line_items']:
            num_days = calcDays(i['date'])
            if num_days <= 2629743:
                quant_last_30_days = j['quantity']
            else:
                quant_last_30_days = 0
            if j['name'] not in d:
                d[j['name']] = [j['description'], j['amount']/100,
                                j['quantity'], quant_last_30_days, j['net_amount']*j['quantity']/100]
            else:
                d[j['name']][2] += j['quantity']
                d[j['name']][3] += quant_last_30_days
                d[j['name']][4] += j['net_amount']*j['quantity']/100
    return render_template('topgrossing.html', d=d)


def calcDays(ts):
    curr = int(time.time())
    g = curr-ts
    return g


@ app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run(debug=True)
