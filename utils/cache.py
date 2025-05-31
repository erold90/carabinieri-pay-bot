# utils/cache.py
"""Simple in-memory cache"""
from datetime import datetime, timedelta
from functools import wraps

class SimpleCache:
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
    
    def get(self, key):
        """Get from cache if not expired"""
        if key in self.cache:
            timestamp = self.timestamps.get(key)
            if timestamp and datetime.now() - timestamp < timedelta(minutes=5):
                return self.cache[key]
            else:
                # Expired
                del self.cache[key]
                del self.timestamps[key]
        return None
    
    def set(self, key, value):
        """Set in cache"""
        self.cache[key] = value
        self.timestamps[key] = datetime.now()
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.timestamps.clear()

# Global cache instance
cache = SimpleCache()

def cached(ttl_minutes=5):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Calculate and cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        return wrapper
    return decorator
