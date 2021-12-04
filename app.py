from flask import Flask, render_template, request, redirect, session
import razorpay
import time
import requests
import json
import env
import pyodbc
from werkzeug.exceptions import HTTPException
import datetime

app = Flask(__name__)
app.secret_key = env.secret

conn = pyodbc.connect('DRIVER='+env.driver+';SERVER=tcp:'+env.server +';PORT=1433;DATABASE='+env.database+';UID='+env.username+';PWD=' + env.password)
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
    if session['user']!='' and session['pass']!='':
        client = razorpay.Client(auth=(env.key, env.keyid))
        data = client.invoice.fetch_all()
        d = dict()
        d['monthly_sales'] = 0
        d['annual_sales'] = 0
        d['daily_orders'] = 0
        d['monthly_orders'] = 0
        chart_data = [0]*12
        for i in data['items']:
            num_days = calcDays(i['date'])
            month = int(datetime.datetime.fromtimestamp(int(i['date'])).strftime('%m')) - 1
            chart_data[month] += int(i['amount']/100)
            for j in i['line_items']:
                if num_days <= 2629743:
                    d['monthly_sales'] += j['net_amount']*j['quantity']/100
                if num_days <= 31536000:
                    d['annual_sales'] += j['net_amount']*j['quantity']/100
            if num_days <= 2629743:
                d['monthly_orders'] += 1
            if num_days <= 86400:
                d['daily_orders'] += 1
        d['chart_data'] = chart_data
        return render_template('dashboard.html', data=d)
    else:
        return render_template('404.html'), 404


@app.route("/easyinvoice.html", methods=['GET', 'POST'])
def get_data():
    url = "https://api.razorpay.com/v1/items?count=100"
    files=[]
    headers = {
        'Authorization': 'Basic cnpwX3Rlc3RfcW55WVp4azhHSm5zSjc6MHJtcThzU29YTTZEWHRRSHJFR2xwUndK'
    }
    response = requests.request("GET", url, headers=headers,files=files)
    data = json.loads(response.text)
    return render_template('easyinvoice.html', data=data['items'])

@app.route("/add",methods=['GET','POST'])
def add():
    pass

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
        final_amt = []
        for i in range(0, len(qty)):
            final_amt.append(int(qty[i]) * int(amt[i]))

        final_amt = [i for i in final_amt if i != 0]
        total_amt = 0
        for i in final_amt:
            total_amt = total_amt + i
    return render_template('cart.html', cust_name=cust_name, cust_phone=cust_phone, cust_email=cust_email, selected_item=selected_item, final_amt=final_amt, qty=qty, total_amt=total_amt, product_name=product_name)


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
        client = razorpay.Client(
            auth=(session['key'], session['pvtkey']))
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

# @app.errorhandler(Exception)
# def handle_exception(e):
#     # pass through HTTP errors
#     if isinstance(e, HTTPException):
#         return e

#     # now you're handling non-HTTP exceptions only
#     return render_template("login.html", e=e), 500

if __name__ == "__main__":
    app.run(debug=True)
