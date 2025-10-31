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
    FRONTEND_URL = "https://nexva.pages.dev"
    accept_url = f"{FRONTEND_URL}/accept-invitation?token={invitation_token}"
    
    subject = f"You've been invited to support team for {chatbot_name}"
    body = f"""Hello {name},

{invited_by} has invited you to join the support team for {chatbot_name}.

Click the link below to accept the invitation:
{accept_url}

This invitation will expire in 7 days.

Best regards,
Nexva Team"""

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">Nexva</h1>
            </div>
            <div style="padding: 30px; background-color: #f9fafb;">
                <h2 style="color: #111827;">Support Team Invitation</h2>
                <p style="color: #4b5563; font-size: 16px;">Hello <strong>{name}</strong>,</p>
                <p style="color: #4b5563; font-size: 16px;">
                    <strong>{invited_by}</strong> has invited you to join the support team for 
                    <strong style="color: #667eea;">{chatbot_name}</strong>.
                </p>
                <p style="color: #4b5563; font-size: 16px;">
                    As a support team member, you'll be able to respond to customer support tickets through the Nexva dashboard.
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{accept_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold; font-size: 16px;">Accept Invitation</a>
                </div>
                <p style="color: #6b7280; font-size: 14px;">
                    Or copy and paste this link into your browser:<br>
                    <a href="{accept_url}" style="color: #667eea; word-break: break-all;">{accept_url}</a>
                </p>
                <p style="color: #9ca3af; font-size: 12px; margin-top: 30px;">
                    This invitation will expire in 7 days. If you didn't expect this invitation, you can safely ignore this email.
                </p>
            </div>
            <div style="background-color: #f3f4f6; padding: 20px; text-align: center;">
                <p style="color: #6b7280; font-size: 12px; margin: 0;">
                    © 2025 Nexva. All rights reserved.
                </p>
            </div>
        </body>
    </html>
    """
    send_email(email, subject, body, html_body)

def send_new_ticket_alert(support_emails: List[str], ticket_id: int, chatbot_name: str, user_message: str):
    FRONTEND_URL = "https://nexva.pages.dev"
    ticket_url = f"{FRONTEND_URL}/dashboard/support"
    
    subject = f"New Support Ticket #{ticket_id} - {chatbot_name}"
    preview = user_message[:100] + "..." if len(user_message) > 100 else user_message
    
    body = f"""New Support Ticket #{ticket_id}

Chatbot: {chatbot_name}
Message: {preview}

View and respond: {ticket_url}

Nexva Team"""

    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>New Support Ticket #{ticket_id}</h2>
            <p><strong>Chatbot:</strong> {chatbot_name}</p>
            <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #4F46E5; margin: 20px 0;">
                <p style="margin: 0;">{preview}</p>
            </div>
            <p><a href="{ticket_url}" style="background-color: #4F46E5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">View Ticket</a></p>
            <p>Best regards,<br>Nexva Team</p>
        </body>
    </html>
    """
    
    for email in support_emails:
        send_email(email, subject, body, html_body)

