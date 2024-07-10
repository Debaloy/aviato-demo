import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List
from dotenv import dotenv_values
from fastapi import HTTPException
import my_logger

config = dotenv_values(".env")

def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def process_user_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in user_data.items():
        if key in ["pass", "password"]:
            user_data[key] = hash_password(value)
    return user_data

def send_invitation_email(recipients: List[str]):
    subject = "API Documentation Invitation"
    body = """
    <html>
    <body>
        <div style="text-align: center; background-color: #376edc; padding: 10px;">
            <h1 style="color: white; font-weight: bold;">API Documentation Invite</h1>
        </div>
        <p><span style="color: #376edc; font-weight: bold;">Hello,</span></p>
        <p>We are excited to invite you to view our User Management API documentation on ReDoc.</p>
        <p>You can access the documentation by clicking the button below:</p>
        <div>
            <a href="http://test1.tkrecon.xyz/redoc" style="background-color: #376edc; color: white; padding: 10px 20px; text-decoration: none;">View API Documentation</a>
        </div>
        <p>As per the Requirements I changed that "Any" method because of Flutter.</p>
        <p>I have also set up an AWS EC2 instance for the public IP, used Reverse Proxy for port forwarding, and GCP Postgres for the database.</p>
        <p>We appreciate your time and look forward to your feedback.</p>
        <div style="background-color: #376edc; color: white; text-align: center; padding: 10px;">
            <p>Thank you,<br>Urlich Bachmann</p>
            <p>If you have any questions, feel free to reply to this email.</p>
        </div>
    </body>
    </html>
    """

    try:
        with smtplib.SMTP(config["MAIL_SERVER"], config["MAIL_PORT"]) as server:
            server.starttls()
            server.login(config["SENDER_MAIL"], config["SENDER_PASS"])
            for recipient in recipients:
                msg = MIMEMultipart("alternative")
                msg['From'] = config["SENDER_MAIL"]
                msg['To'] = recipient
                msg['Subject'] = subject

                part = MIMEText(body, 'html')
                msg.attach(part)

                server.sendmail(config["SENDER_MAIL"], recipient, msg.as_string())
                my_logger.logger.info(f"Invitation email sent successfully to {recipient}.")
    except Exception as e:
        my_logger.logger.error(f"Error sending invitation emails: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
