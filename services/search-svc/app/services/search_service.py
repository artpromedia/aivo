"""Main search service that orchestrates all search functionality."""

import json
import logging
from typing import Any

import redis.asyncio as redis

from app.config import settings
from app.models import (
    BulkIndexRequest,
    HealthStatus,
    IndexRequest,
    SearchRequest,
    SearchResponse,
    SuggestionRequest,
    SuggestionResponse,
    UserContext,
)
from app.services.opensearch_service import OpenSearchService
from app.services.pii_masking_service import PIIMaskingService
from app.services.rbac_service import RBACService

logger = logging.getLogger(__name__)


class SearchService:
    """Main search service that orchestrates search operations."""

    def __init__(self) -> None:
        """Initialize the search service."""
        self.opensearch_service = OpenSearchService()
        self.rbac_service = RBACService()
        self.pii_masking_service = PIIMaskingService()
        self.redis_client = None
        logger.info("SearchService initialized")

    async def initialize(self) -> None:
        """Initialize all service dependencies."""
        try:
            # pylint: disable=no-member
            await self.opensearch_service.initialize()
            if settings.REDIS_URL:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL, encoding="utf-8", decode_responses=True
                )
            logger.info("SearchService dependencies initialized successfully")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to initialize SearchService: %s", str(e))
            raise

    async def health_check(self) -> HealthStatus:
        """Perform health check on all dependencies."""
        try:
            # Check OpenSearch health
            # pylint: disable=no-member
            opensearch_health = await self.opensearch_service.health_check()

            # Check Redis health if configured
            redis_healthy = True
            if self.redis_client:
                try:
                    await self.redis_client.ping()
                except (
                    Exception
                ) as e:  # pylint: disable=broad-exception-caught  # noqa: E501
                    logger.warning("Redis health check failed: %s", str(e))
                    redis_healthy = False

            overall_status = (
                "healthy"
                if opensearch_health.status == "healthy" and redis_healthy
                else "unhealthy"
            )

            return HealthStatus(
                status=overall_status,
                details={
                    "opensearch": opensearch_health.details,
                    "redis": "healthy" if redis_healthy else "unhealthy",
                },
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Health check failed: %s", str(e))
            return HealthStatus(status="unhealthy", details={"error": str(e)})

    async def search(
        self,
        request: SearchRequest,
        user_context: UserContext
    ) -> SearchResponse:
        """Perform search with RBAC filtering and PII masking."""
        try:
            # Check cache first
            cache_key = None
            if self.redis_client:
                cache_key = self._generate_cache_key(request, user_context)
                cached_result = await self._get_cached_result(cache_key)
                if cached_result:
                    logger.debug("Cache hit for user %s", user_context.user_id)
                    return SearchResponse(**cached_result)

            # Apply RBAC filtering
            # pylint: disable=no-member
            filtered_request = await self.rbac_service.filter_search_request(
                request,
                user_context
            )

            # Perform search
            # pylint: disable=no-member
            search_response = await self.opensearch_service.search(
                filtered_request
            )

            # Apply PII masking
            # pylint: disable=no-member
            masked_response = await self.pii_masking_service.mask_response(
                search_response, user_context
            )

            # Cache the result
            if self.redis_client and cache_key:
                await self._cache_result(cache_key, masked_response)

            logger.debug(
                "Search completed: %d results for user %s",
                len(masked_response.hits),
                user_context.user_id,
            )
            return masked_response

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Search failed for user %s: %s",
                user_context.user_id,
                str(e),
            )
            raise

    async def suggest(
        self,
        request: SuggestionRequest,
        user_context: UserContext
    ) -> SuggestionResponse:
        """Get search suggestions with RBAC filtering."""
        try:
            # Apply RBAC filtering to suggestion request
            # pylint: disable=no-member
            filtered_request = (
                await self.rbac_service.filter_suggestion_request(
                    request,
                    user_context
                )
            )

            # Get suggestions from OpenSearch
            # pylint: disable=no-member
            suggestions = await self.opensearch_service.suggest(
                filtered_request
            )

            logger.debug(
                "Suggestions generated for user %s: %d suggestions",
                user_context.user_id,
                len(suggestions.suggestions),
            )
            return suggestions

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Suggestion generation failed for user %s: %s",
                user_context.user_id,
                str(e),
            )
            raise

    async def index_document(
        self,
        request: IndexRequest,
        user_context: UserContext
    ) -> dict[str, Any]:
        """Index a single document with authorization checks."""
        try:
            # Check user permissions for indexing
            # pylint: disable=no-member
            if not await self.rbac_service.can_index(user_context):
                raise PermissionError(
                    "User does not have permission to index documents"
                )

            # Apply PII masking before indexing
            # pylint: disable=no-member
            masked_document = await self.pii_masking_service.mask_document(
                request.document, user_context
            )

            # Create masked request
            masked_request = IndexRequest(
                index=request.index,
                document=masked_document,
                document_id=request.document_id,
            )

            # Index the document
            # pylint: disable=no-member
            result = await self.opensearch_service.index_document(
                masked_request
            )

            # Invalidate relevant caches
            if self.redis_client:
                await self._invalidate_search_cache()

            logger.info(
                "Document indexed successfully for user %s: %s",
                user_context.user_id,
                result.get("_id", "unknown"),
            )
            return result

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Document indexing failed for user %s: %s",
                user_context.user_id,
                str(e),
            )
            raise

    async def bulk_index(
        self,
        request: BulkIndexRequest,
        user_context: UserContext
    ) -> dict[str, Any]:
        """Bulk index documents with authorization checks."""
        try:
            # Check user permissions for bulk indexing
            # pylint: disable=no-member
            if not await self.rbac_service.can_bulk_index(user_context):
                raise PermissionError(
                    "User does not have permission to bulk index documents"
                )

            # Apply PII masking to all documents
            masked_documents = []
            for doc in request.documents:
                # pylint: disable=no-member
                masked_doc = await self.pii_masking_service.mask_document(
                    doc, user_context
                )
                masked_documents.append(masked_doc)

            # Create masked request
            masked_request = BulkIndexRequest(
                index=request.index, documents=masked_documents
            )

            # Bulk index the documents
            # pylint: disable=no-member
            result = await self.opensearch_service.bulk_index(masked_request)

            # Invalidate relevant caches
            if self.redis_client:
                await self._invalidate_search_cache()

            logger.info(
                "Bulk indexing completed for user %s: %d documents",
                user_context.user_id,
                len(request.documents),
            )
            return result

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Bulk indexing failed for user %s: %s",
                user_context.user_id,
                str(e),
            )
            raise

    def _generate_cache_key(
        self, request: SearchRequest, user_context: UserContext
    ) -> str:
        """Generate a cache key for the search request."""
        key_data = {
            "query": request.query,
            "filters": request.filters,
            "user_id": user_context.user_id,
            "user_roles": sorted(user_context.roles),
        }
        return f"search:{hash(str(sorted(key_data.items())))}"

    async def _get_cached_result(self, cache_key: str) -> dict | None:
        """Get cached search result."""
        try:
            if not self.redis_client:
                return None

            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("Failed to get cached result: %s", str(e))
            return None

    async def _cache_result(
        self, cache_key: str, result: SearchResponse
    ) -> None:
        """Cache search result."""
        try:
            if not self.redis_client:
                return

            # Convert to dict for caching
            result_dict = result.dict()
            await self.redis_client.setex(
                cache_key, settings.CACHE_TTL_SECONDS, json.dumps(result_dict)
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("Failed to cache result: %s", str(e))

    async def _invalidate_search_cache(self) -> None:
        """Invalidate all search cache entries."""
        try:
            if not self.redis_client:
                return

            # Find all search cache keys
            keys = await self.redis_client.keys("search:*")
            if keys:
                await self.redis_client.delete(*keys)
                logger.debug("Invalidated %d search cache entries", len(keys))
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("Failed to invalidate search cache: %s", str(e))

    async def close(self) -> None:
        """Close all service connections."""
        try:
            await self.opensearch_service.close()  # pylint: disable=no-member
            if self.redis_client:
                await self.redis_client.close()
            logger.info("SearchService connections closed")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error closing SearchService connections: %s", str(e))
