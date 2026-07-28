import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def send_otp_email(to_email: str, otp_code: str):
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    msg = EmailMessage()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = "Your Verification Code"
    msg.set_content(f"Your OTP code is: {otp_code}")

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls() 
        server.login(smtp_user, smtp_password) # type: ignore
        server.send_message(msg)