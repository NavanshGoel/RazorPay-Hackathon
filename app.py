from flask import Flask, render_template, request, redirect, session
import razorpay
import time
import requests
import json
import env
import pyodbc

app = Flask(__name__)
app.secret_key = env.secret

conn = pyodbc.connect('DRIVER='+env.driver+';SERVER=tcp:'+env.server +
                      ';PORT=1433;DATABASE='+env.database+';UID='+env.username+';PWD=' + env.password)
cursor = conn.cursor()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/logout')
def logout():
    session['user']='' 
    session['pass']=''
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
            session['user']=username
            session['pass']=password
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
        repass= request.form['repeat_password']
        if password!=repass:
            return render_template('register.html',err="Invalid Credentials")
        fname=request.form['first_name']
        lname=request.form['last_name']
        city=request.form['city']
        



@app.route('/dashboard.html')
def dashboard():
    if session['user']!='' and session['pass']!='':
        return render_template('dashboard.html')
    else:
        return render_template('404.html'), 404


@app.route("/easyinvoice.html", methods=['GET', 'POST'])
def get_data():
    req = requests.get(
        'https://raw.githubusercontent.com/ashank2603/RazorPay-Hackathon/main/items.json')
    data = json.loads(req.content)
    return render_template('easyinvoice.html', data=data['items'])


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
    return render_template('cart.html', cust_name=cust_name, cust_phone=cust_phone, cust_email=cust_email, selected_item=selected_item, final_amt=final_amt, qty=qty, total_amt=total_amt, product_name = product_name)


@app.route('/profile.html')
def profile():
    if session['user']!='' and session['pass']!='':
        cursor.execute(
            "SELECT * FROM utable WHERE email = ? AND password = ?", session['user'], session['pass'])
        row = cursor.fetchone()
        print(row)
        return render_template('profile.html',fname=row[0],lname=row[1],email=row[2],user=row[2],addr=row[6],sname=row[7],cno=row[8],city=row[9],country=row[10],key=row[11],keyid=row[12])
    else:
        return render_template('404.html'), 404



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
