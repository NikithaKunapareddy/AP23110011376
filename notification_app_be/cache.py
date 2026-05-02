"""
Redis Cache Layer
Performance optimization using Redis caching
"""

import redis
import json
from typing import Optional, Dict, Any
from datetime import timedelta

class CacheManager:
    """Manages Redis caching for notification queries"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = True
        except Exception:
            # Redis not available, disable caching
            self.redis_client = None
            self.enabled = False
    
    def get(self, key: str) -> Optional[Dict]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception:
            pass
        
        return None
    
    def set(self, key: str, value: Dict, ttl_seconds: int = 300):
        """Set value in cache with TTL (5 min default)"""
        if not self.enabled:
            return
        
        try:
            self.redis_client.setex(
                key,
                ttl_seconds,
                json.dumps(value)
            )
        except Exception:
            pass
    
    def delete(self, key: str):
        """Delete from cache"""
        if not self.enabled:
            return
        
        try:
            self.redis_client.delete(key)
        except Exception:
            pass
    
    def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        if not self.enabled:
            return
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except Exception:
            pass

# Initialize cache manager
cache = CacheManager()

# Cache key builders
def get_notifications_cache_key(student_id: str, page: int, limit: int) -> str:
    """Generate cache key for notifications query"""
    return f"notifications:{student_id}:page:{page}:limit:{limit}"

def get_unread_count_cache_key(student_id: str) -> str:
    """Generate cache key for unread count"""
    return f"unread_count:{student_id}"

def get_priority_inbox_cache_key(student_id: str, n: int) -> str:
    """Generate cache key for priority inbox"""
    return f"priority_inbox:{student_id}:top:{n}"

def invalidate_student_cache(student_id: str):
    """Invalidate all cached data for a student"""
    cache.clear_pattern(f"notifications:{student_id}:*")
    cache.clear_pattern(f"unread_count:{student_id}*")
    cache.clear_pattern(f"priority_inbox:{student_id}:*")
