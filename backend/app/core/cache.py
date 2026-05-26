import logging
from redis.asyncio import Redis, from_url
from redis.exceptions import RedisError

logger = logging.getLogger("cache")

class CacheService:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis = None

    async def connect(self):
        """Initialize async Redis connection"""
        try:
            self.redis = from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
        except Exception as e:
            logger.warning(f"Failed to connect to Redis at {self.redis_url}: {e}. Caching will be disabled.")
            self.redis = None

    async def get(self, key: str) -> str | None:
        """Get cached value by key"""
        if not self.redis:
            return None
        try:
            return await self.redis.get(key)
        except RedisError as e:
            logger.warning(f"Redis error on get: {e}")
            return None

    async def set(self, key: str, value: str, ttl: int = 86400) -> None:
        """Set cached value with TTL (default 24 hours)"""
        if not self.redis:
            return
        try:
            await self.redis.set(key, value, ex=ttl)
        except RedisError as e:
            logger.warning(f"Redis error on set: {e}")

    async def delete(self, key: str) -> None:
        """Delete cached value"""
        if not self.redis:
            return
        try:
            await self.redis.delete(key)
        except RedisError as e:
            logger.warning(f"Redis error on delete: {e}")

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis:
            return False
        try:
            return bool(await self.redis.exists(key))
        except RedisError as e:
            logger.warning(f"Redis error on exists: {e}")
            return False

    @staticmethod
    def make_pain_point_key(industry: str, location: str, maturity: str) -> str:
        """Generate consistent cache key: 'pain_points:{industry}:{location}:{maturity}'"""
        ind_norm = " ".join(industry.strip().lower().split())
        loc_norm = " ".join(location.strip().lower().split())
        mat_norm = " ".join(maturity.strip().lower().split())
        return f"pain_points:{ind_norm}:{loc_norm}:{mat_norm}"

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            try:
                await self.redis.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
            finally:
                self.redis = None
