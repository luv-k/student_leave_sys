import os

# -----------------------------
# Flask Secret Key
# -----------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey123")  # change in production

# -----------------------------
# File Uploads
# -----------------------------
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------
# Databases
# -----------------------------
USERS_DATABASE = os.path.join(os.getcwd(), "users.db")   # login system
LEAVES_DATABASE = os.path.join(os.getcwd(), "leaves.db") # student leave requests

# -----------------------------
# Mail settings (use environment vars in production)
# -----------------------------
MAIL_SENDER = os.environ.get("MAIL_SENDER", "")
MAIL_SMTP_SERVER = os.environ.get("MAIL_SMTP_SERVER", "smtp.gmail.com")
MAIL_SMTP_PORT = int(os.environ.get("MAIL_SMTP_PORT", "587"))

