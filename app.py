import os
import hmac
import hashlib
import secrets
import smtplib
import ssl
import certifi
from datetime import datetime, timedelta
from email.message import EmailMessage
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import bcrypt
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET", "change-this-development-secret")


def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "registration"),
    )


CODE_TTL_MINUTES = 10
MAX_ATTEMPTS = 5


def hash_code(email, code):
    msg = f"{email.lower()}:{code}".encode("utf-8")
    return hmac.new(app.secret_key.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def send_code_email(to_email, code):
    sender = os.getenv("MAIL_USERNAME")
    msg = EmailMessage()
    msg["Subject"] = "Your verification code"
    msg["From"] = sender
    msg["To"] = to_email
    msg.set_content(
        f"Your verification code is: {code}\n\n"
        f"It expires in {CODE_TTL_MINUTES} minutes. "
        "If you didn't request this, ignore this email."
    )
    with smtplib.SMTP(os.getenv("MAIL_SERVER", "smtp.gmail.com"),
                      int(os.getenv("MAIL_PORT", "587")), timeout=15) as server:
        server.starttls(context=ssl.create_default_context(cafile=certifi.where()))
        server.login(sender, os.getenv("MAIL_APP_PASSWORD"))
        server.send_message(msg)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def index():
    return redirect(url_for("todos") if "user_id" in session else url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    errors = {}
    name = email = ""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not name: errors["name"] = "Name is required"
        if not email: errors["email"] = "Email is required"
        if not password: errors["password"] = "Password is required"
        if not confirm: errors["confirm_password"] = "Confirm password is required"
        if password and confirm and password != confirm:
            errors["confirm_password"] = "Passwords do not match"
        if not errors:
            conn = get_db()
            cur = conn.cursor()
            try:
                pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                cur.execute(
                    "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
                    (email, name, pw_hash)
                )
                conn.commit()
                cur.execute("SELECT user_id, name FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
                session.clear()
                session["user_id"], session["name"] = user[0], user[1]
                return redirect(url_for("todos"))
            except mysql.connector.IntegrityError:
                errors["email"] = "Email Already Exists"
            finally:
                cur.close()
                conn.close()
    return render_template("register.html", errors=errors, name=name, email=email)


@app.route("/login", methods=["GET", "POST"])
def login():
    errors = {}
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not email: errors["email"] = "Email is required"
        if not password: errors["password"] = "Password is required"
        if not errors:
            conn = get_db()
            cur = conn.cursor()
            try:
                cur.execute("SELECT user_id, name, password_hash FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
                valid = False
                if user:
                    try:
                        valid = bcrypt.checkpw(password.encode("utf-8"), user[2].encode("utf-8"))
                    except ValueError:
                        valid = False
                if valid:
                    session.clear()
                    session["user_id"], session["name"] = user[0], user[1]
                    return redirect(url_for("todos"))
                flash("Invalid email or password", "error")
            finally:
                cur.close()
                conn.close()
    return render_template("login.html", errors=errors, email=email)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    errors = {}
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if not email:
            errors["email"] = "Email is required"
        else:
            conn = get_db()
            cur = conn.cursor()
            try:
                cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
                if cur.fetchone():
                    code = f"{secrets.randbelow(10000):04d}"
                    cur.execute(
                        "DELETE FROM verification_codes WHERE email = %s AND purpose = 'reset_password'",
                        (email,))
                    cur.execute(
                        "INSERT INTO verification_codes (email, code_hash, purpose, expires_at) "
                        "VALUES (%s, %s, 'reset_password', %s)",
                        (email, hash_code(email, code),
                         datetime.now() + timedelta(minutes=CODE_TTL_MINUTES)))
                    conn.commit()
                    try:
                        send_code_email(email, code)
                    except Exception as e:
                        app.logger.error("Email sending failed: %s", e)
                        flash("Could not send the email. Try again later.", "error")
                        return render_template("forgot_password.html", errors=errors, email=email)
            finally:
                cur.close()
                conn.close()
            session["reset_email"] = email
            flash("If this email is registered, a 4-digit code has been sent.", "success")
            return redirect(url_for("verify_code"))
    return render_template("forgot_password.html", errors=errors, email=email)


@app.route("/verify-code", methods=["GET", "POST"])
def verify_code():
    email = session.get("reset_email")
    if not email:
        return redirect(url_for("forgot_password"))
    errors = {}
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        if not (code.isdigit() and len(code) == 4):
            errors["code"] = "Enter the 4-digit code"
        else:
            conn = get_db()
            cur = conn.cursor(dictionary=True)
            try:
                cur.execute(
                    "SELECT id, code_hash, expires_at, attempts FROM verification_codes "
                    "WHERE email = %s AND purpose = 'reset_password' AND used = 0 "
                    "ORDER BY id DESC LIMIT 1", (email,))
                row = cur.fetchone()
                if (not row or row["expires_at"] < datetime.now()
                        or row["attempts"] >= MAX_ATTEMPTS):
                    errors["code"] = "Code expired or too many attempts. Request a new code."
                elif hmac.compare_digest(row["code_hash"], hash_code(email, code)):
                    cur.execute("UPDATE verification_codes SET used = 1 WHERE id = %s", (row["id"],))
                    conn.commit()
                    session.pop("reset_email", None)
                    session["reset_verified_email"] = email
                    return redirect(url_for("reset_password"))
                else:
                    cur.execute("UPDATE verification_codes SET attempts = attempts + 1 WHERE id = %s",
                                (row["id"],))
                    conn.commit()
                    errors["code"] = "Incorrect code"
            finally:
                cur.close()
                conn.close()
    return render_template("verify_code.html", errors=errors)


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    email = session.get("reset_verified_email")
    if not email:
        return redirect(url_for("forgot_password"))
    errors = {}
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not password:
            errors["password"] = "Password is required"
        elif len(password) < 8:
            errors["password"] = "Password must be at least 8 characters"
        if not confirm:
            errors["confirm_password"] = "Confirm password is required"
        elif password and password != confirm:
            errors["confirm_password"] = "Passwords do not match"
        if not errors:
            pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            conn = get_db()
            cur = conn.cursor()
            try:
                cur.execute("UPDATE users SET password_hash = %s WHERE email = %s", (pw_hash, email))
                cur.execute("DELETE FROM verification_codes WHERE email = %s", (email,))
                conn.commit()
            finally:
                cur.close()
                conn.close()
            session.clear()
            flash("Password updated. Please log in.", "success")
            return redirect(url_for("login"))
    return render_template("reset_password.html", errors=errors)


@app.route("/todos", methods=["GET", "POST"])
@login_required
def todos():
    errors = {}
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            errors["title"] = "Title is required"
        elif len(title) > 200:
            errors["title"] = "Title is too long (200 characters at most)"
        else:
            conn = get_db()
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO todos (user_id, title) VALUES (%s, %s)", (session["user_id"], title))
                conn.commit()
            finally:
                cur.close()
                conn.close()
            return redirect(url_for("todos"))
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT todo_id, title, is_done, created_at FROM todos WHERE user_id = %s ORDER BY todo_id DESC",
            (session["user_id"],)
        )
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return render_template("todos.html", todos=rows, errors=errors, name=session.get("name", ""))


@app.route("/todos/<int:todo_id>/edit", methods=["POST"])
@login_required
def edit_todo(todo_id):
    title = request.form.get("title", "").strip()
    if not title:
        flash("Title is required", "error")
    elif len(title) > 200:
        flash("Title is too long (200 characters at most)", "error")
    else:
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE todos SET title = %s WHERE todo_id = %s AND user_id = %s",
                        (title, todo_id, session["user_id"]))
            conn.commit()
        finally:
            cur.close()
            conn.close()
    return redirect(url_for("todos"))


@app.route("/todos/<int:todo_id>/toggle", methods=["POST"])
@login_required
def toggle_todo(todo_id):
    state = 1 if request.form.get("is_done") == "1" else 0
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE todos SET is_done = %s WHERE todo_id = %s AND user_id = %s",
                    (state, todo_id, session["user_id"]))
        conn.commit()
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("todos"))


@app.route("/todos/<int:todo_id>/delete", methods=["POST"])
@login_required
def delete_todo(todo_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM todos WHERE todo_id = %s AND user_id = %s",
                    (todo_id, session["user_id"]))
        conn.commit()
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("todos"))


if __name__ == "__main__":
    app.run(debug=False)
