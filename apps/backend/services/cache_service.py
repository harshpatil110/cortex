import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CacheService:
    """
    Minimal in-process TTL cache.

    Replaces the Redis-backed cache. Single-user local prototype means a single
    process, so an in-memory store is sufficient. The public API (get/set/delete)
    is unchanged so callers keep working.
    """

    def __init__(self):
        self._store: dict[str, tuple[float, Any]] = {}

    async def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at and time.time() > expires_at:
            self._store.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: Any, ttl: int = 300):
        self._store[key] = (time.time() + ttl, value)

    async def delete(self, key: str):
        self._store.pop(key, None)

    async def invalidate_memories(self, user_id: str):
        await self.delete(f"memories:{user_id}")

    async def invalidate_search(self, user_id: str):
        prefix = f"search:{user_id}:"
        for key in [k for k in self._store if k.startswith(prefix)]:
            self._store.pop(key, None)


cache_service = CacheService()
