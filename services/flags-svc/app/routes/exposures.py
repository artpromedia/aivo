from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import structlog

from ..database import get_db
from ..schemas import ExposureEvent, ExposureResponse
from ..services.analytics_service import AnalyticsService

logger = structlog.get_logger()
router = APIRouter()

@router.post("/", response_model=ExposureResponse)
async def log_exposure(
    exposure: ExposureEvent,
    db: Session = Depends(get_db)
):
    """Log a flag exposure event for analytics"""
    analytics_service = AnalyticsService(db)

    try:
        await analytics_service.log_exposure(exposure)
        return ExposureResponse(success=True, message="Exposure logged successfully")
    except Exception as e:
        logger.error("exposure_logging_failed",
                    flag_key=exposure.flag_key,
                    user_id=exposure.user_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to log exposure")

@router.post("/batch", response_model=ExposureResponse)
async def log_exposures_batch(
    exposures: List[ExposureEvent],
    db: Session = Depends(get_db)
):
    """Log multiple flag exposure events for analytics"""
    analytics_service = AnalyticsService(db)

    try:
        await analytics_service.log_exposures_batch(exposures)
        return ExposureResponse(
            success=True,
            message=f"Batch of {len(exposures)} exposures logged successfully"
        )
    except Exception as e:
        logger.error("batch_exposure_logging_failed",
                    count=len(exposures),
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to log exposure batch")

@router.get("/analytics/{flag_key}")
async def get_flag_analytics(
    flag_key: str,
    period_days: int = 7,
    db: Session = Depends(get_db)
):
    """Get analytics data for a specific flag"""
    analytics_service = AnalyticsService(db)

    try:
        analytics = await analytics_service.get_flag_analytics(flag_key, period_days)
        return analytics
    except Exception as e:
        logger.error("flag_analytics_failed",
                    flag_key=flag_key,
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch flag analytics")

@router.get("/experiments/{experiment_id}/analytics")
async def get_experiment_analytics(
    experiment_id: str,
    period_days: int = 30,
    db: Session = Depends(get_db)
):
    """Get analytics data for a specific experiment"""
    analytics_service = AnalyticsService(db)

    try:
        analytics = await analytics_service.get_experiment_analytics(experiment_id, period_days)
        return analytics
    except Exception as e:
        logger.error("experiment_analytics_failed",
                    experiment_id=experiment_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch experiment analytics")
