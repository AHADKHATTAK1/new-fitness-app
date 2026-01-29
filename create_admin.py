"""
Create admin user directly in Railway PostgreSQL database
Run this once to create your admin account
"""

from models import User, Gym, get_session
from werkzeug.security import generate_password_hash
import os

def create_admin():
    """Create admin user in database"""
    session = get_session()
    
    # Admin details - CHANGE THESE!
    ADMIN_EMAIL = "zaidanfitnessgym@gmail.com"
    ADMIN_PASSWORD = "your-password-here"  # Change this!
    
    try:
        # Check if user exists
        existing = session.query(User).filter_by(email=ADMIN_EMAIL).first()
        if existing:
            print(f"✅ User {ADMIN_EMAIL} already exists")
            print("Updating password...")
            existing.password_hash = generate_password_hash(ADMIN_PASSWORD)
            session.commit()
            print("✅ Password updated!")
        else:
            # Create new user
            user = User(
                email=ADMIN_EMAIL,
                password_hash=generate_password_hash(ADMIN_PASSWORD),
                role='admin'
            )
            session.add(user)
            session.flush()
            
            # Create default gym
            gym = Gym(
                user_id=user.id,
                name='ZAIDAN FITNESS RECORD',
                currency='Rs'
            )
            session.add(gym)
            session.commit()
            
            print(f"✅ Admin created: {ADMIN_EMAIL}")
            print(f"✅ Gym created: {gym.name}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == '__main__':
    print("🔧 Creating admin user...")
    create_admin()
    print("✅ Done!")
