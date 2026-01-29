"""
Database models for Gym Manager
PostgreSQL schema using SQLAlchemy ORM
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Text, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()
_INVALID_DB_URL_WARNED = False

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default='admin')
    market = Column(String(50), default='US', nullable=True)  # 'US' or 'PK' or 'VIP'
    subscription_expiry = Column(DateTime, nullable=True)  # Subscription expiry date
    subscription_tier = Column(String(50), default='starter')
    billing_cycle = Column(String(20), default='monthly')
    tier_upgraded_at = Column(DateTime)
    tier_downgrade_scheduled = Column(String(50))
    subscription_status = Column(String(50), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    gyms = relationship('Gym', back_populates='user', cascade='all, delete-orphan')
    audit_logs = relationship('AuditLog', back_populates='user', cascade='all, delete-orphan')
    sessions = relationship('UserSession', back_populates='user', cascade='all, delete-orphan')

class Gym(Base):
    __tablename__ = 'gyms'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(255), nullable=False)
    logo_url = Column(String(500))
    currency = Column(String(10), default='Rs')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='gyms')
    members = relationship('Member', back_populates='gym', cascade='all, delete-orphan')
    expenses = relationship('Expense', back_populates='gym', cascade='all, delete-orphan')

class Member(Base):
    __tablename__ = 'members'
    
    id = Column(Integer, primary_key=True)
    gym_id = Column(Integer, ForeignKey('gyms.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255))
    photo_url = Column(String(500))
    membership_type = Column(String(50), default='monthly')
    joined_date = Column(Date, default=datetime.utcnow().date)
    is_active = Column(Boolean, default=True, index=True)  # Changed from 'active' to 'is_active'
    is_trial = Column(Boolean, default=False)
    trial_end_date = Column(Date)
    birthday = Column(Date)  # For birthday alerts
    last_check_in = Column(DateTime)  # For inactive member tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    gym = relationship('Gym', back_populates='members')
    fees = relationship('Fee', back_populates='member', cascade='all, delete-orphan')
    attendance = relationship('Attendance', back_populates='member', cascade='all, delete-orphan')
    notes = relationship('MemberNote', back_populates='member', cascade='all, delete-orphan')
    measurements = relationship('BodyMeasurement', back_populates='member', cascade='all, delete-orphan')

class Fee(Base):
    __tablename__ = 'fees'
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey('members.id'), nullable=False, index=True)  # INDEXED
    month = Column(String(7), nullable=False, index=True)  # INDEXED for monthly queries
    amount = Column(DECIMAL(10, 2), nullable=False)
    paid_date = Column(DateTime, nullable=False, index=True)  # INDEXED for date range queries
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    member = relationship('Member', back_populates='fees')

class Attendance(Base):
    __tablename__ = 'attendance'
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey('members.id'), nullable=False)
    check_in_time = Column(DateTime, default=datetime.utcnow, index=True)
    emotion = Column(String(50))
    confidence = Column(DECIMAL(5, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    member = relationship('Member', back_populates='attendance')

class Expense(Base):
    __tablename__ = 'expenses'
    
    id = Column(Integer, primary_key=True)
    gym_id = Column(Integer, ForeignKey('gyms.id'), nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    gym = relationship('Gym', back_populates='expenses')

class MemberNote(Base):
    __tablename__ = 'member_notes'
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey('members.id'), nullable=False)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    member = relationship('Member', back_populates='notes')

class BodyMeasurement(Base):
    __tablename__ = 'body_measurements'
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey('members.id'), nullable=False)
    weight = Column(DECIMAL(5, 2))  # kg
    body_fat = Column(DECIMAL(5, 2))  # percentage
    chest = Column(DECIMAL(5, 2))  # cm
    waist = Column(DECIMAL(5, 2))  # cm
    arms = Column(DECIMAL(5, 2))  # cm
    notes = Column(Text)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    member = relationship('Member', back_populates='measurements')

# Database connection helper
def _is_placeholder_database_url(db_url: str) -> bool:
    """Detect common template/placeholder DATABASE_URL values."""
    if not db_url:
        return True

    normalized = db_url.strip().lower()
    placeholder_patterns = [
        'postgresql://user:password@host:port/database',
        'postgres://user:password@host:port/database',
        '@host:port',
        'host:port/database',
        ':password@',
    ]

    return any(pattern in normalized for pattern in placeholder_patterns)


def get_database_url():
    """Get database URL from environment or use local SQLite for development"""
    global _INVALID_DB_URL_WARNED
    db_url = os.getenv('DATABASE_URL')

    if db_url:
        if _is_placeholder_database_url(db_url):
            if not _INVALID_DB_URL_WARNED:
                print("⚠️ DATABASE_URL appears to be placeholder values; using local SQLite fallback")
                _INVALID_DB_URL_WARNED = True
            return 'sqlite:///gym_manager.db'

        # Railway/Render provides postgres:// but SQLAlchemy needs postgresql://
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return db_url
    else:
        # Local development - use SQLite
        return 'sqlite:///gym_manager.db'

def init_db():
    """Initialize database and create all tables"""
    url = get_database_url()
    try:
        engine = create_engine(url)
        Base.metadata.create_all(engine)
        return engine
    except Exception as e:
        # Safe debug print (mask password)
        safe_url = url
        if '@' in safe_url:
            part1 = safe_url.split('@')[0]
            part2 = safe_url.split('@')[1]
            # Mask password
            if ':' in part1:
                safe_url = part1.split(':')[0] + ':****@' + part2
        
        print(f"❌ DB CONNECTION ERROR: {str(e)}")
        print(f"❌ URL Structure causing error: {safe_url}")
        raise e

def get_session():
    """Get database session with error handling"""
    try:
        engine = create_engine(get_database_url(), pool_pre_ping=True)
        Session = sessionmaker(bind=engine)
        return Session()
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return None

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    details = Column(Text)  # JSON string
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    user = relationship('User', back_populates='audit_logs')


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
    
    user = relationship('User', back_populates='sessions')
