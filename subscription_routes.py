# Add this route to app.py for 3-day trial activation

@app.route('/activate_trial', methods=['POST'])
def activate_trial():
    """Activate 3-day free trial"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    username = session.get('username')
    user = auth_manager.session.query(User).filter_by(email=username).first()
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('subscription'))
    
    # Check if user already had a trial
    if hasattr(user, 'trial_used') and user.trial_used:
        flash('You have already used your free trial', 'warning')
        return redirect(url_for('subscription'))
    
    # Activate 3-day trial
    from datetime import datetime, timedelta
    user.subscription_status = 'trial'
    user.subscription_expiry = datetime.utcnow() + timedelta(days=3)
    user.trial_used = True
    
    auth_manager.session.commit()
    
    flash('🎉 3-day trial activated! Enjoy full access. Pay anytime when ready.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/extend_subscription', methods=['POST'])
def extend_subscription():
    """Allow users to extend/pay for subscription anytime"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    plan_type = request.form.get('plan_type', 'monthly')  # monthly or yearly
    
    # Redirect to subscription page to choose payment method
    session['selected_plan'] = plan_type
    flash(f'Selected {plan_type} plan. Choose your payment method below.', 'info')
    return redirect(url_for('subscription'))


@app.route('/check_subscription_status')
def check_subscription_status():
    """API endpoint to check current subscription status"""
    if 'logged_in' not in session:
        return jsonify({'status': 'not_logged_in'}), 401
    
    username = session.get('username')
    user = auth_manager.session.query(User).filter_by(email=username).first()
    
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
    
    from datetime import datetime
    
    # Check if subscription is active
    is_active = False
    days_remaining = 0
    
    if user.subscription_status == 'active' and user.subscription_expiry:
        if user.subscription_expiry > datetime.utcnow():
            is_active = True
            days_remaining = (user.subscription_expiry - datetime.utcnow()).days
    elif user.subscription_status == 'trial' and user.subscription_expiry:
        if user.subscription_expiry > datetime.utcnow():
            is_active = True
            days_remaining = (user.subscription_expiry - datetime.utcnow()).days
    
    return jsonify({
        'status': user.subscription_status,
        'is_active': is_active,
        'days_remaining': days_remaining,
        'expiry_date': user.subscription_expiry.strftime('%Y-%m-%d') if user.subscription_expiry else None,
        'can_extend': True  # Always allow extension/payment
    })
