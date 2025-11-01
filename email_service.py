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

def send_support_invite(email: str, name: str, chatbot_name: str, invited_by: str, invitation_token: str):
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://nexva.pages.dev')
    accept_url = f"{FRONTEND_URL}/accept-invitation?token={invitation_token}"
    
    subject = f"Support Team Invitation - {chatbot_name}"
    body = f"""Hello {name},

{invited_by} has invited you to join the support team for {chatbot_name}.

Accept invitation: {accept_url}

This link expires in 7 days.

- Nexva Team"""

    html_body = f"""
    <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="border-bottom: 2px solid #0fdc78; padding-bottom: 10px; margin-bottom: 20px;">
                <h2 style="margin: 0; color: #111;">Support Team Invitation</h2>
            </div>
            
            <p>Hello <strong>{name}</strong>,</p>
            
            <p><strong>{invited_by}</strong> invited you to join the support team for <strong>{chatbot_name}</strong>.</p>
            
            <p style="margin: 30px 0;">
                <a href="{accept_url}" style="background-color: #0fdc78; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: 500;">Accept Invitation</a>
            </p>
            
            <p style="color: #666; font-size: 14px;">
                Link: <a href="{accept_url}" style="color: #0fdc78;">{accept_url}</a>
            </p>
            
            <p style="color: #999; font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee;">
                This invitation expires in 7 days. If you didn't expect this, ignore this email.
            </p>
        </body>
    </html>
    """
    send_email(email, subject, body, html_body)

def send_new_ticket_alert(support_emails: List[str], ticket_id: int, chatbot_name: str, user_message: str):
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://nexva.pages.dev')
    ticket_url = f"{FRONTEND_URL}/dashboard/support"
    
    subject = f"New Ticket #{ticket_id} - {chatbot_name}"
    preview = user_message[:100] + "..." if len(user_message) > 100 else user_message
    
    body = f"""New Support Ticket #{ticket_id}

Chatbot: {chatbot_name}
Message: {preview}

View: {ticket_url}

- Nexva Team"""

    html_body = f"""
    <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="border-bottom: 2px solid #0fdc78; padding-bottom: 10px; margin-bottom: 20px;">
                <h2 style="margin: 0; color: #111;">New Support Ticket #{ticket_id}</h2>
            </div>
            
            <p><strong>Chatbot:</strong> {chatbot_name}</p>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-left: 3px solid #0fdc78; margin: 20px 0;">
                <p style="margin: 0; color: #555;">{preview}</p>
            </div>
            
            <p style="margin: 30px 0;">
                <a href="{ticket_url}" style="background-color: #0fdc78; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: 500;">View Ticket</a>
            </p>
        </body>
    </html>
    """
    
    for email in support_emails:
        send_email(email, subject, body, html_body)

