"""
Performance Optimization Utilities
Caching, Query Optimization, and Performance Monitoring
"""

import functools
import time
from datetime import datetime, timedelta
from typing import Any, Callable


class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    def __init__(self):
        self.metrics = {}
    
    def track_time(self, func_name: str):
        """Decorator to track function execution time"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start
                
                # Store metric
                if func_name not in self.metrics:
                    self.metrics[func_name] = []
                self.metrics[func_name].append(duration)
                
                # Log slow queries (>500ms)
                if duration > 0.5:
                    print(f"⚠️ SLOW: {func_name} took {duration:.2f}s")
                
                return result
            return wrapper
        return decorator
    
    def get_stats(self):
        """Get performance statistics"""
        stats = {}
        for func_name, durations in self.metrics.items():
            stats[func_name] = {
                'calls': len(durations),
                'avg_time': sum(durations) / len(durations),
                'max_time': max(durations),
                'min_time': min(durations),
                'total_time': sum(durations)
            }
        return stats


class CacheManager:
    """Simple in-memory cache with TTL"""
    
    def __init__(self, default_ttl: int = 300):
        self.cache = {}
        self.default_ttl = default_ttl  # seconds
    
    def get(self, key: str) -> Any:
        """Get cached value if not expired"""
        if key in self.cache:
            value, expiry = self.cache[key]
            if datetime.now() < expiry:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Set cache value with TTL"""
        if ttl is None:
            ttl = self.default_ttl
        expiry = datetime.now() + timedelta(seconds=ttl)
        self.cache[key] = (value, expiry)
    
    def delete(self, key: str):
        """Delete cache key"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Clear all cache"""
        self.cache = {}
    
    def cached(self, ttl: int = None):
        """Decorator for caching function results"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key from function name and args
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                
                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                return result
            return wrapper
        return decorator


# Global instances
perf_monitor = PerformanceMonitor()
cache_manager = CacheManager(default_ttl=300)  # 5 minute default


def optimize_query_joins():
    """
    Best practices for SQLAlchemy query optimization
    This is a reference guide, not executable code
    """
    tips = """
    # N+1 Query Prevention:
    
    1. Use joinedload() for one-to-many relationships:
       members = session.query(Member).options(joinedload(Member.fees)).all()
    
    2. Use subqueryload() for large collections:
       members = session.query(Member).options(subqueryload(Member.fees)).all()
    
    3. Batch operations instead of loops:
       # BAD:
       for member in members:
           gym.is_fee_paid(member.id, month)  # N queries
       
       # GOOD:
       paid_ids = get_paid_members_bulk(month)  # 1 query
       for member in members:
           is_paid = member.id in paid_ids
    
    4. Use select_in_loading for better performance:
       from sqlalchemy.orm import selectinload
       members = session.query(Member).options(selectinload(Member.fees)).all()
    
    5. Index frequently queried columns:
       # In models.py
       gym_id = Column(Integer, ForeignKey('gyms.id'), index=True)
       paid_date = Column(DateTime, index=True)
    """
    return tips
