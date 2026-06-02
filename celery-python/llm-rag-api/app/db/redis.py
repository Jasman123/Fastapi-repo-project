from functools import lru_cache
import redis as redis_lib
from app.core.config import get_settings


@lru_cache
def get_redis_client() -> redis_lib.Redis:
    settings = get_settings()
    return redis_lib.from_url(
        settings.redis_url,
        decode_responses=True,
    )

class CacheRepository:

    def __init__(self, prefix: str ="cache"):
        self._redis = get_redis_client()
        self._prefix = prefix

    def _key(self, key: str) ->str:
        return f"{self._prefix}:{key}"
    
    def get(self, key: str) -> str | None:
        return self._redis.get(self._key(key))
    
    def set(self, key: str, value: str, ttl_seconds: int = 3600) -> None:
        self._redis.setex(self._key(key), ttl_seconds, value)

    def exist(self, key: str) -> bool:
        return bool(self._redis.exists(self._key(key)))
    
    def delete(self, key: str) -> None:
        self._redis.delete(self._key(key))

    def increment(self, key: str) -> int:
        return self._redis.incr(self._key(key))
    
    def set_expiry(self, key:str, ttl_seconds: int) -> None:
        self._redis.expire(self._key(key), ttl_seconds)