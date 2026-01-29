"""
Subscription tier upgrade/downgrade routes
Handles Stripe checkout for tier changes
"""

from flask import request, redirect, url_for, session, flash, current_app
from subscription_tiers import TierManager, TIERS, TIERS_PAKISTAN
from models import User
import stripe
import os
from datetime import datetime, timedelta


def init_upgrade_routes(app, auth_manager, security_manager):
    """Initialize tier upgrade routes"""
    
    @app.route('/subscription')
    def subscription():
        """Payment required page"""
        from flask import render_template
        return render_template('subscription.html')

    @app.route('/subscription_plans')
    def subscription_plans():
        """Display subscription pricing page"""
        from flask import render_template
        
        # Get current user if logged in
        username = session.get('username')
        current_tier = None
        current_user = None
        subscription_active = False
        if username:
            user = auth_manager.session.query(User).filter_by(email=username).first()
            if user:
                current_user = user
                current_tier = user.subscription_tier or 'starter'
                try:
                    subscription_active = auth_manager.is_subscription_active(username)
                except Exception:
                    subscription_active = False
        
        return render_template('subscription_plans.html',
                             tiers=TIERS,
                             tiers_pakistan=TIERS_PAKISTAN,
                             current_tier=current_tier,
                             current_user=current_user,
                             subscription_active=subscription_active)

    @app.route('/activate_trial', methods=['POST'])
    def activate_trial():
        """Activate 3-day free trial"""
        if 'logged_in' not in session:
            return redirect(url_for('auth'))
        
        username = session.get('username')
        user = auth_manager.session.query(User).filter_by(email=username).first()
        
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('subscription'))
            
        # Check if already had trial
        if getattr(user, 'subscription_status', None) == 'trial':
            flash('You have already used your trial period.', 'warning')
            return redirect(url_for('subscription_plans'))
        
        # Activate 3-day trial
        user.subscription_status = 'trial'
        user.subscription_expiry = datetime.utcnow() + timedelta(days=3)
        
        auth_manager.session.commit()
        
        # Production Security: Log Audit
        user_id = auth_manager.get_user_id(username)
        if user_id:
            security_manager.log_action(user_id, 'TRIAL_ACTIVATED', 
                                       {'expires_at': user.subscription_expiry.strftime('%Y-%m-%d')}, 
                                       request.remote_addr, request.user_agent.string)
        
        flash('🎉 3-day trial activated! Enjoy full access. Pay anytime when ready.', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/upgrade_tier', methods=['POST'])
    def upgrade_tier():
        """Handle tier upgrade with Stripe checkout"""
        username = session.get('username')
        if not username:
            flash('Please login first', 'error')
            return redirect(url_for('auth'))
        
        user = auth_manager.session.query(User).filter_by(email=username).first()
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('auth'))
        
        # Get form data
        new_tier = request.form.get('tier')
        billing_cycle = request.form.get('cycle', 'monthly')
        
        # Validate tier
        if new_tier not in TIERS:
            flash('Invalid tier selected', 'error')
            return redirect(url_for('subscription_plans'))
        
        # Get tier config
        tier_config = TIERS[new_tier]
        
        # Calculate amount
        if billing_cycle == 'yearly':
            amount = tier_config['price_yearly']
            interval = 'year'
        else:
            amount = tier_config['price_monthly']
            interval = 'month'
        
        # Initialize Stripe (env first, then app config fallback)
        raw_key = os.getenv('STRIPE_SECRET_KEY') or current_app.config.get('STRIPE_SECRET_KEY', '')
        stripe_key = (raw_key or '').strip().strip('"').strip("'")
        stripe.api_key = stripe_key

        if not stripe_key or stripe_key == 'your_stripe_secret_key_here':
            flash('Stripe API is not configured. Please contact administrator.', 'error')
            return redirect(url_for('subscription_plans'))
            
        try:
            # Create Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'{tier_config["name"]} Plan',
                            'description': f'{tier_config["description"]}',
                        },
                        'unit_amount': int(amount * 100),  # Convert to cents
                        'recurring': {
                            'interval': interval
                        }
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=url_for('upgrade_success', tier=new_tier, cycle=billing_cycle, _external=True),
                cancel_url=url_for('subscription_plans', _external=True),
                client_reference_id=user.email,
                metadata={
                    'tier': new_tier,
                    'billing_cycle': billing_cycle,
                    'user_email': user.email
                }
            )
            
            return redirect(checkout_session.url)
            
        except Exception as e:
            flash(f'Payment error: {str(e)}', 'error')
            return redirect(url_for('subscription_plans'))
    
    @app.route('/upgrade_success')
    def upgrade_success():
        """Handle successful tier upgrade"""
        username = session.get('username')
        if not username:
            return redirect(url_for('auth'))
        
        user = auth_manager.session.query(User).filter_by(email=username).first()
        if not user:
            return redirect(url_for('auth'))
        
        # Get tier and cycle from query params
        new_tier = request.args.get('tier')
        billing_cycle = request.args.get('cycle', 'monthly')
        
        # Update user subscription
        user.subscription_tier = new_tier
        user.billing_cycle = billing_cycle
        user.tier_upgraded_at = datetime.utcnow()
        user.subscription_status = 'active'
        
        # Set new expiry date
        if billing_cycle == 'yearly':
            user.subscription_expiry = datetime.utcnow() + timedelta(days=365)
        else:
            user.subscription_expiry = datetime.utcnow() + timedelta(days=30)
        
        auth_manager.session.commit()
        
        # Production Security: Log Audit
        user_id = auth_manager.get_user_id(username)
        if user_id:
            security_manager.log_action(user_id, 'SUBSCRIPTION_UPGRADE', 
                                       {'tier': new_tier, 'cycle': billing_cycle}, 
                                       request.remote_addr, request.user_agent.string)
        
        # Send confirmation email (if email_utils available)
        try:
            from email_utils import EmailSender
            sender = EmailSender()
            tier_config = TIERS[new_tier]
            sender.send_email(
                user.email,
                f'🎉 Subscription Upgraded to {tier_config["name"]}!',
                f'''
                <h2>Congratulations!</h2>
                <p>Your subscription has been upgraded to <strong>{tier_config["name"]}</strong> plan.</p>
                <p><strong>Plan Details:</strong></p>
                <ul>
                    <li>Members: {tier_config["limits"]["members"] if tier_config["limits"]["members"] != -1 else "Unlimited"}</li>
                    <li>Gyms: {tier_config["limits"]["gyms"] if tier_config["limits"]["gyms"] != -1 else "Unlimited"}</li>
                    <li>Billing: {billing_cycle}</li>
                </ul>
                <p>Thank you for your business!</p>
                '''
            )
        except Exception as e:
            print(f"⚠️ Email Error: {str(e)}")
            pass  # Email optional
        
        flash(f'🎉 Successfully upgraded to {TIERS[new_tier]["name"]} plan!', 'success')
        return redirect(url_for('dashboard'))
    
    @app.route('/cancel_subscription', methods=['POST'])
    def cancel_subscription():
        """Cancel subscription (switch to starter at end of period)"""
        username = session.get('username')
        if not username:
            return redirect(url_for('auth'))
        
        user = auth_manager.session.query(User).filter_by(email=username).first()
        if not user:
            return redirect(url_for('auth'))
        
        # Schedule downgrade to starter
        user.tier_downgrade_scheduled = 'starter'
        auth_manager.session.commit()
        
        # Production Security: Log Audit
        user_id = auth_manager.get_user_id(username)
        if user_id:
            security_manager.log_action(user_id, 'SUBSCRIPTION_CANCEL', {}, request.remote_addr, request.user_agent.string)
        
        flash('Subscription will be canceled at end of billing period. You will be moved to Starter plan.', 'info')
        return redirect(url_for('settings'))
