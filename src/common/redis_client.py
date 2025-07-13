"""Redis service for managing chat history and user data."""

import json
import os
from typing import Any
from typing import Optional

import redis.asyncio as redis


class RedisService:
    """Service for managing Redis operations."""

    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        """Establish Redis connection."""
        try:
            if self.redis_client:
                return
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
        except Exception as e:
            raise

    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.aclose()

    async def set(self, key: str, value: Any, expire: Optional[int] = None):
        """Set a key-value pair in Redis, storing JSON-encoded data."""
        value_to_store = json.dumps(value, ensure_ascii=False)
        await self.redis_client.set(key, value_to_store, ex=expire)

    async def get(self, key: str) -> Optional[Any]:
        """Get and deserialize a value from Redis."""
        raw_value = await self.redis_client.get(key)
        if raw_value is None:
            return None

        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            return raw_value  # fallback to raw string

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a value in Redis by key."""
        return await self.redis_client.incrby(key, amount)

    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement a value in Redis by key."""
        return await self.redis_client.decrby(key, amount)

    async def set_game_start_timestamp(self, user_id: int, timestamp: int):
        key = f"game_start_timestamp:{user_id}"
        await self.redis_client.set(key, timestamp)

    async def get_game_start_timestamp(self, user_id: int):
        key = f"game_start_timestamp:{user_id}"
        return float(await self.redis_client.get(key))

    async def keys(self, pattern: str):
        return await self.redis_client.keys(pattern)
    
    async def delete(self, key: str):
        return await self.redis_client.delete(key)


redis_client = RedisService()
