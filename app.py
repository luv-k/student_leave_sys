import os
import sqlite3
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_from_directory, abort, session
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import config

# --------------------------------------------------------------------------------------
# APP SETUP
# --------------------------------------------------------------------------------------
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024  # 4 MB

# --------------------------------------------------------------------------------------
# DATABASE HELPERS
# --------------------------------------------------------------------------------------
def get_users_db():
    conn = sqlite3.connect(config.USERS_DATABASE)  # Separate DB
    conn.row_factory = sqlite3.Row
    return conn

def get_leaves_db():
    conn = sqlite3.connect(config.LEAVES_DATABASE)  # Separate DB
    conn.row_factory = sqlite3.Row
    return conn

# --------------------------------------------------------------------------------------
# INIT DBs
# --------------------------------------------------------------------------------------
def init_db():
    # Users DB
    conn = get_users_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
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
            status TEXT DEFAULT 'Pending'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --------------------------------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------------------------------
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

# --------------------------------------------------------------------------------------
# AUTH ROUTES
# --------------------------------------------------------------------------------------
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
        role = request.form["role"]

        hashed_pw = generate_password_hash(password)

        conn = get_users_db()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                      (username, hashed_pw, role))
            conn.commit()
            flash("Registration successful. You may now login.", "success")
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

# --------------------------------------------------------------------------------------
# STUDENT PAGE
# --------------------------------------------------------------------------------------
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

    conn = get_leaves_db()
    conn.execute(
        "INSERT INTO leaves (name,student_id,class,reason,photo) VALUES (?,?,?,?,?)",
        (name,student_id,student_class,reason,photo_filename)
    )
    conn.commit()
    conn.close()
    flash("Leave request submitted!", "success")
    return redirect("/student")

# --------------------------------------------------------------------------------------
# ADMIN PAGE
# --------------------------------------------------------------------------------------
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
        # Ask for admin password first
        return render_template("admin_password_confirm.html", action="approve", leave_id=leave_id)
    
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
    
    conn = get_leaves_db()
    conn.execute("UPDATE leaves SET status='Approved' WHERE id=?",(leave_id,))
    conn.commit()
    conn.close()
    flash("Leave approved.", "success")
    return redirect("/admin")

@app.route("/admin/reject/<int:leave_id>", methods=["POST","GET"])
@login_required(role="admin")
def reject(leave_id):
    if request.method=="GET":
        return render_template("admin_password_confirm.html", action="reject", leave_id=leave_id)

    password = request.form.get("password","")
    conn = get_users_db()
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE id=?",(session["user_id"],))
    user = c.fetchone()
    conn.close()
    if not check_password_hash(user["password"], password):
        flash("Incorrect admin password.", "danger")
        return redirect("/admin")
    
    conn = get_leaves_db()
    conn.execute("UPDATE leaves SET status='Rejected' WHERE id=?",(leave_id,))
    conn.commit()
    conn.close()
    flash("Leave rejected.", "warning")
    return redirect("/admin")

# --------------------------------------------------------------------------------------
# FILE SERVING
# --------------------------------------------------------------------------------------
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    if '..' in filename or filename.startswith('/'):
        abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --------------------------------------------------------------------------------------
# RUN
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
