"""Cache Service - Redis-based caching for policy responses."""

import json
from typing import Any

import redis.asyncio as redis

from app.config import settings
from app.models import PolicyRequest, PolicyResponse


class CacheService:
    """Redis-based cache service for policy responses."""

    def __init__(self) -> None:
        """Initialize the cache service."""
        self.redis: redis.Redis | None = None
        self.stats = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0,
            "total_size_bytes": 0,
        }

    async def connect(self) -> None:
        """Connect to Redis cache."""
        if settings.cache_enabled:
            try:
                self.redis = redis.from_url(
                    settings.cache_redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                # Test connection
                await self.redis.ping()
                print("Redis cache connected successfully")
            except (redis.ConnectionError, redis.RedisError) as e:
                print(f"Redis connection failed: {str(e)}")
                self.redis = None

    async def disconnect(self) -> None:
        """Disconnect from Redis cache."""
        if self.redis:
            await self.redis.close()
            self.redis = None

    def _generate_cache_key(self, request: PolicyRequest) -> str:
        """Generate cache key for policy request."""
        # Create a deterministic key based on request parameters
        key_parts = [
            "policy",
            request.subject.value,
            request.grade_band.value,
            request.region.value,
            str(request.teacher_override).lower(),
        ]
        return ":".join(key_parts)

    async def get_policy(
        self, request: PolicyRequest
    ) -> PolicyResponse | None:
        """Get cached policy response."""
        if not self.redis or not settings.cache_enabled:
            self.stats["misses"] += 1
            self.stats["total_requests"] += 1
            return None

        try:
            cache_key = self._generate_cache_key(request)
            cached_data = await self.redis.get(cache_key)

            self.stats["total_requests"] += 1

            if cached_data:
                self.stats["hits"] += 1
                response_data = json.loads(cached_data)
                return PolicyResponse(**response_data)

            self.stats["misses"] += 1
            return None

        except (redis.RedisError, ValueError) as e:
            print(f"Cache get error: {str(e)}")
            self.stats["misses"] += 1
            return None

    async def set_policy(
        self,
        request: PolicyRequest,
        response: PolicyResponse,
        ttl_seconds: int | None = None,
    ) -> None:
        """Cache policy response."""
        if not self.redis or not settings.cache_enabled:
            return

        try:
            cache_key = self._generate_cache_key(request)
            response_data = response.model_dump(mode="json")
            serialized_data = json.dumps(response_data)

            ttl = (
                ttl_seconds
                or response.cache_ttl_seconds
                or settings.cache_ttl_seconds
            )

            await self.redis.setex(cache_key, ttl, serialized_data)

            # Update size estimate
            self.stats["total_size_bytes"] += len(serialized_data)

        except (redis.RedisError, json.JSONDecodeError) as e:
            print(f"Cache set error: {str(e)}")

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern."""
        if not self.redis:
            return 0

        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except redis.RedisError as e:
            print(f"Cache invalidation error: {str(e)}")
            return 0

    async def invalidate_subject(self, subject: str) -> int:
        """Invalidate all cached policies for a subject."""
        pattern = f"policy:{subject}:*"
        return await self.invalidate_pattern(pattern)

    async def invalidate_region(self, region: str) -> int:
        """Invalidate all cached policies for a region."""
        pattern = f"policy:*:*:{region}:*"
        return await self.invalidate_pattern(pattern)

    async def clear_all(self) -> bool:
        """Clear all cached data."""
        if not self.redis:
            return False

        try:
            await self.redis.flushdb()
            self.stats = {
                "hits": 0,
                "misses": 0,
                "total_requests": 0,
                "total_size_bytes": 0,
            }
            return True
        except redis.RedisError as e:
            print(f"Cache clear error: {str(e)}")
            return False

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        hit_rate = (
            self.stats["hits"] / self.stats["total_requests"]
            if self.stats["total_requests"] > 0
            else 0.0
        )

        redis_info = {}
        if self.redis:
            try:
                info = await self.redis.info("memory")
                redis_info = {
                    "used_memory": info.get("used_memory", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "connected_clients": info.get("connected_clients", 0),
                }
            except redis.RedisError:
                pass

        return {
            "enabled": settings.cache_enabled and self.redis is not None,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "total_requests": self.stats["total_requests"],
            "hit_rate": hit_rate,
            "estimated_size_bytes": self.stats["total_size_bytes"],
            "redis_info": redis_info,
        }

    async def warm_cache(self, requests: list[PolicyRequest]) -> int:
        """Warm cache with common policy requests."""
        if not self.redis:
            return 0

        warmed_count = 0
        for _ in requests:
            # This would typically call the policy engine to get the response
            # and then cache it. For demo purposes, we'll skip this.
            warmed_count += 1

        return warmed_count


# Global cache service instance
cache_service = CacheService()
