"""
Database-backed Authentication Manager
Uses PostgreSQL User table instead of JSON files
"""

from models import User, get_session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import os
import json

class AuthManager:
    def __init__(self):
        self._reset_codes = {}
        self.session = get_session()
        if not self.session:
            print("⚠️ Running in LEGACY JSON MODE (DB connection failed)")
            self.legacy = True
            # Load users from JSON as fallback
            self.users_file = 'users.json'
            self.users = self.load_users()
        else:
            self.legacy = False
            self.users = {} # Prevent AttributeError in context processors
            print("✅ Running in DATABASE MODE")

    def load_users(self):
        if os.path.exists('users.json'):
            try:
                with open('users.json', 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def hash_password(self, password):
        """Hash password using werkzeug"""
        return generate_password_hash(password)
    
    def check_password(self, password_hash, password):
        """Verify password"""
        return check_password_hash(password_hash, password)
    
    def user_exists(self, username):
        """Check if user exists"""
        if self.legacy:
            return username in self.users
            
        user = self.session.query(User).filter_by(email=username).first()
        return user is not None
    
    def get_user_id(self, email):
        """Get numeric user ID by email"""
        if self.legacy: return None
        user = self.session.query(User).filter_by(email=email).first()
        return user.id if user else None
        
    def validate_referral(self, code):
        """Check if referral code is valid"""
        normalized = self.normalize_referral_code(code)
        valid_codes = {
            '500596AK1',
            'AHADKHATTAK12'
        }
        return bool(normalized and normalized in valid_codes)

    def normalize_referral_code(self, code):
        """Normalize referral code by removing spaces and uppercasing."""
        if not code:
            return None
        return ''.join(str(code).upper().split())
    
    def create_user(self, username, password, referral_code=None):
        """Create a new user"""
        if self.legacy:
            if username in self.users: return False
            self.users[username] = {
                'password': self.hash_password(password),
                'role': 'admin',
                'joined_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            with open('users.json', 'w') as f:
                json.dump(self.users, f)
            return True

        if self.user_exists(username):
            return False
        
        normalized_code = self.normalize_referral_code(referral_code)

        # Determine trial/expiry based on code
        if normalized_code in {'500596AK1', 'AHADKHATTAK12'}:
            expiry = datetime(2099, 1, 1)  # Lifetime Access
            market = 'VIP'
            subscription_tier = 'enterprise_plus'
            subscription_status = 'active'
            billing_cycle = 'yearly'
        else:
            expiry = datetime.utcnow() + timedelta(days=3)  # 3 Days Free Trial
            market = 'US'  # Default
            subscription_tier = 'starter'
            subscription_status = 'trial'
            billing_cycle = 'monthly'

        user = User(
            email=username,
            password_hash=self.hash_password(password),
            role='admin',
            market=market,
            subscription_expiry=expiry,
            subscription_tier=subscription_tier,
            subscription_status=subscription_status,
            billing_cycle=billing_cycle
        )
        
        self.session.add(user)
        self.session.commit()
        return True

    def apply_referral_code(self, username, referral_code):
        """Apply referral code to an existing user and upgrade access when valid."""
        if self.legacy:
            return False

        normalized_code = self.normalize_referral_code(referral_code)
        if normalized_code not in {'500596AK1', 'AHADKHATTAK12'}:
            return False

        user = self.session.query(User).filter_by(email=username).first()
        if not user:
            return False

        user.market = 'VIP'
        user.subscription_tier = 'enterprise_plus'
        user.subscription_status = 'active'
        user.billing_cycle = 'yearly'
        user.subscription_expiry = datetime(2099, 1, 1)
        self.session.commit()
        # Refresh user object to ensure it has the latest data
        self.session.refresh(user)
        return True
    
    def verify_user(self, username, password):
        """Verify user credentials"""
        if self.legacy:
            if username not in self.users: return False
            stored_hash = self.users[username].get('password')
            if stored_hash.startswith('scrypt:') or stored_hash.startswith('pbkdf2:'):
                return check_password_hash(stored_hash, password)
            import hashlib
            sha256_hash = hashlib.sha256(password.encode()).hexdigest()
            return stored_hash == sha256_hash

        user = self.session.query(User).filter_by(email=username).first()
        if not user: return False
        
        if user.password_hash.startswith('scrypt:') or user.password_hash.startswith('pbkdf2:'):
            return self.check_password(user.password_hash, password)
        else:
            # Legacy SHA256 check
            import hashlib
            if user.password_hash == hashlib.sha256(password.encode()).hexdigest():
                user.password_hash = self.hash_password(password)
                self.session.commit()
                return True
            return False

    def is_subscription_active(self, username):
        """Check if user's subscription is active."""
        # Legacy mode - always return True
        if self.legacy:
            return True
        
        user = self.session.query(User).filter_by(email=username).first()
        if not user:
            return False
        
        # VIP code (500596AK1) gets lifetime access
        if hasattr(user, 'market') and user.market == 'VIP':
            return True

        # Trial users get strict 3-day window (no grace)
        if getattr(user, 'subscription_status', None) == 'trial':
            if user.subscription_expiry:
                return datetime.utcnow() < user.subscription_expiry
            return False
        
        # Check expiry with 3-day grace period
        if user.subscription_expiry:
            grace_period = timedelta(days=3)
            return datetime.utcnow() < (user.subscription_expiry + grace_period)
        
        # If no expiry set, give 3 days trial from account creation
        if user.created_at:
            trial_end = user.created_at + timedelta(days=3)
            return datetime.utcnow() < trial_end
        
        return False

    def extend_subscription(self, username, days=30):
        """Extend user's subscription by specified days"""
        user = self.session.query(User).filter_by(email=username).first()
        if user:
            if not user.subscription_expiry:
                user.subscription_expiry = datetime.utcnow() + timedelta(days=days)
            else:
                user.subscription_expiry += timedelta(days=days)
            self.session.commit()
            return True
        return False
    
    def set_market(self, username, market):
        """Set user's market region ('US', 'PK', or 'VIP')"""
        user = self.session.query(User).filter_by(email=username).first()
        if user:
            user.market = market
            self.session.commit()
            return True
        return False
    
    def get_market(self, username):
        """TEMPORARILY DISABLED"""
        return 'US'  # Disabled until /fix_db is run
        # user = self.session.query(User).filter_by(email=username).first()
        # return user.market if user else 'US'

    # Password Reset Methods
    def generate_reset_code(self, username):
        """Generate a 6-digit reset code"""
        if self.legacy:
            if username not in self.users: return None
            code = str(secrets.randbelow(900000) + 100000)
            self._reset_codes[username] = {
                'code': code,
                'expires_at': datetime.utcnow() + timedelta(minutes=15)
            }
            return code

        user = self.session.query(User).filter_by(email=username).first()
        if not user:
            return None
        
        code = str(secrets.randbelow(900000) + 100000)  # 6-digit code
        self._reset_codes[username] = {
            'code': code,
            'expires_at': datetime.utcnow() + timedelta(minutes=15)
        }
        return code
    
    def verify_reset_code(self, username, code):
        """Verify reset code and expiry"""
        record = self._reset_codes.get(username)
        if not record:
            return False

        if datetime.utcnow() > record.get('expires_at', datetime.utcnow()):
            self._reset_codes.pop(username, None)
            return False

        is_valid = str(record.get('code', '')).strip() == str(code or '').strip()
        if is_valid:
            self._reset_codes.pop(username, None)

        return is_valid
    
    def update_password(self, username, new_password):
        """Update user password"""
        if self.legacy:
            if username not in self.users: return False
            self.users[username]['password'] = self.hash_password(new_password)
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f)
            return True

        user = self.session.query(User).filter_by(email=username).first()
        if not user:
            return False
        
        user.password_hash = self.hash_password(new_password)
        self.session.commit()
        return True
    
    def __del__(self):
        """Close database session"""
        if hasattr(self, 'session') and self.session is not None:
            self.session.close()
