import os
import sqlite3
from flask import (Flask, render_template, request, redirect, url_for,flash, send_from_directory, abort, session)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import config
import mail


# APP SETUP

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024  # 4 MB


# DATABASE HELPERS

def get_users_db():
    conn = sqlite3.connect(config.USERS_DATABASE)  # Separate DB
    conn.row_factory = sqlite3.Row
    return conn

def get_leaves_db():
    conn = sqlite3.connect(config.LEAVES_DATABASE)  # Separate DB
    conn.row_factory = sqlite3.Row
    return conn


# INIT DBs

def init_db():
    # Users DB
    conn = get_users_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT
        )
    """)
    # ensure email column exists (for upgrades)
    cols = [r[1] for r in c.execute("PRAGMA_TABLE_INFO('users')").fetchall()] if False else None
    # SQLite PRAGMA returns rows differently via python; safer to try add column if not exists
    try:
        c.execute("ALTER TABLE users ADD COLUMN email TEXT")
    except Exception:
        pass
    conn.commit()
    conn.close()

    # Leaves DB
    conn = get_leaves_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            student_id TEXT NOT NULL,
            class TEXT,
            reason TEXT,
            photo TEXT,
            email TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    try:
        c.execute("ALTER TABLE leaves ADD COLUMN email TEXT")
    except Exception:
        pass
    conn.commit()
    conn.close()

init_db()

# HELPERS
# 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

def login_required(role=None):
    def wrapper(fn):
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return redirect("/login")
            if role and session.get("role") != role:
                flash("Unauthorized access!", "danger")
                return redirect("/")
            return fn(*args, **kwargs)
        decorated.__name__ = fn.__name__
        return decorated
    return wrapper


# AUTH ROUTES
 
@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/admin" if session["role"] == "admin" else "/student")
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_users_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect("/admin" if user["role"]=="admin" else "/student")

        flash("Invalid username or password", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form.get("email",""
                                ).strip()
        role = request.form["role"]

        hashed_pw = generate_password_hash(password)

        conn = get_users_db()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username,password,role,email) VALUES (?,?,?,?,)"[:0] + "INSERT INTO users (username,password,role,email) VALUES (?,?,?,?)",
                      (username, hashed_pw, role, email))
            conn.commit()
            flash("Registration successful. You may now login.", "success")
            # send welcome email if configured
            sender = getattr(config, "MAIL_SENDER", "")
            if sender and email:
                try:
                    mail.send_email(sender, email, subject="Welcome to Student Leave System", body=f"Hello {username},\n\nYour account has been created.\n\nRegards,\nAdmin")
                except Exception as e:
                    print(f"Failed to send welcome email: {e}")
            return redirect("/login")
        except sqlite3.IntegrityError:
            flash("Username already exists.", "danger")
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# STUDENT PAGE

@app.route("/student")
@login_required(role="student")
def student_page():
    conn = get_leaves_db()
    leaves = conn.execute("SELECT * FROM leaves ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("student.html", leaves=leaves)

@app.route("/submit", methods=["POST"])
@login_required(role="student")
def submit():
    name = request.form.get("name","").strip()
    student_id = request.form.get("student_id","").strip()
    student_class = request.form.get("class","").strip()
    reason = request.form.get("reason","").strip()
    if not name or not student_id or not reason:
        flash("Name, student ID, and reason are required.", "danger")
        return redirect("/student")

    photo_filename = None
    photo = request.files.get("photo")
    if photo and photo.filename:
        if not allowed_file(photo.filename):
            flash("Invalid photo type.", "danger")
            return redirect("/student")
        filename = f"{os.urandom(8).hex()}_{secure_filename(photo.filename)}"
        photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        photo_filename = filename

    # include user's email from users DB if available
    user_email = None
    if "user_id" in session:
        uc = get_users_db()
        cur = uc.cursor()
        cur.execute("SELECT email FROM users WHERE id=?", (session["user_id"],))
        urow = cur.fetchone()
        if urow:
            try:
                user_email = urow["email"]
            except Exception:
                user_email = urow[0]
        uc.close()

    conn = get_leaves_db()
    conn.execute(
        "INSERT INTO leaves (name,student_id,class,reason,photo,email) VALUES (?,?,?,?,?,?)",
        (name,student_id,student_class,reason,photo_filename,user_email)
    )
    conn.commit()
    conn.close()
    flash("Leave request submitted!", "success")
    return redirect("/student")


# ADMIN PAGE

@app.route("/admin")
@login_required(role="admin")
def admin_page():
    conn = get_leaves_db()
    leaves = conn.execute("SELECT * FROM leaves ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin.html", leaves=leaves)

@app.route("/admin/approve/<int:leave_id>", methods=["POST","GET"])
@login_required(role="admin")
def approve(leave_id):
    if request.method=="GET":
        # Ask for admin password first — include leave details for template
        conn = get_leaves_db()
        leave = conn.execute("SELECT * FROM leaves WHERE id=?", (leave_id,)).fetchone()
        conn.close()
        if not leave:
            flash("Leave request not found.", "danger")
            return redirect(url_for("admin_page"))
        return render_template("admin_password_confirm.html", action="approve", leave=leave, leave_id=leave_id)
    
    # POST: verify password
    password = request.form.get("password","")
    conn = get_users_db()
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE id=?",(session["user_id"],))
    user = c.fetchone()
    conn.close()
    if not check_password_hash(user["password"], password):
        flash("Incorrect admin password.", "danger")
        return redirect(url_for("admin_page"))
    
    # fetch leave details to notify student
    conn = get_leaves_db()
    cur = conn.cursor()
    cur.execute("SELECT name,email,reason FROM leaves WHERE id=?", (leave_id,))
    row = cur.fetchone()
    conn.execute("UPDATE leaves SET status='Approved' WHERE id=?",(leave_id,))
    conn.commit()
    conn.close()

    # send approval email if email available
    if row:
        try:
            # Use configured MAIL_SENDER from environment (no hard-coded address)
            sender = getattr(config, "MAIL_SENDER", "")
            recipient = None
            try:
                recipient = row[1] if isinstance(row, tuple) else row["email"]
            except Exception:
                recipient = row[1]
            student_name = row[0] if row else ''
            if not sender:
                # Mail sender not configured; skip sending but log
                print("MAIL_SENDER is not set; approval email skipped.")
            elif sender and recipient:
                mail.send_leave_approval(sender, recipient, student_name, row[2] or "")
        except Exception as e:
            print(f"Failed to send approval email: {e}")

    flash("Leave approved.", "success")
    return redirect("/admin")

@app.route("/admin/reject/<int:leave_id>", methods=["POST","GET"])
@login_required(role="admin")
def reject(leave_id):
    if request.method=="GET":
        # include leave details for template
        conn = get_leaves_db()
        leave = conn.execute("SELECT * FROM leaves WHERE id=?", (leave_id,)).fetchone()
        conn.close()
        if not leave:
            flash("Leave request not found.", "danger")
            return redirect(url_for("admin_page"))
        return render_template("admin_password_confirm.html", action="reject", leave=leave, leave_id=leave_id)

    password = request.form.get("password","")
    conn = get_users_db()
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE id=?",(session["user_id"],))
    user = c.fetchone()
    conn.close()
    if not check_password_hash(user["password"], password):
        flash("Incorrect admin password.", "danger")
        return redirect("/admin")
    
    # fetch leave details to notify student
    conn = get_leaves_db()
    cur = conn.cursor()
    cur.execute("SELECT name,email,reason FROM leaves WHERE id=?", (leave_id,))
    row = cur.fetchone()
    conn.execute("UPDATE leaves SET status='Rejected' WHERE id=?",(leave_id,))
    conn.commit()
    conn.close()

    # send rejection email if email available
    if row:
        try:
            sender = getattr(config, "MAIL_SENDER", "")
            recipient = None
            try:
                recipient = row[1] if isinstance(row, tuple) else row["email"]
            except Exception:
                recipient = row[1]
            student_name = row[0] if row else ''
            if sender and recipient:
                mail.send_leave_rejection(sender, recipient, student_name, reason=row[2] or "")
        except Exception as e:
            print(f"Failed to send rejection email: {e}")

    flash("Leave rejected.", "warning")
    return redirect("/admin")


@app.route("/admin/verify/<int:leave_id>/<action>", methods=["GET","POST"])
@login_required(role="admin")
def verify(leave_id, action):
    """
    Compatibility route used by the admin UI: /admin/verify/<id>/approve or /reject
    Delegates to the existing approve/reject handlers.
    """
    action = (action or "").lower()
    if action == "approve":
        return approve(leave_id)
    if action == "reject":
        return reject(leave_id)
    abort(404)


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    if '..' in filename or filename.startswith('/'):
        abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == "__main__":
    app.run(debug=True)
