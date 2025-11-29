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

