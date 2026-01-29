"""
Marketing Automation Manager
Handles automated campaigns: payment reminders, birthday wishes, re-engagement
"""

from datetime import datetime, timedelta
from typing import List, Dict
from models import Member, Fee, Gym, Attendance, User
from email_utils import EmailSender
from sqlalchemy import func
import os


class AutomationManager:
    """Intelligent marketing automation for member engagement"""
    
    def __init__(self, session, email_sender: EmailSender = None):
        self.session = session
        self.email_sender = email_sender or EmailSender()
    
    # ==================== PAYMENT REMINDERS ====================
    
    def check_payment_reminders(self, gym_id: int, days_before: int = 3) -> List[Dict]:
        """
        Find members who need payment reminders
        
        Args:
            gym_id: Gym ID to check
            days_before: Send reminder N days before month end
        
        Returns:
            List of members needing reminders
        """
        today = datetime.now().date()
        current_month = datetime.now().strftime('%Y-%m')
        
        # Calculate if we should send (e.g., 3 days before month end)
        days_left_in_month = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        days_remaining = (days_left_in_month.date() - today).days
        
        if days_remaining != days_before:
            return []  # Not time to send yet
        
        # Get unpaid members
        from sqlalchemy import and_
        
        unpaid_members = self.session.query(Member).filter(
            Member.gym_id == gym_id,
            Member.is_active == True
        ).all()
        
        reminders_to_send = []
        for member in unpaid_members:
            # Check if already paid this month
            paid_this_month = self.session.query(Fee).filter(
                Fee.member_id == member.id,
                Fee.month == current_month
            ).first()
            
            if not paid_this_month:
                # Determine amount based on membership type or default
                membership_type = getattr(member, 'membership_type', 'monthly').lower()
                
                # Logic to determine amount (could be expanded to a dynamic mapping)
                if 'vip' in membership_type:
                    amount_due = 10000
                elif 'premium' in membership_type:
                    amount_due = 7000
                else:
                    amount_due = 5000 # Default
                
                reminders_to_send.append({
                    'member_id': member.id,
                    'name': member.name,
                    'email': member.email,
                    'phone': member.phone,
                    'month': current_month,
                    'amount_due': amount_due
                })
        
        return reminders_to_send
    
    def send_payment_reminder(self, member: Dict, gym: Gym) -> bool:
        """Send payment reminder email to member"""
        if not member.get('email'):
            return False
        
        subject = f"Payment Reminder - {gym.name}"
        
        # HTML email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">💳 Payment Reminder</h1>
            </div>
            
            <div style="padding: 30px; background: #f9fafb;">
                <p>Hi <strong>{member['name']}</strong>,</p>
                
                <p>This is a friendly reminder that your membership payment for <strong>{member['month']}</strong> is due soon.</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
                    <h3 style="margin-top: 0;">Payment Details:</h3>
                    <p><strong>Amount:</strong> {gym.currency}{member['amount_due']}</p>
                    <p><strong>Due Date:</strong> End of {member['month']}</p>
                </div>
                
                <p>Please make your payment at your earliest convenience to avoid any interruption in your membership.</p>
                
                <p style="margin-top: 30px;">Thank you for being a valued member!</p>
                
                <p>Best regards,<br>
                <strong>{gym.name}</strong></p>
            </div>
            
            <div style="background: #1f2937; color: white; padding: 20px; text-align: center; font-size: 12px;">
                <p>You received this email because you are a member at {gym.name}</p>
            </div>
        </body>
        </html>
        """
        
        return self.email_sender.send_email(member['email'], subject, body)
    
    # ==================== BIRTHDAY WISHES ====================
    
    def check_birthdays_today(self, gym_id: int) -> List[Dict]:
        """Find members with birthday today"""
        today = datetime.now().date()
        
        members = self.session.query(Member).filter(
            Member.gym_id == gym_id,
            Member.is_active == True,
            Member.birthday.isnot(None)
        ).all()
        
        birthday_members = []
        for member in members:
            if member.birthday and member.birthday.month == today.month and member.birthday.day == today.day:
                birthday_members.append({
                    'member_id': member.id,
                    'name': member.name,
                    'email': member.email,
                    'phone': member.phone,
                    'age': today.year - member.birthday.year
                })
        
        return birthday_members
    
    def send_birthday_wish(self, member: Dict, gym: Gym) -> bool:
        """Send birthday email"""
        if not member.get('email'):
            return False
        
        subject = f"🎉 Happy Birthday from {gym.name}!"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 40px; text-align: center;">
                <h1 style="color: white; font-size: 48px; margin: 0;">🎂</h1>
                <h1 style="color: white; margin: 10px 0;">Happy Birthday!</h1>
            </div>
            
            <div style="padding: 40px; background: #fff;">
                <p style="font-size: 18px;">Dear <strong>{member['name']}</strong>,</p>
                
                <p style="font-size: 16px; line-height: 1.6;">
                    The entire team at {gym.name} wishes you a very happy birthday! 🎉
                </p>
                
                <p style="font-size: 16px; line-height: 1.6;">
                    Thank you for being such an amazing part of our fitness family. 
                    We hope your special day is filled with joy, health, and happiness!
                </p>
                
                <div style="background: #fef3c7; padding: 20px; border-radius: 8px; margin: 30px 0; text-align: center;">
                    <h3 style="color: #92400e; margin-top: 0;">🎁 Birthday Special!</h3>
                    <p style="color: #78350f; margin-bottom: 0;">Show this email for a special surprise at your next visit!</p>
                </div>
                
                <p style="margin-top: 30px; font-size: 16px;">
                    Keep crushing your fitness goals!
                </p>
                
                <p>With love,<br>
                <strong>Team {gym.name}</strong></p>
            </div>
        </body>
        </html>
        """
        
        return self.email_sender.send_email(member['email'], subject, body)
    
    # ==================== WELCOME SEQUENCE ====================
    
    def send_welcome_email(self, member_id: int) -> bool:
        """Send welcome email to new member"""
        member = self.session.query(Member).filter_by(id=member_id).first()
        if not member or not member.email:
            return False
        
        gym = self.session.query(Gym).filter_by(id=member.gym_id).first()
        
        subject = f"Welcome to {gym.name}! 🎉"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center;">
                <h1 style="color: white; margin: 0;">Welcome Aboard!</h1>
            </div>
            
            <div style="padding: 40px; background: #fff;">
                <p style="font-size: 18px;">Hi <strong>{member.name}</strong>,</p>
                
                <p style="font-size: 16px; line-height: 1.6;">
                    Welcome to the {gym.name} family! We're thrilled to have you join us on your fitness journey. 💪
                </p>
                
                <h3>Here's what to expect:</h3>
                <ul style="line-height: 1.8;">
                    <li>✅ Access to all gym equipment and facilities</li>
                    <li>✅ Professional trainers to guide you</li>
                    <li>✅ Group classes and specialized programs</li>
                    <li>✅ Member portal for tracking your progress</li>
                </ul>
                
                <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">🎯 Quick Start Tips:</h3>
                    <ol style="margin: 0; padding-left: 20px;">
                        <li>Download your membership card from the portal</li>
                        <li>Book your first free fitness assessment</li>
                        <li>Join our WhatsApp community for updates</li>
                        <li>Set your fitness goals in your profile</li>
                    </ol>
                </div>
                
                <p style="font-size: 16px; margin-top: 30px;">
                    If you have any questions, we're here to help!
                </p>
                
                <p>Best regards,<br>
                <strong>Team {gym.name}</strong></p>
            </div>
        </body>
        </html>
        """
        
        return self.email_sender.send_email(member.email, subject, body)
    
    # ==================== RE-ENGAGEMENT CAMPAIGNS ====================
    
    def check_inactive_members(self, gym_id: int, inactive_days: int = 30) -> List[Dict]:
        """Find members who haven't checked in recently"""
        cutoff_date = datetime.now() - timedelta(days=inactive_days)
        
        from sqlalchemy import or_
        inactive_members = self.session.query(Member).filter(
            Member.gym_id == gym_id,
            Member.is_active == True,
            or_(Member.last_check_in < cutoff_date, Member.last_check_in == None)
        ).all()
        
        return [{
            'member_id': m.id,
            'name': m.name,
            'email': m.email,
            'phone': m.phone,
            'last_visit': m.last_check_in.strftime('%Y-%m-%d') if m.last_check_in else 'Never'
        } for m in inactive_members if m.email]
    
    def send_comeback_email(self, member: Dict, gym: Gym) -> bool:
        """Send re-engagement email"""
        subject = f"We Miss You at {gym.name}! 💙"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 40px; text-align: center;">
                <h1 style="color: white; margin: 0;">We Miss You!</h1>
            </div>
            
            <div style="padding: 40px; background: #fff;">
                <p style="font-size: 18px;">Hi <strong>{member['name']}</strong>,</p>
                
                <p style="font-size: 16px; line-height: 1.6;">
                    We noticed you haven't visited {gym.name} in a while. 
                    Your last visit was on <strong>{member['last_visit']}</strong>.
                </p>
                
                <p style="font-size: 16px; line-height: 1.6;">
                    Life gets busy - we totally get it! But your fitness goals are waiting for you. 💪
                </p>
                
                <div style="background: #10b981; color: white; padding: 30px; border-radius: 8px; margin: 30px 0; text-align: center;">
                    <h2 style="margin-top: 0;">🎁 Comeback Special!</h2>
                    <p style="font-size: 20px; margin-bottom: 0;">
                        Get <strong>20% OFF</strong> your next month when you visit this week!
                    </p>
                </div>
                
                <p style="font-size: 16px;">
                    We'd love to see you back at the gym. Your community is here waiting for you!
                </p>
                
                <p style="margin-top: 30px;">Stay strong,<br>
                <strong>Team {gym.name}</strong></p>
            </div>
        </body>
        </html>
        """
        
        return self.email_sender.send_email(member['email'], subject, body)
    
    # ==================== BULK AUTOMATION RUNNER ====================
    
    def run_daily_automations(self, gym_id: int) -> Dict:
        """
        Run all daily automation checks
        Should be called by scheduler (cron job or Celery)
        """
        gym = self.session.query(Gym).filter_by(id=gym_id).first()
        results = {
            'payment_reminders': 0,
            'birthdays': 0,
            'reengagement': 0,
            'errors': []
        }
        
        try:
            # Payment Reminders
            payment_reminders = self.check_payment_reminders(gym_id, days_before=3)
            for member in payment_reminders:
                if self.send_payment_reminder(member, gym):
                    results['payment_reminders'] += 1
            
            # Birthday Wishes
            birthdays = self.check_birthdays_today(gym_id)
            for member in birthdays:
                if self.send_birthday_wish(member, gym):
                    results['birthdays'] += 1
            
            # Re-engagement (run weekly, check day of week)
            if datetime.now().weekday() == 0:  # Monday
                inactive = self.check_inactive_members(gym_id, inactive_days=30)
                for member in inactive[:10]:  # Limit to 10 per week
                    if self.send_comeback_email(member, gym):
                        results['reengagement'] += 1
        
        except Exception as e:
            results['errors'].append(str(e))
        
        return results

    # ==================== BUSINESS REPORTING ====================
    
    def generate_daily_business_summary(self, gym_id: int) -> bool:
        """Generate and send a daily summary email to the gym owner"""
        gym = self.session.query(Gym).filter_by(id=gym_id).first()
        if not gym:
            return False
            
        owner = self.session.query(User).filter_by(id=gym.user_id).first()
        if not owner or not owner.email:
            return False
            
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # 1. Today's Revenue
        revenue_today = self.session.query(func.sum(Fee.amount))\
            .join(Member)\
            .filter(Member.gym_id == gym_id, Fee.paid_date >= today_start, Fee.paid_date < today_end)\
            .scalar() or 0
            
        # 2. Today's Check-ins
        checkins_today = self.session.query(func.count(Attendance.id))\
            .join(Member)\
            .filter(Member.gym_id == gym_id, Attendance.check_in_time >= today_start, Attendance.check_in_time < today_end)\
            .scalar() or 0
            
        # 3. New Members Today
        new_members_today = self.session.query(func.count(Member.id))\
            .filter(Member.gym_id == gym_id, Member.created_at >= today_start, Member.created_at < today_end)\
            .scalar() or 0
            
        # 4. Expiring Trials Today
        expiring_today = self.session.query(func.count(Member.id))\
            .filter(Member.gym_id == gym_id, Member.is_trial == True, Member.trial_end_date == today_start.date())\
            .scalar() or 0
            
        # 5. Get Overdue Escalations
        overdue_members = self.get_overdue_escalation_list(gym_id)
        overdue_html = ""
        if overdue_members:
            overdue_html = """
            <h3 style="color: #ef4444; border-bottom: 2px solid #fee2e2; padding-bottom: 10px; margin-top: 30px;">🚨 Priority Overdue Alerts</h3>
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
            """
            for m in overdue_members[:5]: # Top 5 priority
                overdue_html += f"""
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #f1f5f9;">
                        <strong>{m['name']}</strong><br>
                        <span style="font-size: 11px; color: #94a3b8;">{m['phone']}</span>
                    </td>
                    <td style="padding: 10px 0; text-align: right; color: #ef4444; font-weight: bold;">
                        {m['days_overdue']} days late
                    </td>
                </tr>
                """
            if len(overdue_members) > 5:
                overdue_html += f"<tr><td colspan='2' style='text-align: center; color: #94a3b8; font-size: 11px; padding: 10px 0;'>+ {len(overdue_members)-5} more overdue</td></tr>"
            overdue_html += "</table>"

        subject = f"📊 Daily Business Summary - {gym.name}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f3f4f6; padding: 20px;">
            <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 30px; text-align: center; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0;">Business Summary</h1>
                <p style="color: #94a3b8; margin-top: 5px;">{today_start.strftime('%B %d, %Y')}</p>
            </div>
            
            <div style="padding: 30px; background: white; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                    <div style="padding: 20px; background: #f0fdf4; border-radius: 8px; text-align: center; border: 1px solid #bbf7d0;">
                        <h4 style="margin: 0; color: #166534; text-transform: uppercase; font-size: 12px;">Today's Revenue</h4>
                        <p style="font-size: 24px; font-weight: bold; margin: 10px 0; color: #14532d;">{gym.currency}{float(revenue_today):,.0f}</p>
                    </div>
                    <div style="padding: 20px; background: #eff6ff; border-radius: 8px; text-align: center; border: 1px solid #bfdbfe;">
                        <h4 style="margin: 0; color: #1e40af; text-transform: uppercase; font-size: 12px;">New Members</h4>
                        <p style="font-size: 24px; font-weight: bold; margin: 10px 0; color: #1e3a8a;">{new_members_today}</p>
                    </div>
                </div>
                
                <h3 style="color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">📉 Performance Metrics</h3>
                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <tr>
                        <td style="padding: 12px 0; color: #64748b;">Daily Attendance</td>
                        <td style="padding: 12px 0; text-align: right; font-weight: bold; color: #1e293b;">{checkins_today} check-ins</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 0; color: #64748b;">Expiring Trials</td>
                        <td style="padding: 12px 0; text-align: right; font-weight: bold; color: #f59e0b;">{expiring_today} members</td>
                    </tr>
                </table>
                
                {overdue_html}
                
                <div style="margin-top: 40px; padding: 20px; background: #f8fafc; border-radius: 8px; text-align: center;">
                    <a href="https://fitnessmanagement.site/dashboard" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">View Full Dashboard</a>
                </div>
            </div>
            
            <p style="text-align: center; color: #94a3b8; font-size: 12px; margin-top: 20px;">
                This is an automated report from your Gym Manager system.
            </p>
        </body>
        </html>
        """
        
        return self.email_sender.send_email(owner.email, subject, body)

    def send_milestone_alert(self, member_id: int, milestone_count: int) -> bool:
        """Send a congratulatory email for attendance milestones"""
        member = self.session.query(Member).filter_by(id=member_id).first()
        if not member or not member.email:
            return False
            
        gym = self.session.query(Gym).filter_by(id=member.gym_id).first()
        
        subject = f"🔥 MASSIVE MILESTONE! {milestone_count} Visits at {gym.name}!"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; text-align: center;">
            <div style="background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%); padding: 50px;">
                <h1 style="color: white; font-size: 60px; margin: 0;">🏆</h1>
                <h1 style="color: white; margin: 10px 0;">{milestone_count} VISITS!</h1>
                <p style="color: rgba(255,255,255,0.8); font-size: 18px;">That's pure dedication, {member.name}</p>
            </div>
            
            <div style="padding: 40px;">
                <p style="font-size: 20px; color: #1e293b; line-height: 1.6;">
                    You just hit your <strong>{milestone_count}th</strong> visit at {gym.name}! 
                    Most people quit long before this, but you're still showing up and putting in the work.
                </p>
                
                <div style="margin: 40px 0; padding: 30px; border: 2px dashed #f59e0b; border-radius: 12px; background: #fffbeb;">
                    <h3 style="color: #92400e; margin-top: 0;">🎁 Milestone Reward</h3>
                    <p style="color: #b45309;">Show this email to the front desk for a <strong>FREE protein shake</strong> or <strong>Gym Merch</strong>!</p>
                </div>
                
                <p style="color: #64748b;">Keep pushing, keep growing!</p>
                <p style="font-weight: bold; color: #1e293b;">Team {gym.name}</p>
            </div>
        </body>
        </html>
        """
        
        return self.email_sender.send_email(member.email, subject, body)

    def get_overdue_escalation_list(self, gym_id: int) -> List[Dict]:
        """Identify members overdue by 7+ days for priority alerts"""
        today = datetime.now()
        current_month = today.strftime('%Y-%m')
        
        # This logic is a simplified proxy - in a real app, you'd check a dedicated 'due_date' field
        unpaid_members = self.session.query(Member).filter(
            Member.gym_id == gym_id,
            Member.is_active == True
        ).all()
        
        escalation_list = []
        for member in unpaid_members:
            paid_this_month = self.session.query(Fee).filter(
                Fee.member_id == member.id,
                Fee.month == current_month
            ).first()
            
            # If it's more than 7 days into the month and no payment
            if not paid_this_month and today.day > 7:
                escalation_list.append({
                    'id': member.id,
                    'name': member.name,
                    'phone': member.phone,
                    'days_overdue': today.day # Days since 1st of month
                })
        
        return escalation_list
