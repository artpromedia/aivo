"""
Cache service for Admin Portal Aggregator with Redis backend.
"""
import json
import logging
from typing import Any, Optional
from datetime import timedelta
import redis.asyncio as redis

from .config import get_settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based cache service with tenant isolation."""
    
    def __init__(self):
        """Initialize cache service."""
        self.settings = get_settings()
        self.redis_client: Optional[redis.Redis] = None
        self.enabled = self.settings.cache_enabled
        
    async def initialize(self):
        """Initialize Redis connection."""
        if not self.enabled:
            logger.info("Cache is disabled")
            return
            
        try:
            self.redis_client = redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Cache service connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.enabled = False
            self.redis_client = None
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
    
    def _get_key(self, tenant_id: str, endpoint: str) -> str:
        """Generate cache key with tenant isolation."""
        return f"admin_portal:{tenant_id}:{endpoint}"
    
    async def get(self, tenant_id: str, endpoint: str) -> Optional[Any]:
        """Get cached data for tenant and endpoint."""
        if not self.enabled or not self.redis_client:
            return None
            
        try:
            key = self._get_key(tenant_id, endpoint)
            cached_data = await self.redis_client.get(key)
            
            if cached_data:
                logger.debug(f"Cache hit for {key}")
                return json.loads(cached_data)
            else:
                logger.debug(f"Cache miss for {key}")
                return None
                
        except Exception as e:
            logger.error(f"Cache get error for {tenant_id}:{endpoint}: {e}")
            return None
    
    async def set(self, tenant_id: str, endpoint: str, data: Any, ttl: Optional[int] = None) -> bool:
        """Set cached data for tenant and endpoint."""
        if not self.enabled or not self.redis_client:
            return False
            
        try:
            key = self._get_key(tenant_id, endpoint)
            ttl = ttl or self.settings.cache_ttl
            
            serialized_data = json.dumps(data, default=str)
            await self.redis_client.setex(key, ttl, serialized_data)
            
            logger.debug(f"Cache set for {key} with TTL {ttl}s")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for {tenant_id}:{endpoint}: {e}")
            return False
    
    async def delete(self, tenant_id: str, endpoint: str) -> bool:
        """Delete cached data for tenant and endpoint."""
        if not self.enabled or not self.redis_client:
            return False
            
        try:
            key = self._get_key(tenant_id, endpoint)
            result = await self.redis_client.delete(key)
            
            logger.debug(f"Cache delete for {key}: {'success' if result else 'not found'}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache delete error for {tenant_id}:{endpoint}: {e}")
            return False
    
    async def clear_tenant(self, tenant_id: str) -> int:
        """Clear all cached data for a tenant."""
        if not self.enabled or not self.redis_client:
            return 0
            
        try:
            pattern = f"admin_portal:{tenant_id}:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} cache entries for tenant {tenant_id}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache clear error for tenant {tenant_id}: {e}")
            return 0
    
    async def get_stats(self) -> dict:
        """Get cache statistics."""
        if not self.enabled or not self.redis_client:
            return {"status": "disabled"}
            
        try:
            info = await self.redis_client.info()
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"status": "error", "error": str(e)}


# Global cache service instance
cache_service = CacheService()
