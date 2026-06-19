import json
import logging
import os
from typing import Any, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> Optional[Any]:
        try:
            val = await self.redis.get(key)
            if val:
                return json.loads(val)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        try:
            await self.redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    async def delete(self, key: str):
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")

    async def invalidate_memories(self, user_id: str):
        key = f"memories:{user_id}"
        await self.delete(key)


cache_service = CacheService()
