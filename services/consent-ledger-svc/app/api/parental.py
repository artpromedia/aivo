"""
Parental rights API endpoints.

COPPA compliant parental consent and rights management.
"""

from datetime import datetime
from uuid import UUID

from config import get_db
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ParentalRightStatus
from app.services import ParentalRightsService

router = APIRouter()


# Request/Response models
class ParentalVerificationRequest(BaseModel):
    """Request model for parental verification."""

    child_user_id: str = Field(..., description="Child user identifier")
    parent_email: str = Field(..., description="Parent email address")
    parent_name: str = Field(..., description="Parent full name")
    verification_method: str = Field("email", description="Verification method")
    metadata: dict | None = Field(None, description="Additional metadata")

    @validator("parent_email")
    def validate_email(self, v):
        """Validate email format."""
        import re

        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError("Invalid email format")
        return v.lower().strip()

    @validator("child_user_id", "parent_name")
    def validate_not_empty(self, v):
        """Validate non-empty fields."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Field cannot be empty")
        return v.strip()


class ParentalRightResponse(BaseModel):
    """Response model for parental rights."""

    id: UUID
    child_user_id: str
    parent_email: str
    parent_name: str
    status: ParentalRightStatus
    verification_token: str | None
    verified_at: datetime | None
    expires_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class ParentalConsentRequest(BaseModel):
    """Request model for parental consent."""

    consent_given: bool = Field(..., description="Whether consent is given")
    purposes: list[str] = Field(..., description="Data processing purposes")
    metadata: dict | None = Field(None, description="Additional metadata")


def get_parental_service(db: AsyncSession = Depends(get_db)) -> ParentalRightsService:
    """Get parental rights service instance."""
    return ParentalRightsService(db)


@router.post("/verify", response_model=ParentalRightResponse, status_code=201)
async def initiate_parental_verification(
    request: ParentalVerificationRequest,
    background_tasks: BackgroundTasks,
    parental_service: ParentalRightsService = Depends(get_parental_service),
):
    """
    Initiate parental verification process.

    Sends verification email to parent and creates pending parental right record.
    """
    try:
        parental_right = await parental_service.initiate_verification(
            child_user_id=request.child_user_id,
            parent_email=request.parent_email,
            parent_name=request.parent_name,
            verification_method=request.verification_method,
            metadata=request.metadata or {},
        )

        # Send verification email in background
        background_tasks.add_task(parental_service.send_verification_email, parental_right.id)

        return ParentalRightResponse.from_orm(parental_right)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to initiate verification")


@router.post("/verify/{token}")
async def complete_parental_verification(
    token: str, parental_service: ParentalRightsService = Depends(get_parental_service)
):
    """
    Complete parental verification using token.

    Verifies the token and activates parental rights.
    """
    try:
        success = await parental_service.verify_token(token)
        if not success:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")

        return {"message": "Parental verification completed successfully"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to complete verification")


@router.get("/child/{child_user_id}", response_model=list[ParentalRightResponse])
async def get_parental_rights(
    child_user_id: str, parental_service: ParentalRightsService = Depends(get_parental_service)
):
    """
    Get parental rights for a child user.

    Returns all parental right records for the specified child.
    """
    try:
        rights = await parental_service.get_child_parental_rights(child_user_id)
        return [ParentalRightResponse.from_orm(right) for right in rights]
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve parental rights")


@router.get("/{right_id}", response_model=ParentalRightResponse)
async def get_parental_right(
    right_id: UUID, parental_service: ParentalRightsService = Depends(get_parental_service)
):
    """
    Get specific parental right by ID.

    Returns detailed parental right information.
    """
    try:
        right = await parental_service.get_parental_right(right_id)
        if not right:
            raise HTTPException(status_code=404, detail="Parental right not found")

        return ParentalRightResponse.from_orm(right)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve parental right")


@router.post("/{right_id}/consent")
async def manage_parental_consent(
    right_id: UUID,
    request: ParentalConsentRequest,
    parental_service: ParentalRightsService = Depends(get_parental_service),
):
    """
    Manage consent on behalf of child.

    Allows verified parent to give or withdraw consent for their child.
    """
    try:
        consent = await parental_service.manage_child_consent(
            parental_right_id=right_id,
            consent_given=request.consent_given,
            purposes=request.purposes,
            metadata=request.metadata or {},
        )

        if not consent:
            raise HTTPException(status_code=404, detail="Parental right not found or not verified")

        return {
            "message": f"Consent {'given' if request.consent_given else 'withdrawn'} successfully",
            "consent_id": str(consent.id),
            "purposes": request.purposes,
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to manage consent")


@router.delete("/{right_id}", status_code=204)
async def revoke_parental_right(
    right_id: UUID, parental_service: ParentalRightsService = Depends(get_parental_service)
):
    """
    Revoke parental rights.

    Deactivates parental rights and related consents.
    """
    try:
        success = await parental_service.revoke_parental_right(right_id)
        if not success:
            raise HTTPException(status_code=404, detail="Parental right not found")

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to revoke parental right")


@router.get("/verify/status/{token}")
async def check_verification_status(
    token: str, parental_service: ParentalRightsService = Depends(get_parental_service)
):
    """
    Check verification token status.

    Returns information about the verification token without completing verification.
    """
    try:
        status_info = await parental_service.check_verification_status(token)
        if not status_info:
            raise HTTPException(status_code=404, detail="Verification token not found")

        return status_info
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to check verification status")


@router.post("/{right_id}/resend-verification")
async def resend_verification(
    right_id: UUID,
    background_tasks: BackgroundTasks,
    parental_service: ParentalRightsService = Depends(get_parental_service),
):
    """
    Resend verification email.

    Generates new verification token and sends email.
    """
    try:
        success = await parental_service.resend_verification(right_id)
        if not success:
            raise HTTPException(
                status_code=404, detail="Parental right not found or already verified"
            )

        # Send verification email in background
        background_tasks.add_task(parental_service.send_verification_email, right_id)

        return {"message": "Verification email sent successfully"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to resend verification")
