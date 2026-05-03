from flask import Flask, render_template, request, redirect, session
import sqlite3
import hashlib
import pickle
import numpy as np

app = Flask(__name__)
app.secret_key = "flow_secret"

# 🔥 LOAD MODEL (safe)
try:
    model = pickle.load(open("model.pkl", "rb"))
except:
    model = None

# ---------------- USER DB ----------------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- HISTORY DB ----------------
def init_history():
    conn = sqlite3.connect("history.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS history(
            income INT,
            loan INT,
            cibil INT,
            result TEXT
        )
    """)
    conn.commit()
    conn.close()

init_history()

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("login.html")

# ---------------- LOGIN (🔥 UPDATED) ----------------
@app.route("/login", methods=["POST"])
def login():
    u = request.form["username"]
    p = hash_pw(request.form["password"])

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # 🔍 Check user exists
    c.execute("SELECT * FROM users WHERE username=?", (u,))
    user = c.fetchone()

    if not user:
        return render_template("login.html", error=" User not found")

    # 🔐 Check password
    if user[1] != p:
        return render_template("login.html", error=" Incorrect Password")

    # ✅ Success
    session["user"] = u
    return redirect("/dashboard")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    return render_template("index.html",
                           user=session["user"],
                           prediction_text="",
                           probability=0,
                           emi="",
                           interest_rate="",
                           tenure="",
                           approved=0,
                           rejected=0,
                           history=[],
                           income=0,
                           loan=0)

# ---------------- PREDICT ----------------
@app.route("/predict", methods=["POST"])
def predict():
    if "user" not in session:
        return redirect("/")

    income = int(request.form["income_annum"])
    loan = int(request.form["loan_amount"])
    cibil = int(request.form["cibil_score"])
    existing_loan = int(request.form.get("existing_loan", 0))
    job = int(request.form.get("job", 0))

    monthly_income = income

    if cibil >= 750:
        interest = 3
    elif cibil >= 700:
        interest = 4
    else:
        interest = 5

    tenure = 60

    r = interest / (12 * 100)
    emi = int((loan * r * (1 + r)**tenure) / ((1 + r)**tenure - 1))

    if model:
        try:
            input_data = np.array([[income, loan, cibil]])
            ml_pred = model.predict(input_data)[0]
        except:
            ml_pred = 1
    else:
        ml_pred = 1

    if cibil < 550:
        result = "❌ Rejected (Very Low CIBIL)"
        prob = 30
        reason = "Low Cibil Score"
        suggestion = "Improve credit score"
        approved = 0
        rejected = 1

    elif emi > (0.6 * monthly_income):
        result = "❌ Rejected (High EMI Risk)"
        prob = 35
        reason = "EMI too high compared to income"
        suggestion = "Reduce loan amount"
        approved = 0
        rejected = 1

    else:
        if ml_pred == 1:
            result = "✅ Approved"
            prob = 90
            reason = "Strong financial profile"
            suggestion = "Eligible for loan"
            approved = 1
            rejected = 0
        else:
            result = "❌ Rejected"
            prob = 50
            reason = "ML model rejection"
            suggestion = "Improve profile"
            approved = 0
            rejected = 1

        if existing_loan == 1:
            prob -= 10

        # 🔥 JOB LOGIC
        if job == 0:
            if cibil >= 750 and loan < (income * 2):
                result = "✅ Approved (Strong Profile, No Job)"
                prob = 70
                reason = "High CIBIL compensates for no job"
                suggestion = "Stable income recommended"
                approved = 1
                rejected = 0
            else:
                result = "❌ Rejected (No Job Risk)"
                prob = 40
                reason = "No job increases risk"
                suggestion = "Get stable income"
                approved = 0
                rejected = 1

    conn = sqlite3.connect("history.db")
    c = conn.cursor()
    c.execute("INSERT INTO history VALUES (?,?,?,?)",
              (income, loan, cibil, result))
    conn.commit()

    rows = c.execute("SELECT * FROM history").fetchall()
    conn.close()

    history = [{"income":r[0],"loan":r[1],"cibil":r[2],"result":r[3]} for r in rows]

    return render_template("index.html",
                           user=session["user"],
                           prediction_text=result,
                           probability=prob,
                           emi=emi,
                           interest_rate=interest,
                           tenure=tenure,
                           approved=approved,
                           rejected=rejected,
                           history=history,
                           income=income,
                           loan=loan,
                           reason=reason,
                           suggestion=suggestion,
                           cibil=cibil)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)