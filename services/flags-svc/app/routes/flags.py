from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import structlog

from ..database import get_db
from ..models import FeatureFlag, Experiment
from ..schemas import (
    FeatureFlagCreate, FeatureFlagUpdate, FeatureFlagResponse,
    ExperimentCreate, ExperimentUpdate, ExperimentResponse
)
from ..services.flag_service import FlagService

logger = structlog.get_logger()
router = APIRouter()

@router.get("/", response_model=List[FeatureFlagResponse])
async def list_flags(
    tenant_id: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    is_experiment: Optional[bool] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List feature flags with optional filtering"""
    query = db.query(FeatureFlag)

    if tenant_id is not None:
        query = query.filter(FeatureFlag.tenant_id == tenant_id)

    if enabled is not None:
        query = query.filter(FeatureFlag.enabled == enabled)

    if is_experiment is not None:
        query = query.filter(FeatureFlag.is_experiment == is_experiment)

    flags = query.offset(offset).limit(limit).all()
    return flags

@router.get("/{flag_key}", response_model=FeatureFlagResponse)
async def get_flag(flag_key: str, db: Session = Depends(get_db)):
    """Get a specific feature flag by key"""
    flag = db.query(FeatureFlag).filter(FeatureFlag.key == flag_key).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return flag

@router.post("/", response_model=FeatureFlagResponse)
async def create_flag(
    flag_data: FeatureFlagCreate,
    db: Session = Depends(get_db)
):
    """Create a new feature flag"""
    # Check if flag key already exists
    existing = db.query(FeatureFlag).filter(FeatureFlag.key == flag_data.key).first()
    if existing:
        raise HTTPException(status_code=400, detail="Flag key already exists")

    flag_service = FlagService(db)
    try:
        flag = flag_service.create_flag(flag_data)
        logger.info("flag_created", flag_key=flag.key, flag_id=flag.id)
        return flag
    except Exception as e:
        logger.error("flag_creation_failed", flag_key=flag_data.key, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create feature flag")

@router.put("/{flag_key}", response_model=FeatureFlagResponse)
async def update_flag(
    flag_key: str,
    flag_data: FeatureFlagUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing feature flag"""
    flag = db.query(FeatureFlag).filter(FeatureFlag.key == flag_key).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    flag_service = FlagService(db)
    try:
        updated_flag = flag_service.update_flag(flag, flag_data)
        logger.info("flag_updated", flag_key=flag_key, flag_id=flag.id)
        return updated_flag
    except Exception as e:
        logger.error("flag_update_failed", flag_key=flag_key, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update feature flag")

@router.delete("/{flag_key}")
async def delete_flag(flag_key: str, db: Session = Depends(get_db)):
    """Delete a feature flag"""
    flag = db.query(FeatureFlag).filter(FeatureFlag.key == flag_key).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    flag_service = FlagService(db)
    try:
        flag_service.delete_flag(flag)
        logger.info("flag_deleted", flag_key=flag_key, flag_id=flag.id)
        return {"message": "Feature flag deleted successfully"}
    except Exception as e:
        logger.error("flag_deletion_failed", flag_key=flag_key, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete feature flag")

@router.post("/{flag_key}/toggle")
async def toggle_flag(flag_key: str, db: Session = Depends(get_db)):
    """Toggle a feature flag on/off"""
    flag = db.query(FeatureFlag).filter(FeatureFlag.key == flag_key).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    flag.enabled = not flag.enabled
    db.commit()
    db.refresh(flag)

    logger.info("flag_toggled", flag_key=flag_key, enabled=flag.enabled)
    return {"flag_key": flag_key, "enabled": flag.enabled}

# Experiment management endpoints
@router.get("/{flag_key}/experiments", response_model=List[ExperimentResponse])
async def list_flag_experiments(flag_key: str, db: Session = Depends(get_db)):
    """List experiments for a specific flag"""
    flag = db.query(FeatureFlag).filter(FeatureFlag.key == flag_key).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    experiments = db.query(Experiment).filter(Experiment.flag_id == flag.id).all()
    return experiments

@router.post("/{flag_key}/experiments", response_model=ExperimentResponse)
async def create_experiment(
    flag_key: str,
    experiment_data: ExperimentCreate,
    db: Session = Depends(get_db)
):
    """Create a new experiment for a flag"""
    flag = db.query(FeatureFlag).filter(FeatureFlag.key == flag_key).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    # Validate that the flag_id matches
    if experiment_data.flag_id != flag.id:
        raise HTTPException(status_code=400, detail="Flag ID mismatch")

    flag_service = FlagService(db)
    try:
        experiment = flag_service.create_experiment(experiment_data)

        # Mark the flag as an experiment
        flag.is_experiment = True
        flag.experiment_id = experiment.experiment_id
        db.commit()

        logger.info("experiment_created",
                   experiment_id=experiment.experiment_id,
                   flag_key=flag_key)
        return experiment
    except Exception as e:
        logger.error("experiment_creation_failed",
                    experiment_id=experiment_data.experiment_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create experiment")
