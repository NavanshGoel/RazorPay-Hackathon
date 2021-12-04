from flask import Flask, render_template, request, redirect, session
import razorpay
import time
import requests
import json
import env
import pyodbc
from werkzeug.exceptions import HTTPException
import datetime
import base64
import collections

app = Flask(__name__)
app.secret_key = env.secret

conn = pyodbc.connect('DRIVER='+env.driver+';SERVER=tcp:'+env.server +
                      ';PORT=1433;DATABASE='+env.database+';UID='+env.username+';PWD=' + env.password)
cursor = conn.cursor()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/index.html')
def ind():
    return render_template('index.html')


@app.route('/logout')
def logout():
    session['user'] = ''
    session['pass'] = ''
    session['key'] = ''
    session['pvtkey'] = ''
    return redirect('/index.html')


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
            session['user'] = username
            session['pass'] = password
            session['key'] = row[10]
            session['pvtkey'] = row[11]
            return redirect('/dashboard.html')
        else:
            return render_template('login.html', err="Invalid Credentials")


@app.route('/forgot-password.html')
def forgot_password():
    return render_template('forgot-password.html')


@app.route('/register.html', methods=['GET', 'POST'])
def register():
    return render_template('register.html')


@app.route('/validation1', methods=['GET', 'POST'])
def validation1():
    if request.method == 'POST':
        username = request.form['email']
        password = request.form['password']
        repass = request.form['password_repeat']
        if password != repass:
            return render_template('register.html', err="Invalid Credentials")
        fname = request.form['first_name']
        lname = request.form['last_name']
        city = request.form['city']
        country = request.form['country']
        addr = request.form['addr']
        key = request.form['keyid']
        pvtkey = request.form['pvtkey']
        sname = request.form['sname']
        cursor.execute("INSERT INTO utable (email, password, fname, lname, city, country, addr, keyid, keypr, sname) VALUES (?,?,?,?,?,?,?,?,?,?)",
                       username, password, fname, lname, city, country, addr, key, pvtkey, sname)
        cursor.commit()
        return redirect('/login.html')


@app.route('/dashboard.html')
def dashboard():
    if session['user'] != '' and session['pass'] != '':
        url = "https://api.razorpay.com/v1/invoices?count=100"
        s = session['key']+':'+session['pvtkey']
        en = s.encode("ascii")
        f = str(base64.b64encode(en).decode("utf-8"))
        files = []
        headers = {
            'Authorization': 'Basic '+f
        }
        response = requests.request("GET", url, headers=headers, files=files)

        # initialization of dictionary items
        data = json.loads(response.text)
        d = dict()
        d['monthly_sales'] = 0
        d['annual_sales'] = 0
        d['daily_orders'] = 0
        d['monthly_orders'] = 0
        chart_data = [0]*12
        pie_data = dict()
        for i in data['items']:
            num_days = calcDays(i['date'])
            month = int(datetime.datetime.fromtimestamp(
                int(i['date'])).strftime('%m')) - 1
            chart_data[month] += int(i['amount']/100)
            for j in i['line_items']:
                if num_days <= 2629743:
                    # updating monthly revenue
                    d['monthly_sales'] += j['amount']*j['quantity']/100
                    # updating the pie data
                    if j['name'] not in pie_data:
                        pie_data[j['name']] = j['amount']*j['quantity']/100
                    else:
                        pie_data[j['name']] += j['amount']*j['quantity']/100
                if num_days <= 31536000:
                    d['annual_sales'] += j['amount']*j['quantity']/100
            # updating number of orders daily and monthly
            if num_days <= 2629743:
                d['monthly_orders'] += 1
            if num_days <= 86400:
                d['daily_orders'] += 1
        d['chart_data'] = chart_data

        final_pie_data = calculate_top_products_monthly(pie_data)

        d['pie_data_keys'] = json.dumps(list(final_pie_data.keys()))
        d['pie_data_keys_list'] = list(final_pie_data.keys())
        d['pie_data_values'] = list(final_pie_data.values())

        return render_template('dashboard.html', data=d)
    else:
        return render_template('404.html'), 404


def calculate_top_products_monthly(pie_data):
    sorted_pie_data = collections.OrderedDict(
        sorted(pie_data.items(), key=lambda kv: kv[1], reverse=True))
    final_pie_data = dict()
    others = 0
    counter = 0
    for i in sorted_pie_data.keys():
        counter += 1
        if counter <= 5:
            final_pie_data[i] = int(sorted_pie_data[i])
        else:
            others += int(sorted_pie_data[i])

    final_pie_data['Others'] = others
    return final_pie_data


@app.route("/easyinvoice.html", methods=['GET', 'POST'])
def get_data():
    url = "https://api.razorpay.com/v1/items?count=100"
    s = session['key']+':'+session['pvtkey']
    en = s.encode("ascii")
    f = str(base64.b64encode(en).decode("utf-8"))
    files = []
    headers = {
        'Authorization': 'Basic '+f
    }
    response = requests.request("GET", url, headers=headers, files=files)
    data = json.loads(response.text)
    return render_template('easyinvoice.html', data=data['items'])


@app.route("/add", methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        item_name = request.form['item_name']
        item_desc = request.form['item_desc']
        item_price = request.form['item_price']*100
        url = "https://api.razorpay.com/v1/items"
        s = session['key']+':'+session['pvtkey']
        en = s.encode("ascii")
        f = str(base64.b64encode(en).decode("utf-8"))
        files = []
        payload = {'name': item_name,
                   'description': item_desc,
                   'amount': item_price,
                   'currency': 'INR'}
        headers = {
            'Authorization': 'Basic '+f
        }

        response = requests.request(
            "POST", url, headers=headers, data=payload, files=files)
        print(response)
    return redirect('easyinvoice.html')


@app.route("/invoice", methods=['GET', 'POST'])
def invoice():
    if request.method == 'POST':
        cust_name = request.form.get("cust_name")
        cust_phone = request.form.get("cust_phone")
        cust_email = request.form.get("cust_email")
        selected_item = request.form.getlist("itemCheck")
        product_name = request.form.getlist("pname")
        qty = request.form.getlist('qty')
        amt = request.form.getlist('amt')
        client = razorpay.Client(auth=(session['key'], session['pvtkey']))
        l = []
        fq = [int(i) for i in qty if i != '0']
        if len(fq) == 0:
            return redirect('easyinvoice.html')
        DATA = {
            "type": "invoice",
            "description": "Invoice for shopping list",
            "partial_payment": True,
            "customer": {
                "name": cust_name,
                "contact": cust_phone,
                "email": cust_email
            },
            "line_items": [{"item_id": selected_item[i],
                            "quantity": fq[i]} for i in range(len(fq))],
            "sms_notify": 1,
            "email_notify": 1,
            "currency": "INR"
        }
        client.invoice.create(data=DATA)
        return redirect('easyinvoice.html')


@app.route("/cart.html", methods=['GET', 'POST'])
def send_data():
    if request.method == 'POST':
        cust_name = request.form.get("cust_name")
        cust_phone = request.form.get("cust_phone")
        cust_email = request.form.get("cust_email")
        selected_item = request.form.getlist("itemCheck")
        product_name = request.form.getlist("pname")
        qty = request.form.getlist('qty')
        amt = request.form.getlist('amt')
        itemid = request.form.getlist("itemid")
        final_amt = []
        for i in range(0, len(qty)):
            final_amt.append(int(qty[i]) * int(amt[i]))

        final_amt = [i for i in final_amt if i != 0]
        total_amt = 0
        for i in final_amt:
            total_amt = total_amt + i
    return render_template('cart.html', cust_name=cust_name, cust_phone=cust_phone, cust_email=cust_email, selected_item=selected_item, final_amt=final_amt, qty=qty, total_amt=total_amt, product_name=product_name, itemid=itemid)


@app.route('/profile.html')
def profile():
    if session['user'] != '' and session['pass'] != '':
        cursor.execute(
            "SELECT * FROM utable WHERE email = ? AND password = ?", session['user'], session['pass'])
        row = cursor.fetchone()
        print(row)
        return render_template('profile.html', fname=row[0], lname=row[1], email=row[2], user=row[2], addr=row[5], sname=row[6], cno=row[7], city=row[8], country=row[9], key=row[10], keyid=row[11])
    else:
        return render_template('404.html'), 404


@app.route('/topgrossing.html')
def topgrossing():
    if session['user'] != '' and session['pass'] != '':
        url = "https://api.razorpay.com/v1/invoices?count=100"
        s = session['key']+':'+session['pvtkey']
        en = s.encode("ascii")
        f = str(base64.b64encode(en).decode("utf-8"))
        files = []
        headers = {
            'Authorization': 'Basic '+f
        }
        response = requests.request("GET", url, headers=headers, files=files)

        # initialization of dictionary items
        js = json.loads(response.text)
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
                                    j['quantity'], quant_last_30_days, j['amount']*j['quantity']/100]
                else:
                    d[j['name']][2] += j['quantity']
                    d[j['name']][3] += quant_last_30_days
                    d[j['name']][4] += j['amount']*j['quantity']/100
        return render_template('topgrossing.html', d=d)


def calcDays(ts):
    curr = int(time.time())
    g = curr-ts
    return g


@ app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return e

    # now you're handling non-HTTP exceptions only
    return render_template("login.html", e=e), 500


if __name__ == "__main__":
    app.run(debug=True)
