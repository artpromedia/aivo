from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import structlog
from typing import Optional, Dict, Any
import hashlib
import time

from .database import get_db, engine
from .models import Base
from .routes import flags, evaluate, exposures
from .services.analytics_service import AnalyticsService

# Create all tables
Base.metadata.create_all(bind=engine)

logger = structlog.get_logger()

app = FastAPI(
    title="Feature Flags Service",
    description="Tenant-scoped feature flags with rollout control and experiment tracking",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(flags.router, prefix="/api/v1/flags", tags=["flags"])
app.include_router(evaluate.router, prefix="/api/v1", tags=["evaluation"])
app.include_router(exposures.router, prefix="/api/v1/exposures", tags=["exposures"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "flags-svc"}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(
        "request_processed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time
    )

    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
