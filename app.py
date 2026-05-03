from flask import Flask, render_template, request, redirect, session
import sqlite3
import hashlib
import pickle
import numpy as np
import os

app = Flask(__name__)
app.secret_key = "flow_secret"

# 🔥 LOAD MODEL
try:
    model = pickle.load(open("model.pkl", "rb"))
except:
    model = None

# ---------------- USER DB ----------------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT UNIQUE, password TEXT)")
    conn.commit()
    conn.close()

init_db()

# ---------------- HISTORY DB ----------------
def init_history():
    conn = sqlite3.connect("history.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS history(income INT, loan INT, cibil INT, result TEXT)")
    conn.commit()
    conn.close()

init_history()

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("login.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    u = request.form["username"]
    p = hash_pw(request.form["password"])

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (u,))
    user = c.fetchone()

    if not user:
        return render_template("login.html", error="❌ User not found")

    if user[1] != p:
        return render_template("login.html", error="❌ Incorrect Password")

    session["user"] = u
    return redirect("/dashboard")

# ---------------- REGISTER (🔥 FIXED) ----------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        u = request.form["username"]
        p = hash_pw(request.form["password"])

        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users VALUES(?,?)", (u,p))
            conn.commit()
            conn.close()
            return render_template("login.html", success="✅ Registered successfully")

        except:
            conn.close()
            return render_template("login.html", error="❌ User already exists")

    return redirect("/")

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
                           loan=0,
                           reason="",
                           suggestion="",
                           cibil=0)

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
            ml_pred = model.predict(np.array([[income, loan, cibil]]))[0]
        except:
            ml_pred = 1
    else:
        ml_pred = 1

    # ---- DECISION LOGIC ----
    if cibil < 550:
        result = "❌ Rejected (Low CIBIL)"
        prob = 30
        reason = "Low credit score"
        suggestion = "Improve CIBIL score"
        approved, rejected = 0, 1

    elif emi > (0.6 * monthly_income):
        result = "❌ Rejected (High EMI)"
        prob = 35
        reason = "EMI too high"
        suggestion = "Reduce loan amount"
        approved, rejected = 0, 1

    else:
        if ml_pred == 1:
            result = "✅ Approved"
            prob = 90
            reason = "Strong profile"
            suggestion = "Eligible"
            approved, rejected = 1, 0
        else:
            result = "❌ Rejected"
            prob = 50
            reason = "Model rejection"
            suggestion = "Improve profile"
            approved, rejected = 0, 1

        if existing_loan == 1:
            prob -= 10

        if job == 0:
            if cibil >= 750 and loan < income * 2:
                result = "✅ Approved (No Job Strong)"
                prob = 70
                reason = "High CIBIL compensates"
                suggestion = "Maintain stability"
                approved, rejected = 1, 0
            else:
                result = "❌ Rejected (No Job Risk)"
                prob = 40
                reason = "No job risk"
                suggestion = "Get stable income"
                approved, rejected = 0, 1

    # ---- SAVE HISTORY ----
    conn = sqlite3.connect("history.db")
    c = conn.cursor()
    c.execute("INSERT INTO history VALUES (?,?,?,?)", (income, loan, cibil, result))
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