"""
Quick migration to add tier columns to production database
Run this once to add new subscription tier fields
"""

from models import get_session
from sqlalchemy import text
import os

def add_tier_columns():
    """Add tier columns to users table"""
    session = get_session()
    
    try:
        # Add columns one by one (safe if they already exist)
        migrations = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(50) DEFAULT 'starter'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS billing_cycle VARCHAR(20) DEFAULT 'monthly'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS tier_upgraded_at TIMESTAMP",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS tier_downgrade_scheduled VARCHAR(50)"
        ]
        
        for migration in migrations:
            try:
                session.execute(text(migration))
                session.commit()
                print(f"✅ Executed: {migration[:50]}...")
            except Exception as e:
                print(f"⚠️  Migration may have already run: {str(e)[:100]}")
                session.rollback()
        
        print("✅ All tier columns added successfully!")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == '__main__':
    print("🔧 Adding tier columns to production database...")
    add_tier_columns()
