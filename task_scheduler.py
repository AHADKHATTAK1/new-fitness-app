"""
Task Scheduler for Automation
Runs daily automation tasks using APScheduler
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from automation_manager import AutomationManager
from models import Gym
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os


class TaskScheduler:
    """Background task scheduler for automation"""
    
    def __init__(self, database_url: str = None):
        self.scheduler = BackgroundScheduler()
        
        # Database setup
        if database_url is None:
            database_url = os.getenv('DATABASE_URL', 'sqlite:///gym.db')
        
        self.engine = create_engine(database_url)
        self.SessionFactory = sessionmaker(bind=self.engine)
    
    def start(self):
        """Start the scheduler"""
        # Run daily at midnight
        self.scheduler.add_job(
            func=self.run_all_gym_automations,
            trigger='cron',
            hour=0,
            minute=0,
            id='daily_automation'
        )
        
        self.scheduler.start()
        print("✅ Task Scheduler started - running daily at midnight")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
    
    def run_all_gym_automations(self):
        """Run automation for all gyms"""
        session = self.SessionFactory()
        
        try:
            gyms = session.query(Gym).all()
            automation_mgr = AutomationManager(session)
            
            for gym in gyms:
                print(f"Running automation for gym: {gym.name}")
                results = automation_mgr.run_daily_automations(gym.id)
                
                print(f"  Payment reminders sent: {results['payment_reminders']}")
                print(f"  Birthday wishes sent: {results['birthdays']}")
                print(f"  Re-engagement emails sent: {results['reengagement']}")
                
                if results['errors']:
                    print(f"  Errors: {results['errors']}")
        
        except Exception as e:
            print(f"Error in automation: {str(e)}")
        
        finally:
            session.close()
    
    def run_manual(self):
        """Run automation manually (for testing)"""
        print("▶️ Running manual automation test...")
        self.run_all_gym_automations()


# Global scheduler instance
scheduler = None

def init_scheduler(app=None):
    """Initialize scheduler (call this in app.py)"""
    global scheduler
    
    database_url = os.getenv('DATABASE_URL')
    scheduler = TaskScheduler(database_url)
    scheduler.start()
    
    return scheduler
