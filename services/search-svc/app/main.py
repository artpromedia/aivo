"""FastAPI application for search service."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import (
    BulkIndexRequest,
    HealthStatus,
    IndexRequest,
    SearchRequest,
    SearchResponse,
    SearchScope,
    SuggestionRequest,
    SuggestionResponse,
    UserContext,
    UserRole,
)
from app.services import SearchService

# Configure logging
logging.basicConfig(
    level=getattr(logging, str(settings.log_level).upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global search service instance
search_service: SearchService | None = None


@asynccontextmanager
async def lifespan(
    _app: FastAPI,  # noqa: ARG001
) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    global search_service  # pylint: disable=global-statement

    # Startup
    logger.info("Starting search service application...")
    search_service = SearchService()
    await search_service.startup()  # pylint: disable=no-member

    yield

    # Shutdown
    logger.info("Shutting down search service application...")
    if search_service:
        await search_service.shutdown()  # pylint: disable=no-member


# Create FastAPI application
app = FastAPI(
    title="Search Service",
    description=(
        "Unified search service with OpenSearch, RBAC, and PII masking"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_search_service() -> SearchService:
    """Get search service dependency."""
    if search_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search service not initialized"
        )
    return search_service


async def get_user_context(
    # In a real application, these would come from JWT token or session
    user_id: str = Query(..., description="User ID"),
    role: UserRole = Query(..., description="User role"),
    district_id: str | None = Query(None, description="District ID"),
    school_id: str | None = Query(None, description="School ID"),
    class_ids: str = Query("", description="Comma-separated class IDs"),
    learner_ids: str = Query("", description="Comma-separated learner IDs"),
) -> UserContext:
    """Get user context from request parameters."""
    return UserContext(
        user_id=user_id,
        role=role,
        district_id=district_id,
        school_id=school_id,
        class_ids=[id.strip() for id in class_ids.split(",") if id.strip()],
        learner_ids=[
            id.strip() for id in learner_ids.split(",") if id.strip()
        ],
    )


@app.get("/health", response_model=HealthStatus)
async def health_check(
    service: SearchService = Depends(get_search_service),
) -> HealthStatus:
    """Health check endpoint."""
    try:
        return await service.get_health()
    except Exception as e:
        logger.error("Health check failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health check failed"
        ) from e


@app.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="Search query", min_length=1),
    scope: SearchScope = Query(SearchScope.ALL, description="Search scope"),
    size: int = Query(20, description="Number of results", ge=1, le=100),
    from_: int = Query(
        0, description="Offset for pagination", ge=0, alias="from"
    ),
    service: SearchService = Depends(get_search_service),
    user_context: UserContext = Depends(get_user_context),
) -> SearchResponse:
    """Search endpoint with RBAC filtering and PII masking."""
    try:
        request = SearchRequest(
            q=q,
            scope=scope,
            size=size,
            from_=from_,
        )

        result = await service.search(request, user_context)
        logger.info(
            "Search request completed: %d results for query '%s' by user %s",
            len(result.hits),
            q,
            user_context.user_id
        )
        return result

    except Exception as e:
        logger.error("Search request failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        ) from e


@app.get("/suggest", response_model=SuggestionResponse)
async def suggest(
    q: str = Query(..., description="Query for suggestions", min_length=1),
    size: int = Query(5, description="Number of suggestions", ge=1, le=10),
    scope: SearchScope = Query(
        SearchScope.ALL, description="Suggestion scope"
    ),
    service: SearchService = Depends(get_search_service),
    user_context: UserContext = Depends(get_user_context),
) -> SuggestionResponse:
    """Suggestion endpoint."""
    try:
        request = SuggestionRequest(
            q=q,
            size=size,
            scope=scope,
        )

        result = await service.suggest(request, user_context)
        logger.debug(
            "Suggestion request completed: %d suggestions for query '%s' "
            "by user %s",
            len(result.suggestions),
            q,
            user_context.user_id
        )
        return result

    except Exception as e:
        logger.error("Suggestion request failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Suggestions failed: {str(e)}"
        ) from e


@app.post("/index", response_model=dict[str, Any])
async def index_document(
    request: IndexRequest,
    service: SearchService = Depends(get_search_service),
    user_context: UserContext = Depends(get_user_context),
) -> dict[str, Any]:
    """Index a single document."""
    try:
        # Check if user has permission to index documents
        admin_roles = [UserRole.SYSTEM_ADMIN, UserRole.DISTRICT_ADMIN]
        if user_context.role not in admin_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to index documents"
            )

        result = await service.index_document(request, user_context)
        logger.info("Document indexed: %s", request.document.id)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Index request failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Indexing failed: " + str(e)
        ) from e


@app.post("/bulk-index", response_model=dict[str, Any])
async def bulk_index_documents(
    request: BulkIndexRequest,
    service: SearchService = Depends(get_search_service),
    user_context: UserContext = Depends(get_user_context),
) -> dict[str, Any]:
    """Bulk index multiple documents."""
    try:
        # Check if user has permission to index documents
        admin_roles = [UserRole.SYSTEM_ADMIN, UserRole.DISTRICT_ADMIN]
        if user_context.role not in admin_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to index documents"
            )

        result = await service.bulk_index_documents(request, user_context)
        logger.info("Bulk indexed %d documents", len(request.documents))
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Bulk index request failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk indexing failed: " + str(e)
        ) from e


@app.exception_handler(Exception)
async def global_exception_handler(
    _request: object,  # noqa: ARG001
    exc: Exception,
) -> JSONResponse:
    """Global exception handler."""
    logger.error("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=bool(settings.debug),
        log_level=str(settings.log_level).lower(),
    )
