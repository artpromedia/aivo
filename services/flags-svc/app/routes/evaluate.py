from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import structlog

from ..database import get_db
from ..schemas import EvaluationRequest, EvaluationResponse, BulkEvaluationRequest, BulkEvaluationResponse
from ..services.evaluation_service import EvaluationService

logger = structlog.get_logger()
router = APIRouter()

@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_flag(
    request: EvaluationRequest,
    db: Session = Depends(get_db)
):
    """Evaluate a single feature flag for a user context"""
    evaluation_service = EvaluationService(db)

    try:
        result = evaluation_service.evaluate_flag(
            flag_key=request.flag_key,
            context=request.context,
            default_value=request.default_value
        )

        # Log the evaluation for analytics
        await evaluation_service.log_exposure(
            flag_key=request.flag_key,
            context=request.context,
            result=result
        )

        return result
    except Exception as e:
        logger.error("flag_evaluation_failed",
                    flag_key=request.flag_key,
                    user_id=request.context.user_id,
                    error=str(e))

        # Return default value on error
        return EvaluationResponse(
            flag_key=request.flag_key,
            value=request.default_value,
            reason="error"
        )

@router.post("/evaluate/bulk", response_model=BulkEvaluationResponse)
async def evaluate_flags_bulk(
    request: BulkEvaluationRequest,
    db: Session = Depends(get_db)
):
    """Evaluate multiple feature flags for a user context"""
    evaluation_service = EvaluationService(db)

    evaluations = {}

    for flag_key in request.flag_keys:
        default_value = request.default_values.get(flag_key, False)

        try:
            result = evaluation_service.evaluate_flag(
                flag_key=flag_key,
                context=request.context,
                default_value=default_value
            )

            # Log the evaluation for analytics
            await evaluation_service.log_exposure(
                flag_key=flag_key,
                context=request.context,
                result=result
            )

            evaluations[flag_key] = result

        except Exception as e:
            logger.error("bulk_flag_evaluation_failed",
                        flag_key=flag_key,
                        user_id=request.context.user_id,
                        error=str(e))

            # Return default value on error
            evaluations[flag_key] = EvaluationResponse(
                flag_key=flag_key,
                value=default_value,
                reason="error"
            )

    return BulkEvaluationResponse(evaluations=evaluations)

@router.get("/flags/{user_id}")
async def get_user_flags(
    user_id: str,
    tenant_id: str = None,
    user_role: str = None,
    user_region: str = None,
    user_grade_band: str = None,
    db: Session = Depends(get_db)
):
    """Get all enabled flags for a specific user (SDK helper endpoint)"""
    from ..schemas import EvaluationContext

    context = EvaluationContext(
        user_id=user_id,
        tenant_id=tenant_id,
        user_role=user_role,
        user_region=user_region,
        user_grade_band=user_grade_band
    )

    evaluation_service = EvaluationService(db)

    try:
        # Get all enabled flags for the tenant
        enabled_flags = evaluation_service.get_enabled_flags_for_tenant(tenant_id)

        results = {}
        for flag in enabled_flags:
            result = evaluation_service.evaluate_flag(
                flag_key=flag.key,
                context=context,
                default_value=False
            )

            if result.value:  # Only return flags that evaluate to True
                results[flag.key] = {
                    "value": result.value,
                    "variant": result.variant,
                    "experiment_id": result.experiment_id
                }

        return {"flags": results, "user_id": user_id, "tenant_id": tenant_id}

    except Exception as e:
        logger.error("user_flags_fetch_failed",
                    user_id=user_id,
                    tenant_id=tenant_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch user flags")
