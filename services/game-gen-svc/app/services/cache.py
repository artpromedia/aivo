"""Template cache service for game generation."""

import asyncio
import json
import time
from typing import Any

import redis.asyncio as redis
from redis.asyncio import Redis

from app.config import settings
from app.models import CacheStats, GameManifest


class TemplateCache:
    """High-performance template cache for sub-second game generation."""

    def __init__(self) -> None:
        """Initialize template cache."""
        self.redis: Redis | None = None
        self.local_cache: dict[str, dict[str, Any]] = {}
        self.cache_stats = {
            "hits": 0, "misses": 0, "size_bytes": 0, "num_entries": 0
        }
        self._cache_lock = asyncio.Lock()

    async def connect(self) -> None:
        """Connect to Redis cache."""
        if settings.cache_enabled:
            try:
                self.redis = redis.from_url(
                    settings.cache_redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
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

    def _generate_cache_key(
        self,
        subject: str,
        grade: int,
        game_type: str,
        duration_minutes: int,
        accessibility_hash: str,
    ) -> str:
        """Generate cache key for game manifest."""
        return (
            f"manifest:{subject}:{grade}:{game_type}:"
            f"{duration_minutes}:{accessibility_hash}"
        )

    def _calculate_accessibility_hash(
        self, accessibility: dict[str, Any]
    ) -> str:
        """Calculate hash for accessibility settings."""
        # Sort keys for consistent hashing
        sorted_settings = sorted(accessibility.items())
        settings_str = json.dumps(sorted_settings, sort_keys=True)
        return str(hash(settings_str))

    async def get_manifest(
        self,
        subject: str,
        grade: int,
        game_type: str,
        duration_minutes: int,
        accessibility: dict[str, Any],
    ) -> GameManifest | None:
        """Get cached game manifest."""
        a11y_hash = self._calculate_accessibility_hash(accessibility)
        cache_key = self._generate_cache_key(
            subject, grade, game_type, duration_minutes, a11y_hash
        )

        async with self._cache_lock:
            # Try local cache first (fastest)
            if cache_key in self.local_cache:
                self.cache_stats["hits"] += 1
                manifest_data = self.local_cache[cache_key]
                return GameManifest(**manifest_data["manifest"])

            # Try Redis cache
            if self.redis:
                try:
                    cached_data = await self.redis.get(cache_key)
                    if cached_data:
                        self.cache_stats["hits"] += 1
                        manifest_data = json.loads(cached_data)

                        # Update local cache
                        self.local_cache[cache_key] = manifest_data

                        return GameManifest(**manifest_data["manifest"])
                except (redis.ConnectionError, redis.RedisError) as e:
                    print(f"Redis get error: {str(e)}")

            # Cache miss
            self.cache_stats["misses"] += 1
            return None

    async def store_manifest(
        self,
        subject: str,
        grade: int,
        game_type: str,
        duration_minutes: int,
        accessibility: dict[str, Any],
        manifest: GameManifest,
    ) -> None:
        """Store game manifest in cache."""
        a11y_hash = self._calculate_accessibility_hash(accessibility)
        cache_key = self._generate_cache_key(
            subject, grade, game_type, duration_minutes, a11y_hash
        )

        manifest_data = {
            "manifest": manifest.model_dump(),
            "created_at": time.time(),
            "subject": subject,
            "grade": grade,
            "game_type": game_type,
            "duration_minutes": duration_minutes,
        }

        # Check size limits
        data_size = len(json.dumps(manifest_data))
        if data_size > settings.cache_max_manifest_size_kb * 1024:
            print(f"Manifest too large for cache: {data_size} bytes")
            return

        async with self._cache_lock:
            # Store in local cache
            self.local_cache[cache_key] = manifest_data

            # Store in Redis cache
            if self.redis:
                try:
                    await self.redis.setex(
                        cache_key,
                        settings.cache_default_ttl_seconds,
                        json.dumps(manifest_data)
                    )
                except (redis.ConnectionError, redis.RedisError) as e:
                    print(f"Redis set error: {str(e)}")

            # Update stats
            self.cache_stats["size_bytes"] += data_size
            self.cache_stats["num_entries"] += 1

    async def get_template_variants(
        self, subject: str, grade: int
    ) -> list[dict[str, Any]]:
        """Get all cached template variants for subject/grade."""
        pattern = f"manifest:{subject}:{grade}:*"
        variants = []

        if self.redis:
            try:
                keys = await self.redis.keys(pattern)
                for key in keys:
                    cached_data = await self.redis.get(key)
                    if cached_data:
                        variant_data = json.loads(cached_data)
                        variants.append(
                            {
                                "cache_key": key,
                                "game_type": variant_data.get("game_type"),
                                "duration_minutes": variant_data.get(
                                    "duration_minutes"
                                ),
                                "created_at": variant_data.get("created_at"),
                            }
                        )
            except (redis.ConnectionError, redis.RedisError) as e:
                print(f"Redis keys error: {str(e)}")

        return variants

    async def warm_cache(self, subject: str, grade: int) -> None:
        """Pre-warm cache with common game variants."""
        # Get available game types for subject
        game_types = getattr(settings, f"{subject}_game_types", [])
        common_durations = [5, 10, 15, 20]

        # Pre-generate common accessibility combinations
        accessibility_variants = [
            {},  # Default
            {"reduced_motion": True},
            {"high_contrast": True},
            {"large_text": True},
            {"audio_cues": False},
            {"reduced_motion": True, "high_contrast": True},
        ]

        tasks = []
        for game_type in game_types:
            for duration in common_durations:
                for accessibility in accessibility_variants:
                    # Check if already cached
                    manifest = await self.get_manifest(
                        subject, grade, game_type, duration, accessibility
                    )
                    if not manifest:
                        # Would trigger generation in real implementation
                        # For now, create placeholder
                        tasks.append((
                            subject, grade, game_type, duration, accessibility
                        ))

        print(f"Cache warming identified {len(tasks)} variants to generate")

    async def clear_expired(self) -> int:
        """Clear expired entries from local cache."""
        expired_count = 0
        current_time = time.time()

        async with self._cache_lock:
            expired_keys = []
            for key, data in self.local_cache.items():
                cache_age = current_time - data.get("created_at", 0)
                if cache_age > settings.cache_default_ttl_seconds:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.local_cache[key]
                expired_count += 1
                self.cache_stats["num_entries"] -= 1

        return expired_count

    def get_cache_stats(self) -> CacheStats:
        """Get current cache statistics."""
        hit_rate = 0.0
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        if total_requests > 0:
            hit_rate = self.cache_stats["hits"] / total_requests

        return CacheStats(
            hit_count=self.cache_stats["hits"],
            miss_count=self.cache_stats["misses"],
            hit_rate=hit_rate,
            size_bytes=self.cache_stats["size_bytes"],
            num_entries=self.cache_stats["num_entries"],
            redis_connected=self.redis is not None,
        )


# Global cache instance
template_cache = TemplateCache()
