"""
Email Utility for sending verification codes and notifications
Supports Gmail SMTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime


class EmailSender:
    """Send emails for verification codes and notifications"""
    
    def __init__(self):
        """Initialize with SMTP settings from environment"""
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email = os.getenv('SMTP_EMAIL', '')
        self.password = os.getenv('SMTP_PASSWORD', '')
        self.enabled = bool(self.email and self.password)
    
    def is_configured(self):
        """Check if email is configured"""
        return self.enabled
    
    def send_reset_code(self, to_email, reset_code, username):
        """
        Send password reset code via email
        
        Args:
            to_email: Recipient email
            reset_code: 6-digit verification code
            username: User's username
        
        Returns:
            bool: True if sent successfully
        """
        if not self.enabled:
            print(f"Email not configured. Reset code for {username}: {reset_code}")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = 'Password Reset Code - fitnessmanagement'
            
            # HTML email body
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #7928ca; text-align: center;">🔐 Password Reset Request</h2>
                    <p>Hello <strong>{username}</strong>,</p>
                    <p>We received a request to reset your password. Use the code below to reset your password:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <div style="background: linear-gradient(135deg, #7928ca, #3a8ed8); color: white; font-size: 32px; font-weight: bold; padding: 20px; border-radius: 10px; letter-spacing: 5px;">
                            {reset_code}
                        </div>
                    </div>
                    
                    <p style="color: #666;">This code will expire in <strong>15 minutes</strong>.</p>
                    <p style="color: #666;">If you didn't request this, please ignore this email.</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="font-size: 12px; color: #999; text-align: center;">
                        fitnessmanagement - Secure Fitness Management<br>
                        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Attach HTML
            msg.attach(MIMEText(html, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            return True
        
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    def send_password_changed_notification(self, to_email, username):
        """Send notification that password was changed"""
        if not self.enabled:
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = 'Password Changed Successfully - fitnessmanagement'
            
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px;">
                    <h2 style="color: #27ae60; text-align: center;">✅ Password Changed</h2>
                    <p>Hello <strong>{username}</strong>,</p>
                    <p>Your password has been successfully changed.</p>
                    <p style="color: #666;">If you didn't make this change, please contact support immediately.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="font-size: 12px; color: #999; text-align: center;">
                        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            return True
        
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            return False

    def send_email(self, to_email, subject, body_html):
        """
        Generic method to send HTML emails
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body_html: HTML content of the email
            
        Returns:
            bool: True if sent successfully
        """
        if not self.enabled:
            print(f"Email not configured. To: {to_email}, Subject: {subject}")
            return False
            
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body_html, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
                
            return True
            
        except Exception as e:
            print(f"Error sending generic email: {str(e)}")
            return False

    def send_auto_code_email(self, to_email, code, purpose='Verification', username=None, expires_minutes=10):
        """
        Send an automatic email containing a security code.

        Args:
            to_email: Recipient email
            code: Security code (OTP/reset/verification)
            purpose: Code purpose shown in subject/body
            username: Optional display name
            expires_minutes: Code validity time in minutes

        Returns:
            bool: True if sent successfully
        """
        safe_purpose = str(purpose or 'Verification').strip().title()
        display_name = (username or to_email or 'User').strip()

        subject = f"{safe_purpose} Code - fitnessmanagement"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 10px; padding: 28px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">
                <h2 style="margin: 0 0 14px; color: #4f46e5;">{safe_purpose} Code</h2>
                <p style="margin: 0 0 10px;">Hello <strong>{display_name}</strong>,</p>
                <p style="margin: 0 0 16px;">Use the code below to complete your {safe_purpose.lower()} request:</p>
                <div style="text-align: center; margin: 20px 0;">
                    <div style="display: inline-block; background: #eef2ff; color: #1e1b4b; border: 1px solid #c7d2fe; font-size: 30px; font-weight: 700; letter-spacing: 6px; padding: 16px 24px; border-radius: 10px;">
                        {code}
                    </div>
                </div>
                <p style="color: #475569; margin: 0 0 8px;">This code expires in <strong>{int(expires_minutes)}</strong> minutes.</p>
                <p style="color: #64748b; font-size: 13px; margin: 0;">If you did not request this, you can ignore this email.</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(to_email, subject, body)
