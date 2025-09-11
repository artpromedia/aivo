"""
Consent management API endpoints.

GDPR/COPPA compliant consent tracking and management.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ConsentRecord, ConsentType, ConsentStatus
from app.services import ConsentService
from config import get_db


router = APIRouter()


# Request/Response models
class ConsentRequest(BaseModel):
    """Request model for creating consent."""
    user_id: str = Field(..., description="User identifier")
    consent_type: ConsentType = Field(..., description="Type of consent")
    purposes: List[str] = Field(..., description="Data processing purposes")
    given: bool = Field(..., description="Whether consent is given")
    user_agent: Optional[str] = Field(None, description="User agent information")
    ip_address: Optional[str] = Field(None, description="IP address")
    metadata: Optional[dict] = Field(None, description="Additional metadata")
    
    @validator("user_id")
    def validate_user_id(cls, v):
        """Validate user ID format."""
        if not v or len(v.strip()) == 0:
            raise ValueError("User ID cannot be empty")
        return v.strip()
    
    @validator("purposes")
    def validate_purposes(cls, v):
        """Validate purposes list."""
        if not v or len(v) == 0:
            raise ValueError("At least one purpose must be specified")
        return [p.strip() for p in v if p.strip()]


class ConsentResponse(BaseModel):
    """Response model for consent records."""
    id: UUID
    user_id: str
    consent_type: ConsentType
    purposes: List[str]
    given: bool
    status: ConsentStatus
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    version: int
    
    class Config:
        from_attributes = True


class ConsentUpdateRequest(BaseModel):
    """Request model for updating consent."""
    given: bool = Field(..., description="Whether consent is given")
    purposes: Optional[List[str]] = Field(None, description="Updated purposes")
    user_agent: Optional[str] = Field(None, description="User agent information")
    ip_address: Optional[str] = Field(None, description="IP address")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class ConsentListResponse(BaseModel):
    """Response model for consent list."""
    consents: List[ConsentResponse]
    total: int
    page: int
    per_page: int


def get_consent_service(db: AsyncSession = Depends(get_db)) -> ConsentService:
    """Get consent service instance."""
    return ConsentService(db)


@router.post("/", response_model=ConsentResponse, status_code=201)
async def create_consent(
    request: ConsentRequest,
    consent_service: ConsentService = Depends(get_consent_service)
):
    """
    Create a new consent record.
    
    Creates a consent record with proper audit logging and COPPA/GDPR compliance.
    """
    try:
        consent = await consent_service.create_consent(
            user_id=request.user_id,
            consent_type=request.consent_type,
            purposes=request.purposes,
            given=request.given,
            user_agent=request.user_agent,
            ip_address=request.ip_address,
            metadata=request.metadata or {}
        )
        return ConsentResponse.from_orm(consent)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create consent")


@router.get("/user/{user_id}", response_model=ConsentListResponse)
async def get_user_consents(
    user_id: str,
    consent_type: Optional[ConsentType] = Query(None, description="Filter by consent type"),
    status: Optional[ConsentStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    consent_service: ConsentService = Depends(get_consent_service)
):
    """
    Get consent records for a user.
    
    Returns paginated list of consent records with optional filtering.
    """
    try:
        consents, total = await consent_service.get_user_consents(
            user_id=user_id,
            consent_type=consent_type,
            status=status,
            limit=per_page,
            offset=(page - 1) * per_page
        )
        
        return ConsentListResponse(
            consents=[ConsentResponse.from_orm(c) for c in consents],
            total=total,
            page=page,
            per_page=per_page
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve consents")


@router.get("/{consent_id}", response_model=ConsentResponse)
async def get_consent(
    consent_id: UUID,
    consent_service: ConsentService = Depends(get_consent_service)
):
    """
    Get a specific consent record by ID.
    
    Returns detailed consent information including audit trail.
    """
    try:
        consent = await consent_service.get_consent(consent_id)
        if not consent:
            raise HTTPException(status_code=404, detail="Consent not found")
        
        return ConsentResponse.from_orm(consent)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve consent")


@router.put("/{consent_id}", response_model=ConsentResponse)
async def update_consent(
    consent_id: UUID,
    request: ConsentUpdateRequest,
    consent_service: ConsentService = Depends(get_consent_service)
):
    """
    Update an existing consent record.
    
    Creates a new version of the consent with proper audit logging.
    """
    try:
        consent = await consent_service.update_consent(
            consent_id=consent_id,
            given=request.given,
            purposes=request.purposes,
            user_agent=request.user_agent,
            ip_address=request.ip_address,
            metadata=request.metadata or {}
        )
        
        if not consent:
            raise HTTPException(status_code=404, detail="Consent not found")
        
        return ConsentResponse.from_orm(consent)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update consent")


@router.delete("/{consent_id}", status_code=204)
async def withdraw_consent(
    consent_id: UUID,
    user_agent: Optional[str] = Query(None, description="User agent"),
    ip_address: Optional[str] = Query(None, description="IP address"),
    consent_service: ConsentService = Depends(get_consent_service)
):
    """
    Withdraw consent (GDPR Article 7).
    
    Marks consent as withdrawn with proper audit logging.
    """
    try:
        success = await consent_service.withdraw_consent(
            consent_id=consent_id,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Consent not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to withdraw consent")


@router.get("/user/{user_id}/status")
async def get_consent_status(
    user_id: str,
    purposes: List[str] = Query(..., description="Required purposes"),
    consent_service: ConsentService = Depends(get_consent_service)
):
    """
    Check consent status for specific purposes.
    
    Validates if user has given valid consent for specified purposes.
    """
    try:
        valid_consents = await consent_service.check_consent_validity(
            user_id=user_id,
            purposes=purposes
        )
        
        return {
            "user_id": user_id,
            "purposes": purposes,
            "valid": len(valid_consents) > 0,
            "consents": [
                {
                    "id": str(consent.id),
                    "type": consent.consent_type,
                    "purposes": consent.purposes,
                    "expires_at": consent.expires_at.isoformat() if consent.expires_at else None
                }
                for consent in valid_consents
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to check consent status")


@router.post("/user/{user_id}/withdraw-all", status_code=204)
async def withdraw_all_consents(
    user_id: str,
    user_agent: Optional[str] = Query(None, description="User agent"),
    ip_address: Optional[str] = Query(None, description="IP address"),
    consent_service: ConsentService = Depends(get_consent_service)
):
    """
    Withdraw all consents for a user.
    
    Convenience endpoint for complete consent withdrawal.
    """
    try:
        await consent_service.withdraw_all_consents(
            user_id=user_id,
            user_agent=user_agent,
            ip_address=ip_address
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to withdraw all consents")
