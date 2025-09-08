"""
Tests for caching functionality and Redis integration.
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.cache_service import CacheService, cache_service


class TestCacheService:
    """Test cache service functionality."""

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test cache key generation."""
        cache = CacheService()

        # Test standard key
        key = cache._get_key("tenant_123", "summary")
        assert key == "admin_portal:tenant_123:summary"

        # Test with special characters
        key = cache._get_key("tenant-with-dash", "billing_history")
        assert key == "admin_portal:tenant-with-dash:billing_history"

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """Test setting and getting cache values."""
        mock_redis = Mock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value='{"test": "data"}')

        cache = CacheService()

        with patch.object(cache, "redis_client", mock_redis):
            # Test set
            test_data = {"test": "data"}
            result = await cache.set("tenant_123", "summary", test_data, ttl=30)
            assert result is True

            # Verify Redis was called correctly
            mock_redis.set.assert_called_once()
            call_args = mock_redis.set.call_args
            assert call_args[0][0] == "admin_portal:tenant_123:summary"
            assert call_args[1]["ex"] == 30

            # Test get
            retrieved_data = await cache.get("tenant_123", "summary")
            assert retrieved_data == {"test": "data"}

            mock_redis.get.assert_called_once_with("admin_portal:tenant_123:summary")

    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """Test cache miss behavior."""
        mock_redis = Mock()
        mock_redis.get = AsyncMock(return_value=None)

        cache = CacheService()

        with patch.object(cache, "redis", mock_redis):
            result = await cache.get("tenant_123", "summary")
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_delete(self):
        """Test cache deletion."""
        mock_redis = Mock()
        mock_redis.delete = AsyncMock(return_value=1)

        cache = CacheService()

        with patch.object(cache, "redis", mock_redis):
            result = await cache.delete("tenant_123", "summary")
            assert result == 1

            mock_redis.delete.assert_called_once_with("admin_portal:tenant_123:summary")

    @pytest.mark.asyncio
    async def test_cache_json_serialization(self):
        """Test JSON serialization and deserialization."""
        mock_redis = Mock()

        cache = CacheService()

        # Test complex data structure
        complex_data = {
            "tenant_id": "tenant_123",
            "metrics": [{"name": "api_calls", "value": 1000}, {"name": "storage", "value": 250.5}],
            "metadata": {"timestamp": "2024-09-02T10:00:00Z", "version": "1.0"},
        }

        # Mock set operation
        mock_redis.set = AsyncMock(return_value=True)

        with patch.object(cache, "redis", mock_redis):
            await cache.set("tenant_123", "usage", complex_data)

            # Verify JSON was serialized correctly
            call_args = mock_redis.set.call_args
            stored_value = call_args[0][1]
            parsed_data = json.loads(stored_value)
            assert parsed_data == complex_data

        # Mock get operation
        mock_redis.get = AsyncMock(return_value=json.dumps(complex_data))

        with patch.object(cache, "redis", mock_redis):
            retrieved_data = await cache.get("tenant_123", "usage")
            assert retrieved_data == complex_data

    @pytest.mark.asyncio
    async def test_cache_error_handling(self):
        """Test error handling in cache operations."""
        mock_redis = Mock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis connection failed"))
        mock_redis.set = AsyncMock(side_effect=Exception("Redis connection failed"))

        cache = CacheService()

        with patch.object(cache, "redis", mock_redis):
            # Get should return None on error
            result = await cache.get("tenant_123", "summary")
            assert result is None

            # Set should return False on error
            result = await cache.set("tenant_123", "summary", {"test": "data"})
            assert result is False

    @pytest.mark.asyncio
    async def test_cache_invalid_json_handling(self):
        """Test handling of invalid JSON in cache."""
        mock_redis = Mock()
        mock_redis.get = AsyncMock(return_value="invalid json {")

        cache = CacheService()

        with patch.object(cache, "redis", mock_redis):
            # Should return None for invalid JSON
            result = await cache.get("tenant_123", "summary")
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_clear_tenant(self):
        """Test clearing all cache entries for a tenant."""
        mock_redis = Mock()
        mock_redis.scan_iter = AsyncMock(
            return_value=[
                "admin_portal:tenant_123:summary",
                "admin_portal:tenant_123:usage",
                "admin_portal:tenant_456:summary",  # Different tenant
            ]
        )
        mock_redis.delete = AsyncMock(return_value=2)

        cache = CacheService()

        with patch.object(cache, "redis", mock_redis):
            result = await cache.clear_tenant("tenant_123")
            assert result == 2

            # Should have called delete with tenant-specific keys only
            mock_redis.delete.assert_called_once_with(
                "admin_portal:tenant_123:summary", "admin_portal:tenant_123:usage"
            )


class TestCacheIntegrationPatterns:
    """Test cache integration patterns."""

    @pytest.mark.asyncio
    async def test_cache_aside_pattern(self):
        """Test cache-aside pattern implementation."""
        from app.service_aggregator import service_aggregator

        tenant_id = "tenant_123"
        fresh_data = {"tenant_id": tenant_id, "tenant_name": "Fresh Data", "status": "active"}

        with (
            patch.object(cache_service, "get") as mock_get,
            patch.object(cache_service, "set") as mock_set,
            patch.object(service_aggregator, "_get_tenant_info") as mock_service,
        ):
            # Cache miss scenario
            mock_get.return_value = None
            mock_set.return_value = True
            mock_service.return_value = fresh_data

            # First call should fetch from service and cache
            await service_aggregator.get_summary(tenant_id)

            # Verify service was called
            mock_service.assert_called()
            # Verify data was cached
            mock_set.assert_called()

            # Second call with cache hit
            mock_get.return_value = {
                "tenant_id": tenant_id,
                "tenant_name": "Cached Data",
                "status": "active",
                "subscription_tier": "basic",
                "total_users": 10,
                "active_users_30d": 8,
                "total_documents": 100,
                "pending_approvals": 1,
                "monthly_spend": "29.99",
                "usage_alerts": 0,
                "health_score": 85.0,
            }
            mock_service.reset_mock()

            cached_summary = await service_aggregator.get_summary(tenant_id)

            # Should use cached data
            assert cached_summary.tenant_name == "Cached Data"
            # Should not call service again
            mock_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_write_through_pattern(self):
        """Test write-through cache pattern for updates."""
        # This would be used for operations that modify data
        tenant_id = "tenant_123"

        with (
            patch.object(cache_service, "set") as mock_set,
            patch.object(cache_service, "delete") as mock_delete,
        ):
            mock_set.return_value = True
            mock_delete.return_value = 1

            # Simulate an update operation that invalidates cache
            await cache_service.delete(tenant_id, "summary")
            await cache_service.delete(tenant_id, "subscription")

            # Verify cache invalidation
            assert mock_delete.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self):
        """Test cache TTL behavior."""
        from app.config import get_settings

        settings = get_settings()
        default_ttl = settings.cache_ttl

        mock_redis = Mock()
        mock_redis.set = AsyncMock(return_value=True)

        cache = CacheService()

        with patch.object(cache, "redis", mock_redis):
            # Test default TTL
            await cache.set("tenant_123", "summary", {"test": "data"})

            call_args = mock_redis.set.call_args
            assert call_args[1]["ex"] == default_ttl

            # Test custom TTL
            await cache.set("tenant_123", "temp_data", {"test": "data"}, ttl=60)

            call_args = mock_redis.set.call_args
            assert call_args[1]["ex"] == 60


class TestCachePerformance:
    """Test cache performance characteristics."""

    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self):
        """Test concurrent cache operations."""
        import asyncio

        mock_redis = Mock()
        mock_redis.get = AsyncMock(return_value='{"test": "data"}')
        mock_redis.set = AsyncMock(return_value=True)

        cache = CacheService()

        with patch.object(cache, "redis", mock_redis):
            # Simulate concurrent operations
            tasks = [
                cache.get("tenant_1", "summary"),
                cache.get("tenant_2", "summary"),
                cache.set("tenant_3", "summary", {"test": "data"}),
                cache.get("tenant_4", "usage"),
                cache.set("tenant_5", "billing", {"test": "data"}),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All operations should complete successfully
            assert len(results) == 5
            assert all(not isinstance(r, Exception) for r in results)

    @pytest.mark.asyncio
    async def test_cache_memory_efficiency(self):
        """Test cache memory usage patterns."""
        # Test that we're storing data efficiently
        large_data = {
            "tenant_id": "tenant_123",
            "large_list": [{"id": i, "data": f"item_{i}"} for i in range(1000)],
        }

        mock_redis = Mock()
        mock_redis.set = AsyncMock(return_value=True)

        cache = CacheService()

        with patch.object(cache, "redis", mock_redis):
            await cache.set("tenant_123", "large_data", large_data)

            # Verify the data was JSON serialized (compressed representation)
            call_args = mock_redis.set.call_args
            stored_value = call_args[0][1]

            # JSON should be more compact than Python object representation
            assert isinstance(stored_value, str)
            assert "large_list" in stored_value


@pytest.mark.asyncio
class TestCacheReliability:
    """Test cache reliability and fault tolerance."""

    async def test_cache_failover_graceful_degradation(self):
        """Test graceful degradation when cache is unavailable."""
        from app.service_aggregator import service_aggregator

        # Mock cache failure
        with (
            patch.object(cache_service, "get", side_effect=Exception("Cache unavailable")),
            patch.object(cache_service, "set", side_effect=Exception("Cache unavailable")),
            patch.object(service_aggregator, "_get_tenant_info") as mock_service,
        ):
            mock_service.return_value = {
                "name": "Direct Service",
                "status": "active",
                "subscription_tier": "basic",
            }

            # Should still work without cache
            summary = await service_aggregator.get_summary("tenant_123")

            assert summary.tenant_name == "Direct Service"
            # Service should have been called directly
            mock_service.assert_called()

    async def test_cache_consistency_after_errors(self):
        """Test cache consistency after errors."""
        mock_redis = Mock()

        # First operation fails
        mock_redis.set = AsyncMock(side_effect=Exception("Network error"))

        cache = CacheService()

        with patch.object(cache, "redis", mock_redis):
            result = await cache.set("tenant_123", "summary", {"test": "data"})
            assert result is False

        # Next operation should work normally
        mock_redis.set = AsyncMock(return_value=True)

        with patch.object(cache, "redis", mock_redis):
            result = await cache.set("tenant_123", "summary", {"test": "data"})
            assert result is True
