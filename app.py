from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from backend.database import get_db, init_db, seed_db
from backend.recommendations import get_recommendations
from backend.chatbot import answer
from backend.quiz import get_quiz, grade_quiz

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.environ.get("MONEYWISE_SECRET_KEY") or "dev-only-change-this-secret"
app.config["DATABASE"] = "database/moneywise.db"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("RENDER") == "true"

with app.app_context():
    init_db()
    seed_db()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def current_user():
    if "user_id" not in session:
        return None
    db = get_db()
    return db.execute("SELECT id, name, email FROM users WHERE id=?", (session["user_id"],)).fetchone()

@app.context_processor
def inject_user():
    return {"current_user": current_user()}

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        if not name or not email or len(password) < 6:
            flash("Please enter a name, valid email, and password of at least 6 characters.", "error")
            return render_template("register.html")
        db = get_db()
        try:
            cur = db.execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",
                             (name, email, generate_password_hash(password)))
            db.commit()
            session.clear()
            session["user_id"] = cur.lastrowid
            session.modified = True
            return redirect(url_for("dashboard"))
        except Exception:
            flash("That email is already registered.", "error")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session.modified = True
            return redirect(url_for("dashboard"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")

@app.route("/switch-account")
def switch_account():
    session.clear()
    session.modified = True
    flash("Previous account signed out. You can now log in with another account.", "success")
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    session.modified = True
    return redirect(url_for("index"))

def financial_data(uid):
    db = get_db()
    income = db.execute("SELECT COALESCE(SUM(amount),0) total FROM transactions WHERE user_id=? AND type='income'", (uid,)).fetchone()["total"]
    expenses = db.execute("SELECT COALESCE(SUM(amount),0) total FROM transactions WHERE user_id=? AND type='expense'", (uid,)).fetchone()["total"]
    saved = db.execute("SELECT COALESCE(SUM(amount),0) total FROM savings WHERE user_id=?", (uid,)).fetchone()["total"]
    balance = income - expenses - saved
    goals = db.execute("SELECT * FROM saving_goals WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()
    categories = db.execute("""SELECT category, COALESCE(SUM(amount),0) amount
        FROM transactions WHERE user_id=? AND type='expense'
        GROUP BY category ORDER BY amount DESC""", (uid,)).fetchall()
    return {"income": income, "expenses": expenses, "saved": saved, "balance": balance,
            "goals": goals, "categories": categories}

@app.route("/dashboard")
@login_required
def dashboard():
    uid = session["user_id"]
    data = financial_data(uid)
    return render_template("dashboard.html", data=data, recommendations=get_recommendations(uid))

@app.route("/wallet", methods=["GET","POST"])
@login_required
def wallet():
    db = get_db(); uid = session["user_id"]
    if request.method == "POST":
        try:
            amount = float(request.form["amount"]); typ = request.form["type"]
            category = request.form.get("category","General"); note = request.form.get("note","").strip()
            if amount <= 0 or typ not in ("income","expense"): raise ValueError()
            db.execute("""INSERT INTO transactions(user_id,type,amount,category,note,created_at)
                         VALUES(?,?,?,?,?,?)""",
                       (uid,typ,amount,category,note,datetime.now().isoformat(timespec="seconds")))
            db.commit(); flash("Transaction added.", "success")
        except (ValueError, KeyError):
            flash("Enter a valid amount and transaction type.", "error")
        return redirect(url_for("wallet"))
    tx = db.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()
    return render_template("wallet.html", transactions=tx, data=financial_data(uid))

@app.route("/transaction/delete/<int:txid>", methods=["POST"])
@login_required
def delete_transaction(txid):
    db = get_db()
    db.execute("DELETE FROM transactions WHERE id=? AND user_id=?", (txid, session["user_id"]))
    db.commit()
    return redirect(request.referrer or url_for("wallet"))

@app.route("/expenses")
@login_required
def expenses():
    db = get_db(); uid = session["user_id"]
    rows = db.execute("SELECT * FROM transactions WHERE user_id=? AND type='expense' ORDER BY created_at DESC", (uid,)).fetchall()
    return render_template("expenses.html", rows=rows, data=financial_data(uid))

@app.route("/savings", methods=["GET","POST"])
@login_required
def savings():
    db = get_db(); uid = session["user_id"]
    if request.method == "POST":
        try:
            amount = float(request.form["amount"]); note = request.form.get("note","").strip()
            if amount <= 0: raise ValueError()
            db.execute("INSERT INTO savings(user_id,amount,note,created_at) VALUES(?,?,?,?)",
                       (uid,amount,note,datetime.now().isoformat(timespec="seconds")))
            db.commit(); flash("Savings entry added.", "success")
        except (ValueError, KeyError):
            flash("Enter a positive savings amount.", "error")
        return redirect(url_for("savings"))
    rows = db.execute("SELECT * FROM savings WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()
    return render_template("savings.html", rows=rows, data=financial_data(uid))

@app.route("/goals", methods=["GET","POST"])
@login_required
def goals():
    db = get_db(); uid = session["user_id"]
    if request.method == "POST":
        try:
            name = request.form["name"].strip(); target = float(request.form["target"])
            current = float(request.form.get("current",0) or 0); deadline = request.form.get("deadline","") or None
            if not name or target <= 0 or current < 0: raise ValueError()
            db.execute("""INSERT INTO saving_goals(user_id,name,target_amount,current_amount,deadline,created_at)
                          VALUES(?,?,?,?,?,?)""",
                       (uid,name,target,current,deadline,datetime.now().isoformat(timespec="seconds")))
            db.commit(); flash("Saving goal created.", "success")
        except (ValueError, KeyError):
            flash("Please enter a valid goal.", "error")
        return redirect(url_for("goals"))
    goals = db.execute("SELECT * FROM saving_goals WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()
    return render_template("goals.html", goals=goals)

@app.route("/goals/<int:gid>/add", methods=["POST"])
@login_required
def add_goal_progress(gid):
    try:
        amount = float(request.form["amount"])
        if amount <= 0: raise ValueError()
        db = get_db()
        db.execute("UPDATE saving_goals SET current_amount=MIN(target_amount,current_amount+?) WHERE id=? AND user_id=?",
                   (amount,gid,session["user_id"]))
        db.commit()
    except (ValueError, KeyError):
        flash("Enter a valid amount.", "error")
    return redirect(url_for("goals"))

@app.route("/learning")
@login_required
def learning():
    db = get_db()
    skills = db.execute("SELECT * FROM skills ORDER BY id").fetchall()
    sources = db.execute("SELECT * FROM learning_sources ORDER BY skill_id, title").fetchall()
    projects = db.execute("SELECT * FROM projects ORDER BY skill_id, id").fetchall()
    return render_template("learning.html", skills=skills, sources=sources, projects=projects)

@app.route("/skills")
@login_required
def skills():
    db = get_db(); uid = session["user_id"]
    skills = db.execute("SELECT * FROM skills ORDER BY id").fetchall()
    progress = {r["skill_id"]: r["completed"] for r in db.execute(
        "SELECT skill_id, completed FROM user_skill_progress WHERE user_id=?", (uid,)).fetchall()}
    return render_template("skills.html", skills=skills, progress=progress,
                           recommendations=get_recommendations(uid))

@app.route("/skills/<int:sid>/complete", methods=["POST"])
@login_required
def complete_skill(sid):
    db = get_db()
    db.execute("""INSERT INTO user_skill_progress(user_id,skill_id,completed)
                  VALUES(?,?,1) ON CONFLICT(user_id,skill_id) DO UPDATE SET completed=1""",
               (session["user_id"],sid))
    db.commit()
    return redirect(url_for("skills"))

@app.route("/quiz")
@login_required
def quiz():
    return render_template("quiz.html", questions=get_quiz())

@app.route("/quiz/submit", methods=["POST"])
@login_required
def quiz_submit():
    answers = {int(k): v for k,v in request.form.items() if k.isdigit()}
    result = grade_quiz(answers)
    db = get_db()
    db.execute("INSERT INTO quiz_results(user_id,score,total,created_at) VALUES(?,?,?,?)",
               (session["user_id"],result["score"],result["total"],datetime.now().isoformat(timespec="seconds")))
    db.commit()
    return render_template("quiz_result.html", result=result)

@app.route("/chatbot", methods=["GET","POST"])
@login_required
def chatbot():
    history = session.get("chat_history", [])
    if request.method == "POST":
        msg = request.form.get("message","").strip()
        if msg:
            reply = answer(msg, session["user_id"])
            history.append({"user":msg, "bot":reply})
            session["chat_history"] = history[-12:]
            session.modified = True
    return render_template("chatbot.html", history=history)

@app.route("/api/summary")
@login_required
def api_summary():
    data = financial_data(session["user_id"])
    return jsonify({"income":data["income"],"expenses":data["expenses"],"saved":data["saved"],"balance":data["balance"],
                    "categories":[{"category":r["category"],"amount":r["amount"]} for r in data["categories"]]})

if __name__ == "__main__":
    app.run(debug=True)
