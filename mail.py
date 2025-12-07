import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config

"""
Mail module for sending pre-written emails.
"""

def send_email(sender_email, recipient_email, subject="Student Leave System Notification", body=""):
    """
    Send a pre-written email.
    
    Args:
        sender_email (str): Sender's email address
        recipient_email (str): Recipient's email address
        subject (str): Email subject
        body (str): Email body/message
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        
        # Create message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))
        
        # Configure SMTP
        smtp_server = getattr(config, "MAIL_SMTP_SERVER", "smtp.gmail.com")
        smtp_port = getattr(config, "MAIL_SMTP_PORT", 587)
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()

        # Use password from environment variable for security
        password = os.environ.get("MAIL_PASSWORD")
        if password:
            try:
                server.login(sender_email, password)
            except Exception as e:
                print(f"Mail login failed: {e}")

        server.send_message(message)
        server.quit()
        
        print(f"Email sent successfully to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


def send_leave_approval(sender_email, recipient_email, student_name, leave_dates):
    """
    Send pre-written leave approval email.
    """
    subject = "Leave Request Approved - Student Leave System"
    body = f"""
Dear {student_name},

Your leave request for {leave_dates} has been approved.

Best regards,
Student Leave System
    """
    return send_email(sender_email, recipient_email, subject, body)


def send_leave_rejection(sender_email, recipient_email, student_name, reason=""):
    """
    Send pre-written leave rejection email.
    """
    subject = "Leave Request Rejected - Student Leave System"
    body = f"""
Dear {student_name},

Your leave request has been rejected.
Reason: {reason}

Best regards,
Student Leave System
    """
    return send_email(sender_email, recipient_email, subject, body)