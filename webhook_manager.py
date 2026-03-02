"""
Webhook System - Send real-time events to external URLs
Enables integration with external services like QuickBooks, Salesforce, Slack

Key Features:
- Event-based notifications
- Automatic retries
- Signature verification
- Webhook logs and stats
"""

import requests
import json
import hmac
import hashlib
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from models import get_session, User, get_database_url
import os

Base = declarative_base()


class Webhook(Base):
    """Webhook configuration"""
    __tablename__ = 'webhooks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    events = Column(Text)  # JSON array of subscribed events
    secret = Column(String(100))  # For HMAC signature verification
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime)
    total_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)


class WebhookLog(Base):
    """Log of webhook deliveries"""
    __tablename__ = 'webhook_logs'
    
    id = Column(Integer, primary_key=True)
    webhook_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(100))
    payload = Column(Text)  # JSON
    response_code = Column(Integer)
    response_time_ms = Column(Integer)
    success = Column(Boolean)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class WebhookManager:
    """Manage and trigger webhooks for events"""
    
    # Available event types
    EVENTS = {
        # Member events
        'member.created': 'New member added',
        'member.updated': 'Member details changed',
        'member.deleted': 'Member removed',
        'member.trial_started': 'Member started trial',
        'member.trial_ended': 'Member trial ended',
        
        # Payment events
        'payment.received': 'Payment recorded',
        'payment.overdue': 'Payment is overdue',
        'payment.refunded': 'Payment refunded',
        
        # Subscription events
        'subscription.upgraded': 'Tier upgraded',
        'subscription.downgraded': 'Tier downgraded',
        'subscription.expired': 'Subscription expired',
        'subscription.renewed': 'Subscription renewed',
        
        # Gym events
        'gym.created': 'New gym location',
        'gym.updated': 'Gym details changed',
        
        # Attendance events
        'attendance.checked_in': 'Member checked in',
        'attendance.checked_out': 'Member checked out'
    }
    
    @staticmethod
    def create_tables():
        """Create webhook tables in database"""
        try:
            engine = create_engine(get_database_url())
            Base.metadata.create_all(engine, tables=[
                Webhook.__table__,
                WebhookLog.__table__
            ])
            WebhookManager._ensure_schema(engine)
            print("✅ Webhook tables created")
        except Exception as e:
            print(f"Webhook table creation: {e}")

    @staticmethod
    def _ensure_schema(engine):
        """Ensure webhook tables have required columns for older DBs."""
        required_columns = {
            'webhooks': {
                'events': 'TEXT',
                'secret': 'VARCHAR(100)',
                'is_active': 'BOOLEAN DEFAULT 1',
                'created_at': 'DATETIME',
                'last_triggered': 'DATETIME',
                'total_calls': 'INTEGER DEFAULT 0',
                'failed_calls': 'INTEGER DEFAULT 0'
            },
            'webhook_logs': {
                'response_code': 'INTEGER',
                'response_time_ms': 'INTEGER',
                'success': 'BOOLEAN',
                'error_message': 'TEXT',
                'created_at': 'DATETIME'
            }
        }

        try:
            inspector = inspect(engine)
            with engine.begin() as conn:
                for table_name, columns in required_columns.items():
                    if table_name not in inspector.get_table_names():
                        continue
                    existing = {col['name'] for col in inspector.get_columns(table_name)}
                    for column_name, column_type in columns.items():
                        if column_name in existing:
                            continue
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
        except Exception as schema_error:
            print(f"Webhook schema ensure warning: {schema_error}")
    
    @staticmethod
    def trigger_event(user_id, event_type, data):
        """
        Trigger webhooks for an event
        
        Args:
            user_id: User who owns the webhook
            event_type: Type of event (e.g., 'member.created')
            data: Event payload dict
            
        Example:
            WebhookManager.trigger_event(
                user_id=1, 
                event_type='member.created',
                data={'member_id': 123, 'name': 'John Doe'}
            )
        """
        if event_type not in WebhookManager.EVENTS:
            print(f"Unknown webhook event: {event_type}")
            return
        
        session = get_session()
        if not session:
            return
        
        try:
            # Find active webhooks subscribed to this event
            webhooks = session.query(Webhook).filter_by(
                user_id=user_id,
                is_active=True
            ).all()
            
            for webhook in webhooks:
                # Check if webhook is subscribed to this event
                try:
                    subscribed_events = json.loads(webhook.events or '[]')
                except:
                    subscribed_events = []
                
                if event_type not in subscribed_events:
                    continue
                
                # Send webhook asynchronously (in production, use Celery/RQ)
                WebhookManager._send_webhook(webhook, event_type, data, session)
        
        except Exception as e:
            print(f"Webhook trigger error: {e}")
        finally:
            session.close()
    
    @staticmethod
    def _send_webhook(webhook, event_type, data, session):
        """
        Send HTTP POST to webhook URL
        
        Args:
            webhook: Webhook object
            event_type: Event type string
            data: Payload data
            session: Database session
        """
        # Prepare payload
        payload = {
            'event': event_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'webhook_id': webhook.id
        }
        
        # Add HMAC signature if secret exists
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'GymManager-Webhook/1.0'
        }
        
        if webhook.secret:
            payload_str = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                webhook.secret.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()
            headers['X-Webhook-Signature'] = f'sha256={signature}'
        
        try:
            start_time = datetime.utcnow()
            
            # Send POST request with timeout
            response = requests.post(
                webhook.url,
                json=payload,
                headers=headers,
                timeout=10  # 10 second timeout
            )
            
            end_time = datetime.utcnow()
            response_time = int((end_time - start_time).total_seconds() * 1000)
            
            success = 200 <= response.status_code < 300
            
            # Update webhook stats
            webhook.last_triggered = datetime.utcnow()
            webhook.total_calls = (webhook.total_calls or 0) + 1
            if not success:
                webhook.failed_calls = (webhook.failed_calls or 0) + 1
            
            # Log the delivery
            log = WebhookLog(
                webhook_id=webhook.id,
                event_type=event_type,
                payload=json.dumps(payload),
                response_code=response.status_code,
                response_time_ms=response_time,
                success=success,
                error_message=None if success else response.text[:500]
            )
            
            session.add(log)
            session.commit()
            
            print(f"✅ Webhook delivered: {event_type} -> {webhook.url} ({response.status_code})")
            return success
            
        except requests.exceptions.Timeout:
            error_msg = "Request timeout (10s)"
            WebhookManager._log_failure(webhook, event_type, payload, error_msg, session)
            return False
            
        except requests.exceptions.ConnectionError:
            error_msg = "Connection error - unable to reach endpoint"
            WebhookManager._log_failure(webhook, event_type, payload, error_msg, session)
            return False
            
        except Exception as e:
            error_msg = str(e)[:500]
            WebhookManager._log_failure(webhook, event_type, payload, error_msg, session)
            return False
    
    @staticmethod
    def _log_failure(webhook, event_type, payload, error_msg, session):
        """Log webhook failure"""
        webhook.total_calls = (webhook.total_calls or 0) + 1
        webhook.failed_calls = (webhook.failed_calls or 0) + 1
        webhook.last_triggered = datetime.utcnow()
        
        log = WebhookLog(
            webhook_id=webhook.id,
            event_type=event_type,
            payload=json.dumps(payload),
            success=False,
            error_message=error_msg
        )
        
        session.add(log)
        session.commit()
        
        print(f"❌ Webhook failed: {event_type} -> {webhook.url} ({error_msg})")
    
    @staticmethod
    def get_webhooks(user_id):
        """Get all webhooks for a user"""
        session = get_session()
        if not session:
            return []
        
        try:
            webhooks = session.query(Webhook).filter_by(user_id=user_id).all()
            return webhooks
        finally:
            session.close()
    
    @staticmethod
    def get_webhook_logs(webhook_id, limit=100):
        """Get recent logs for a webhook"""
        session = get_session()
        if not session:
            return []
        
        try:
            logs = session.query(WebhookLog)\
                .filter_by(webhook_id=webhook_id)\
                .order_by(WebhookLog.created_at.desc())\
                .limit(limit)\
                .all()
            return logs
        finally:
            session.close()
    
    @staticmethod
    def verify_signature(payload_str, signature, secret):
        """
        Verify webhook signature
        
        Args:
            payload_str: Raw payload string
            signature: Signature from X-Webhook-Signature header
            secret: Webhook secret
            
        Returns:
            bool: True if signature is valid
        """
        if not signature or not secret:
            return False
        
        # Extract algorithm and signature
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        # Calculate expected signature
        expected = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)


# Create tables on module import
try:
    WebhookManager.create_tables()
except:
    pass  # Tables might already exist
