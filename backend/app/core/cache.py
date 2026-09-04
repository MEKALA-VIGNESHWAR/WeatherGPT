import time
import json
from typing import Optional, Any
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("cache")

# In-memory fallback cache
_memory_cache = {}


class CacheService:
    def __init__(self):
        self.redis_client = None
        if settings.REDIS_URL:
            try:
                import redis
                self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                self.redis_client.ping()
                logger.info("Connected to Redis cache successfully.")
            except Exception as e:
                logger.warning(f"Redis unavailable ({e}). Using robust In-Memory Cache.")
                self.redis_client = None
        else:
            logger.info("No REDIS_URL configured. Using fast In-Memory Cache.")

    def get(self, key: str) -> Optional[Any]:
        if self.redis_client:
            try:
                val = self.redis_client.get(key)
                return json.loads(val) if val else None
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        
        # In-memory check
        entry = _memory_cache.get(key)
        if entry:
            val, expiry = entry
            if expiry is None or time.time() < expiry:
                return val
            else:
                del _memory_cache[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 600) -> bool:
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl_seconds, json.dumps(value, default=str))
                return True
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
        
        # In-memory set
        expiry = time.time() + ttl_seconds if ttl_seconds > 0 else None
        _memory_cache[key] = (value, expiry)
        return True

    def delete(self, key: str) -> bool:
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception:
                pass
        if key in _memory_cache:
            del _memory_cache[key]
        return True


cache_service = CacheService()
