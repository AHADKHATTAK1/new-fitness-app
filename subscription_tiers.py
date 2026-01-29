"""
Subscription Tier Management System
Handles tier limits, features, and access control
"""

from datetime import datetime, timedelta

# Tier Configurations
TIERS = {
    'starter': {
        'name': 'Starter',
        'price_monthly': 49,
        'price_yearly': 490,  # ~10% discount
        'currency': 'USD',
        'limits': {
            'gyms': 1,
            'members': 250,
            'staff': 2,
            'exports_per_month': 10,
            'storage_mb': 500,
            'api_calls_per_day': 0
        },
        'features': [
            'basic_dashboard',
            'member_management',
            'payment_tracking',
            'basic_reports',
            'email_support',
            'mobile_app'
        ],
        'description': 'Perfect for small gyms getting started',
        'highlight': False
    },
    
    'professional': {
        'name': 'Professional',
        'price_monthly': 149,
        'price_yearly': 1490,  # ~17% discount
        'currency': 'USD',
        'limits': {
            'gyms': 5,
            'members': 1000,
            'staff': 10,
            'exports_per_month': 100,
            'storage_mb': 5000,
            'api_calls_per_day': 1000
        },
        'features': [
            'all_starter_features',
            'marketing_automation',
            'advanced_analytics',
            'ai_churn_prediction',
            'multi_gym_management',
            'priority_support',
            'custom_branding',
            'bulk_operations',
            'advanced_reports'
        ],
        'description': 'For growing gyms with multiple locations',
        'highlight': True  # Most popular
    },
    
    'enterprise': {
        'name': 'Enterprise',
        'price_monthly': 499,
        'price_yearly': 4990,
        'currency': 'USD',
        'limits': {
            'gyms': -1,  # unlimited
            'members': -1,
            'staff': -1,
            'exports_per_month': -1,
            'storage_mb': 50000,
            'api_calls_per_day': 10000
        },
        'features': [
            'all_pro_features',
            'white_label',
            'api_access',
            'webhooks',
            'custom_domain',
            'dedicated_account_manager',
            'sla_guarantee',
            '24_7_support',
            'advanced_integrations',
            'custom_workflows'
        ],
        'description': 'For large gym chains and franchises',
        'highlight': False
    },
    
    'enterprise_plus': {
        'name': 'Enterprise+',
        'price_monthly': 1999,
        'price_yearly': 19990,
        'currency': 'USD',
        'limits': {
            'gyms': -1,
            'members': -1,
            'staff': -1,
            'exports_per_month': -1,
            'storage_mb': -1,  # unlimited
            'api_calls_per_day': -1
        },
        'features': [
            'all_enterprise_features',
            'on_premise_deployment',
            'custom_development',
            'phone_support',
            'training_sessions',
            'data_migration',
            'compliance_support',
            'multi_region_deployment'
        ],
        'description': 'Ultimate package with dedicated resources',
        'highlight': False
    }
}

# Pakistan-specific tiers (in PKR)
TIERS_PAKISTAN = {
    'starter_pk': {
        'name': 'Starter (Pakistan)',
        'price_monthly': 4000,  # PKR
        'price_yearly': 40000,
        'currency': 'PKR',
        'limits': TIERS['starter']['limits'],
        'features': TIERS['starter']['features'],
        'description': 'Pakistan special pricing - JazzCash/EasyPaisa',
        'payment_methods': ['jazzcash', 'easypaisa']
    },
    'professional_pk': {
        'name': 'Professional (Pakistan)',
        'price_monthly': 12000,
        'price_yearly': 120000,
        'currency': 'PKR',
        'limits': TIERS['professional']['limits'],
        'features': TIERS['professional']['features'],
        'description': 'Pakistan special pricing - JazzCash/EasyPaisa',
        'payment_methods': ['jazzcash', 'easypaisa']
    }
}


class TierManager:
    """Manage subscription tiers, limits, and features"""
    
    @staticmethod
    def get_tier_config(tier_name):
        """Get configuration for a specific tier"""
        # Check regular tiers first
        if tier_name in TIERS:
            return TIERS[tier_name]
        # Check Pakistan tiers
        if tier_name in TIERS_PAKISTAN:
            return TIERS_PAKISTAN[tier_name]
        # Default to starter
        return TIERS['starter']
    
    @staticmethod
    def check_limit(user, resource, count):
        """
        Check if user has reached their tier limit
        
        Args:
            user: User object
            resource: Resource type ('gyms', 'members', 'staff', 'exports')
            count: Current count
            
        Returns:
            tuple: (has_capacity, limit, message)
        """
        # Default to starter if tier is None (backwards compatibility)
        tier = user.subscription_tier or 'starter'
        
        if tier not in TIERS:
            tier = 'starter'
            
        tier_config = TIERS[tier]
        limit = tier_config['limits'].get(resource, -1)
        
        # -1 means unlimited
        if limit == -1:
            return True
            
        return count < limit
    
    @staticmethod
    def get_limit(user, resource):
        """Get the limit value for a resource"""
        tier = TierManager.get_tier_config(user.subscription_tier)
        return tier['limits'].get(resource, 0)
    
    @staticmethod
    def has_feature(user, feature):
        """
        Check if user's tier includes a specific feature
        
        Args:
            user: User object
            feature: Feature name to check
            
        Returns:
            bool: True if feature is available
        """
        if not user or not hasattr(user, 'subscription_tier'):
            return False
            
        tier = TierManager.get_tier_config(user.subscription_tier)
        features = tier.get('features', [])
        
        # Check direct feature
        if feature in features:
            return True
            
        # Check inherited features (all_starter_features, all_pro_features, etc.)
        if 'all_starter_features' in features and feature in TIERS['starter']['features']:
            return True
        if 'all_pro_features' in features and feature in TIERS['professional']['features']:
            return True
        if 'all_enterprise_features' in features and feature in TIERS['enterprise']['features']:
            return True
            
        return False
    
    @staticmethod
    def get_upgrade_path(current_tier):
        """
        Suggest next tier upgrade
        
        Returns:
            dict: Next tier config or None if already at top tier
        """
        order = ['starter', 'professional', 'enterprise', 'enterprise_plus']
        
        # Handle Pakistan tiers
        if current_tier.endswith('_pk'):
            current_tier = current_tier.replace('_pk', '')
        
        if current_tier not in order:
            return None
            
        current_idx = order.index(current_tier)
        if current_idx < len(order) - 1:
            next_tier = order[current_idx + 1]
            return {
                'tier_name': next_tier,
                'config': TIERS[next_tier]
            }
        return None
    
    @staticmethod
    def calculate_price(tier_name, billing_cycle='monthly', currency='USD'):
        """
        Calculate price for a tier
        
        Args:
            tier_name: Tier name
            billing_cycle: 'monthly' or 'yearly'
            currency: 'USD' or 'PKR'
            
        Returns:
            float: Price amount
        """
        # Select tier set based on currency
        if currency == 'PKR':
            tier = TIERS_PAKISTAN.get(f'{tier_name}_pk')
        else:
            tier = TIERS.get(tier_name)
            
        if not tier:
            return 0
            
        if billing_cycle == 'yearly':
            return tier['price_yearly']
        return tier['price_monthly']
    
    @staticmethod
    def get_tier_comparison():
        """
        Get comparison data for all tiers
        Used for pricing pages
        
        Returns:
            list: List of tier configs for display
        """
        return [
            {'tier_id': 'starter', **TIERS['starter']},
            {'tier_id': 'professional', **TIERS['professional']},
            {'tier_id': 'enterprise', **TIERS['enterprise']},
            {'tier_id': 'enterprise_plus', **TIERS['enterprise_plus']}
        ]
    
    @staticmethod
    def is_trial_expired(user):
        """Check if user's trial period has expired"""
        if not user or not hasattr(user, 'subscription_status'):
            return True
            
        if user.subscription_status == 'trial':
            if hasattr(user, 'subscription_expiry'):
                return datetime.utcnow() > user.subscription_expiry
            return True  # No expiry date = expired
        return False
    
    @staticmethod
    def get_days_remaining(user):
        """Get days remaining in subscription"""
        if not user or not hasattr(user, 'subscription_expiry'):
            return 0
            
        if user.subscription_expiry:
            delta = user.subscription_expiry - datetime.utcnow()
            return max(0, delta.days)
        return 0


# Helper function for templates
def format_limit(limit):
    """Format limit for display"""
    if limit == -1:
        return "Unlimited"
    return f"{limit:,}"


def get_tier_badge_class(tier_name):
    """Get CSS class for tier badge"""
    badge_classes = {
        'starter': 'tier-badge-starter',
        'professional': 'tier-badge-pro',
        'enterprise': 'tier-badge-enterprise',
        'enterprise_plus': 'tier-badge-premium'
    }
    return badge_classes.get(tier_name, 'tier-badge-default')
