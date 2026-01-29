"""
Multi-Gym Franchise Manager
Manage multiple gym locations from single admin panel
"""

from typing import List, Dict, Optional
from datetime import datetime
from models import Gym, Member, Fee, User
from sqlalchemy import func


class FranchiseManager:
    """Manage multiple gym locations"""
    
    def __init__(self, session_factory):
        self.session = session_factory()
    
    # ==================== GYM MANAGEMENT ====================
    
    def create_gym(self, name: str, owner_id: int, location: str = None,
                   currency: str = '$', timezone: str = 'UTC') -> int:
        """
        Create new gym location
        
        Returns:
            gym_id
        """
        gym = Gym(
            name=name,
            owner_id=owner_id,
            location=location,
            currency=currency,
            timezone=timezone,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        self.session.add(gym)
        self.session.commit()
        
        return gym.id
    
    def get_all_gyms(self, owner_id: Optional[int] = None) -> List[Dict]:
        """
        Get all gyms (optionally filtered by owner)
        
        Returns:
            List of gym details
        """
        query = self.session.query(Gym)
        
        if owner_id:
            query = query.filter_by(owner_id=owner_id)
        
        gyms = query.all()
        
        result = []
        for gym in gyms:
            result.append({
                'id': gym.id,
                'name': gym.name,
                'location': gym.location,
                'currency': gym.currency,
                'owner_id': gym.owner_id,
                'is_active': gym.is_active,
                'created_at': gym.created_at.strftime('%Y-%m-%d'),
                'member_count': self.session.query(Member).filter_by(gym_id=gym.id, active=True).count(),
                'monthly_revenue': self._get_monthly_revenue(gym.id)
            })
        
        return result
    
    def _get_monthly_revenue(self,gym_id: int) -> float:
        """Get current month revenue for a gym"""
        current_month = datetime.now().strftime('%Y-%m')
        
        revenue = self.session.query(func.sum(Fee.amount)).join(Member).filter(
            Member.gym_id == gym_id,
            Fee.month == current_month
        ).scalar()
        
        return float(revenue) if revenue else 0.0
    
    def deactivate_gym(self, gym_id: int) -> bool:
        """Deactivate a gym location"""
        gym = self.session.query(Gym).filter_by(id=gym_id).first()
        if gym:
            gym.is_active = False
            self.session.commit()
            return True
        return False
    
    # ==================== CROSS-LOCATION ANALYTICS ====================
    
    def get_franchise_summary(self, owner_id: int) -> Dict:
        """
        Get summary statistics across all gyms
        
        Returns:
            Consolidated stats for all locations
        """
        gyms = self.session.query(Gym).filter_by(owner_id=owner_id, is_active=True).all()
        gym_ids = [g.id for g in gyms]
        
        # Total members across all locations
        total_members = self.session.query(Member).filter(
            Member.gym_id.in_(gym_ids),
            Member.is_active == True
        ).count()
        
        # Total revenue this month
        current_month = datetime.now().strftime('%Y-%m')
        total_revenue = self.session.query(func.sum(Fee.amount)).join(Member).filter(
            Member.gym_id.in_(gym_ids),
            Fee.month == current_month
        ).scalar() or 0
        
        # Average members per gym
        avg_members = total_members / len(gym_ids) if gym_ids else 0
        
        # Top performing gym
        gym_revenues = []
        for gym in gyms:
            revenue = self._get_monthly_revenue(gym.id)
            gym_revenues.append((gym, revenue))
        
        top_gym = max(gym_revenues, key=lambda x: x[1]) if gym_revenues else (None, 0)
        
        return {
            'total_locations': len(gyms),
            'total_members': total_members,
            'total_revenue': float(total_revenue),
            'avg_members_per_gym': round(avg_members, 1),
            'top_performing_gym': {
                'name': top_gym[0].name if top_gym[0] else 'N/A',
                'revenue': top_gym[1]
            }
        }
    
    def get_comparative_analytics(self, owner_id: int) -> List[Dict]:
        """
        Compare performance across all gym locations
        
        Returns:
            List of gyms with comparative metrics
        """
        gyms = self.session.query(Gym).filter_by(owner_id=owner_id, is_active=True).all()
        current_month = datetime.now().strftime('%Y-%m')
        
        results = []
        for gym in gyms:
            # Member count
            member_count = self.session.query(Member).filter_by(
                gym_id=gym.id,
                active=True
            ).count()
            
            # Revenue
            revenue = self._get_monthly_revenue(gym.id)
            
            # Payment collection rate
            paid_count = self.session.query(Fee).join(Member).filter(
                Member.gym_id == gym.id,
                Fee.month == current_month
            ).count()
            
            collection_rate = (paid_count / member_count * 100) if member_count > 0 else 0
            
            # Revenue per member
            revenue_per_member = (revenue / member_count) if member_count > 0 else 0
            
            results.append({
                'gym_id': gym.id,
                'gym_name': gym.name,
                'location': gym.location,
                'members': member_count,
                'revenue': revenue,
                'collection_rate': round(collection_rate, 1),
                'revenue_per_member': round(revenue_per_member, 2)
            })
        
        # Sort by revenue (descending)
        results.sort(key=lambda x: x['revenue'], reverse=True)
        
        return results
    
    # ==================== SHARED MEMBERSHIP ====================
    
    def enable_shared_membership(self, member_id: int, gym_ids: List[int]) -> bool:
        """
        Allow member to access multiple gym locations
        
        Args:
            member_id: Member ID
            gym_ids: List of gym IDs to grant access
        """
        from models import SharedAccess
        
        # Clear existing shared access
        self.session.query(SharedAccess).filter_by(member_id=member_id).delete()
        
        # Add new shared access
        for gym_id in gym_ids:
            access = SharedAccess(
                member_id=member_id,
                gym_id=gym_id,
                granted_at=datetime.utcnow()
            )
            self.session.add(access)
        
        self.session.commit()
        return True
    
    def get_shared_access_gyms(self, member_id: int) -> List[Dict]:
        """Get list of gyms a member has access to"""
        from models import SharedAccess
        
        accesses = self.session.query(SharedAccess, Gym).join(Gym).filter(
            SharedAccess.member_id == member_id
        ).all()
        
        return [{
            'gym_id': gym.id,
            'gym_name': gym.name,
            'location': gym.location,
            'granted_at': access.granted_at.strftime('%Y-%m-%d')
        } for access, gym in accesses]
    
    # ==================== WHITE-LABEL BRANDING ====================
    
    def set_gym_branding(self, gym_id: int, branding: Dict) -> bool:
        """
        Set custom branding for a gym
        
        Args:
            branding: Dict with logo_url, primary_color, secondary_color, etc.
        """
        gym = self.session.query(Gym).filter_by(id=gym_id).first()
        if not gym:
            return False
        
        gym.logo_url = branding.get('logo_url')
        gym.primary_color = branding.get('primary_color', '#8b5cf6')
        gym.secondary_color = branding.get('secondary_color', '#6366f1')
        gym.custom_domain = branding.get('custom_domain')
        
        self.session.commit()
        return True
    
    def get_gym_branding(self, gym_id: int) -> Dict:
        """Get branding settings for a gym"""
        gym = self.session.query(Gym).filter_by(id=gym_id).first()
        if not gym:
            return {}
        
        return {
            'logo_url': gym.logo_url,
            'primary_color': gym.primary_color or '#8b5cf6',
            'secondary_color': gym.secondary_color or '#6366f1',
            'custom_domain': gym.custom_domain,
            'gym_name': gym.name
        }


# Add to models.py:
"""
class SharedAccess(Base):
    __tablename__ = 'shared_access'
    
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey('members.id'), nullable=False, index=True)
    gym_id = Column(Integer, ForeignKey('gyms.id'), nullable=False, index=True)
    granted_at = Column(DateTime, default=datetime.utcnow)
    
    member = relationship('Member')
    gym = relationship('Gym')
"""
