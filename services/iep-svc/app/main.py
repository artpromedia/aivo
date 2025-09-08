"""
FastAPI application for IEP Service with Strawberry GraphQL.
"""

import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from strawberry.fastapi import GraphQLRouter

from .approval_service import approval_service
from .config import settings
from .resolvers import schema

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="IEP Service",
    description="IEP document management with GraphQL and dual approval workflow",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create GraphQL router
graphql_app = GraphQLRouter(
    schema,
    graphiql=settings.graphiql_enabled,
)

# Mount GraphQL
app.include_router(graphql_app, prefix=settings.graphql_path)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An internal error occurred"},
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "iep-svc",
        "version": "1.0.0",
        "graphql_endpoint": settings.graphql_path,
    }


@app.post("/webhooks/approval")
async def approval_webhook(request: Request):
    """
    Webhook endpoint for approval service notifications.
    """
    try:
        webhook_data = await request.json()
        logger.info(f"Received approval webhook: {webhook_data.get('event_type')}")

        # Process the webhook
        result = await approval_service.process_approval_webhook(webhook_data)

        if result["success"]:
            return {"status": "processed", "message": result.get("message", "Webhook processed")}
        else:
            logger.error(f"Webhook processing failed: {result.get('error')}")
            raise HTTPException(
                status_code=400, detail=result.get("error", "Webhook processing failed")
            )

    except Exception as e:
        logger.error(f"Error processing approval webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "IEP Service",
        "version": "1.0.0",
        "description": "IEP document management with GraphQL and dual approval workflow",
        "endpoints": {
            "graphql": settings.graphql_path,
            "graphiql": f"{settings.graphql_path}" if settings.graphiql_enabled else None,
            "health": "/health",
            "approval_webhook": "/webhooks/approval",
            "docs": "/docs",
        },
        "features": [
            "GraphQL API with Strawberry",
            "CRDT collaborative editing",
            "Dual approval workflow",
            "Event publishing",
            "Real-time synchronization",
        ],
    }


@app.get("/schema")
async def get_graphql_schema():
    """Get the GraphQL schema definition."""
    return {
        "schema": schema.as_str(),
        "endpoint": settings.graphql_path,
        "introspection": settings.graphiql_enabled,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
