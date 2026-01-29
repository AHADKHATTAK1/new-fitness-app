"""
Enterprise Security Manager
Two-Factor Authentication (2FA), Audit Logs, Session Management
"""

import pyotp
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import secrets
import hashlib
import json


class SecurityManager:
    """Enterprise-grade security features"""
    
    def __init__(self, session_factory):
        self.session = session_factory()
    
    # ==================== 2FA - TOTP (Authenticator App) ====================
    
    def generate_totp_secret(self, username: str) -> Dict:
        """
        Generate TOTP secret for authenticator app
        
        Returns:
            Dict with secret, qr_code_data, and provisioning_uri
        """
        # Generate random secret
        secret = pyotp.random_base32()
        
        # Create TOTP object
        totp = pyotp.TOTP(secret)
        
        # Generate provisioning URI for QR code
        provisioning_uri = totp.provisioning_uri(
            name=username,
            issuer_name='Gym Manager Pro'
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Convert to base64 image
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_code_data = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            'secret': secret,
            'qr_code': f'data:image/png;base64,{qr_code_data}',
            'provisioning_uri': provisioning_uri
        }
    
    def verify_totp(self, secret: str, code: str) -> bool:
        """Verify TOTP code from authenticator app"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)  # Allow 30s window
    
    # ==================== 2FA - SMS ====================
    
    def generate_sms_code(self) -> str:
        """Generate 6-digit SMS verification code"""
        return str(secrets.randbelow(1000000)).zfill(6)
    
    def send_sms_code(self, phone: str, code: str) -> bool:
        """
        Send SMS verification code
        Requires Twilio integration (placeholder for now)
        """
        # TODO: Integrate with Twilio
        print(f"[SMS] Code {code} would be sent to {phone}")
        # In production:
        # from twilio.rest import Client
        # client = Client(account_sid, auth_token)
        # client.messages.create(to=phone, from_=twilio_number, body=f"Your Gym Manager code: {code}")
        return True
    
    # ==================== 2FA - Email ====================
    
    def send_email_code(self, email: str, code: str) -> bool:
        """Send email verification code"""
        from email_utils import EmailSender
        sender = EmailSender()
        
        subject = "Gym Manager - Verification Code"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #8b5cf6;">Verification Code</h2>
            <p>Your verification code is:</p>
            <h1 style="background: #f3f4f6; padding: 20px; text-align: center; letter-spacing: 10px;">
                {code}
            </h1>
            <p style="color: #6b7280;">This code expires in 10 minutes.</p>
            <p style="color: #6b7280; font-size: 12px;">If you didn't request this, please ignore this email.</p>
        </body>
        </html>
        """
        
        return sender.send_email(email, subject, body)
    
    # ==================== AUDIT LOGS ====================
    
    def log_action(self, user_id: int, action: str, details: Dict = None, 
                   ip_address: str = None, user_agent: str = None):
        """
        Log user action for audit trail
        
        Args:
            user_id: User performing action
            action: Action type (e.g., 'login', 'delete_member', 'export_data')
            details: Additional context (member_id, amount, etc.)
            ip_address: User's IP
            user_agent: Browser user agent
        """
        from models import AuditLog
        
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            details=json.dumps(details) if details else None,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow()
        )
        
        self.session.add(log_entry)
        self.session.commit()
    
    def get_audit_logs(self, user_id: Optional[int] = None, 
                       action: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       limit: int = 100) -> List[Dict]:
        """
        Retrieve audit logs with filters
        
        Returns:
            List of audit log entries
        """
        from models import AuditLog, User
        
        query = self.session.query(AuditLog, User).join(User)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        query = query.order_by(AuditLog.timestamp.desc()).limit(limit)
        
        logs = []
        for log, user in query.all():
            logs.append({
                'id': log.id,
                'user': user.email,
                'action': log.action,
                'details': json.loads(log.details) if log.details else {},
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return logs
    
    # ==================== SESSION MANAGEMENT ====================
    
    def create_session_token(self) -> str:
        """Generate cryptographically secure session token"""
        return secrets.token_urlsafe(32)
    
    def hash_session_token(self, token: str) -> str:
        """Hash session token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def track_session(self, user_id: int, token: str, ip_address: str, 
                      user_agent: str, expires_hours: int = 24):
        """
        Track active user session
        
        Args:
            user_id: User ID
            token: Session token (hashed before storage)
            ip_address: User's IP
            user_agent: Browser info
            expires_hours: Session duration
        """
        from models import UserSession
        
        session_entry = UserSession(
            user_id=user_id,
            token_hash=self.hash_session_token(token),
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=expires_hours),
            is_active=True
        )
        
        self.session.add(session_entry)
        self.session.commit()
    
    def invalidate_session(self, token: str) -> bool:
        """Invalidate a session (logout)"""
        from models import UserSession
        
        token_hash = self.hash_session_token(token)
        session = self.session.query(UserSession).filter_by(
            token_hash=token_hash,
            is_active=True
        ).first()
        
        if session:
            session.is_active = False
            self.session.commit()
            return True
        
        return False
    
    def get_active_sessions(self, user_id: int) -> List[Dict]:
        """Get all active sessions for a user"""
        from models import UserSession
        
        sessions = self.session.query(UserSession).filter_by(
            user_id=user_id,
            is_active=True
        ).filter(
            UserSession.expires_at > datetime.utcnow()
        ).all()
        
        return [{
            'id': s.id,
            'ip_address': s.ip_address,
            'user_agent': s.user_agent,
            'created_at': s.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'expires_at': s.expires_at.strftime('%Y-%m-%d %H:%M:%S')
        } for s in sessions]
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions (cron job)"""
        from models import UserSession
        
        expired = self.session.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow()
        ).update({'is_active': False})
        
        self.session.commit()
        return expired
    
    # ==================== PASSWORD POLICIES ====================
    
    def check_password_strength(self, password: str) -> Dict:
        """
        Check password meets security requirements
        
        Returns:
            Dict with 'valid' bool and 'issues' list
        """
        issues = []
        
        if len(password) < 8:
            issues.append('Password must be at least 8 characters')
        
        if not any(c.isupper() for c in password):
            issues.append('Password must contain uppercase letter')
        
        if not any(c.islower() for c in password):
            issues.append('Password must contain lowercase letter')
        
        if not any(c.isdigit() for c in password):
            issues.append('Password must contain a number')
        
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            issues.append('Password must contain special character')
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt (use Werkzeug)"""
        from werkzeug.security import generate_password_hash
        return generate_password_hash(password)
    
    def verify_password(self, password: str, hash: str) -> bool:
        """Verify password against hash"""
        from werkzeug.security import check_password_hash
        return check_password_hash(hash, password)


# Add new models to models.py

"""
class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    details = Column(Text)  # JSON string
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    user = relationship('User', backref='audit_logs')


class UserSession(Base):
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    user = relationship('User', backref='sessions')
"""
