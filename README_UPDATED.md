# Student Leave System

Small Flask app for students to submit leave requests and for admins to approve or reject them.

## Features

- Student registration & login
- Admin registration & login
- Submit leave requests (name, student ID, class, reason) with optional photo upload
- Role-based access control
- Admin approval/rejection with password confirmation

## Quick setup (Windows PowerShell)

1. Create / activate virtual environment (this project uses `.app` in the workspace, but any venv name is fine):

```powershell
python -m venv .app
.\.app\Scripts\Activate.ps1
```

2. Install dependencies and run:

```powershell
pip install -r requirements.txt
python app.py
```

3. Open the app in your browser:

```
http://127.0.0.1:5000/
```

## Important environment variables

- `SECRET_KEY` — change for production (overrides default in `config.py`)
- `MAIL_SENDER` — sender email address used for notification emails (e.g. `lavishjangra534@gmail.com`)
- `MAIL_PASSWORD` — email SMTP password or App Password (for Gmail create an App Password; do NOT use your regular Google password)
- `MAIL_SMTP_SERVER` and `MAIL_SMTP_PORT` — optional, defaults to Gmail (`smtp.gmail.com:587`)

Set them in PowerShell before running the app (temporary for the session):

```powershell
$env:MAIL_SENDER = 'you@example.com'
$env:MAIL_PASSWORD = 'your-app-password'
python app.py
```

## Databases and uploads

- `users.db` — stores user accounts (created automatically)
- `leaves.db` — stores leave requests and status (`Pending`, `Approved`, `Rejected`)
- `uploads/` — folder for uploaded photos (created automatically)

Approved/rejected requests are kept in the DB for history; student portal only shows the logged-in student's pending requests.

## Notes / Production

- Passwords are hashed using Werkzeug. Keep `SECRET_KEY` secret in production.
- Run behind a production WSGI server (Gunicorn / Waitress) — do not use Flask's dev server in production.
- For better deliverability and ease, consider using a transactional email provider (SendGrid, Mailgun) in production.

## Contributing / Next steps

- To add email testing, set `MAIL_SENDER` and `MAIL_PASSWORD` and use the app's flows; I can add a `send_test.py` helper on request.

---
Small, focused README additions were created to clarify setup and environment variables. No functionality changes were made.
