import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
import os

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "noreply@nexva.ai")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@nexva.ai")

def send_email(to_email: str, subject: str, body: str, html_body: str = None):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        
        msg.attach(MIMEText(body, 'plain'))
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))
        
        if not SMTP_PASSWORD:
            print(f"[EMAIL SIMULATION] To: {to_email}, Subject: {subject}")
            return
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Email send failed: {e}")

def send_support_invite(email: str, name: str, chatbot_name: str, invited_by: str):
    subject = f"You've been invited to support team for {chatbot_name}"
    body = f"""Hello {name},

{invited_by} has invited you to join the support team for {chatbot_name}.

You can now respond to customer support tickets through the Nexva dashboard.

Login at: http://localhost:3000/login

Best regards,
Nexva Team"""

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Support Team Invitation</h2>
            <p>Hello {name},</p>
            <p><strong>{invited_by}</strong> has invited you to join the support team for <strong>{chatbot_name}</strong>.</p>
            <p>You can now respond to customer support tickets through the Nexva dashboard.</p>
            <p><a href="http://localhost:3000/login" style="background-color: #4F46E5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Login to Dashboard</a></p>
            <p>Best regards,<br>Nexva Team</p>
        </body>
    </html>
    """
    send_email(email, subject, body, html_body)

def send_new_ticket_alert(support_emails: List[str], ticket_id: int, chatbot_name: str, user_message: str):
    subject = f"New Support Ticket #{ticket_id} - {chatbot_name}"
    preview = user_message[:100] + "..." if len(user_message) > 100 else user_message
    
    body = f"""New Support Ticket #{ticket_id}

Chatbot: {chatbot_name}
Message: {preview}

View and respond: http://localhost:3000/dashboard/support

Nexva Team"""

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>New Support Ticket #{ticket_id}</h2>
            <p><strong>Chatbot:</strong> {chatbot_name}</p>
            <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #4F46E5; margin: 20px 0;">
                <p style="margin: 0;">{preview}</p>
            </div>
            <p><a href="http://localhost:3000/dashboard/support" style="background-color: #4F46E5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">View Ticket</a></p>
            <p>Best regards,<br>Nexva Team</p>
        </body>
    </html>
    """
    
    for email in support_emails:
        send_email(email, subject, body, html_body)

