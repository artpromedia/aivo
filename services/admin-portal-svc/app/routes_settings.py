"""
Admin Portal Settings API Routes
Handles organization/tenant settings for branding, locale, residency, and consent
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr
import json

from .database import get_db
from .models import OrgSettings, TenantSettings, User
from .auth import get_current_admin_user

router = APIRouter(prefix="/admin/settings", tags=["settings"])


# Pydantic Models for Settings
class OrgSettingsRequest(BaseModel):
    brand_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    support_email: Optional[EmailStr] = None
    website_url: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    terms_of_service_url: Optional[str] = None


class LocaleSettingsRequest(BaseModel):
    default_locale: Optional[str] = None
    time_zone: Optional[str] = None
    date_format: Optional[str] = None
    currency: Optional[str] = None
    grade_scheme: Optional[str] = None  # A-F, 1-10, percentage, etc.
    first_day_of_week: Optional[int] = None  # 0=Sunday, 1=Monday


class ResidencySettingsRequest(BaseModel):
    region: Optional[str] = None  # us-east, eu-west, ap-southeast
    processing_purposes: Optional[list[str]] = None
    data_retention_days: Optional[int] = None
    cross_border_transfer: Optional[bool] = None
    compliance_framework: Optional[str] = None  # GDPR, CCPA, COPPA


class ConsentSettingsRequest(BaseModel):
    media_default: Optional[bool] = None  # Default consent for media capture
    analytics_opt_in: Optional[bool] = None  # Default analytics opt-in
    retention_days: Optional[int] = None
    parental_consent_required: Optional[bool] = None
    consent_expiry_days: Optional[int] = None
    withdrawal_process: Optional[str] = None


class SettingsResponse(BaseModel):
    id: str
    settings: Dict[str, Any]
    updated_by: str
    updated_at: str


def get_or_create_org_settings(db: Session, org_id: str) -> OrgSettings:
    """Get or create organization settings"""
    settings = db.query(OrgSettings).filter(OrgSettings.org_id == org_id).first()
    if not settings:
        settings = OrgSettings(
            org_id=org_id,
            settings={
                "brand_name": "AIVO Education",
                "logo_url": "",
                "primary_color": "#3B82F6",
                "support_email": "support@aivo.education",
                "website_url": "https://aivo.education",
                "privacy_policy_url": "",
                "terms_of_service_url": ""
            }
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def get_or_create_tenant_settings(db: Session, tenant_id: str, setting_type: str) -> TenantSettings:
    """Get or create tenant settings for a specific type"""
    settings = db.query(TenantSettings).filter(
        TenantSettings.tenant_id == tenant_id,
        TenantSettings.setting_type == setting_type
    ).first()

    if not settings:
        default_settings = {
            "locale": {
                "default_locale": "en-US",
                "time_zone": "UTC",
                "date_format": "MM/DD/YYYY",
                "currency": "USD",
                "grade_scheme": "letter",
                "first_day_of_week": 0
            },
            "residency": {
                "region": "us-east",
                "processing_purposes": ["educational", "analytics"],
                "data_retention_days": 2555,  # 7 years
                "cross_border_transfer": False,
                "compliance_framework": "FERPA"
            },
            "consent": {
                "media_default": False,
                "analytics_opt_in": True,
                "retention_days": 2555,
                "parental_consent_required": True,
                "consent_expiry_days": 365,
                "withdrawal_process": "contact_support"
            }
        }

        settings = TenantSettings(
            tenant_id=tenant_id,
            setting_type=setting_type,
            settings=default_settings.get(setting_type, {})
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


@router.get("/org", response_model=SettingsResponse)
async def get_org_settings(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get organization settings (branding)"""
    try:
        settings = get_or_create_org_settings(db, current_user.org_id)

        return SettingsResponse(
            id=settings.id,
            settings=settings.settings,
            updated_by=settings.updated_by or "system",
            updated_at=settings.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization settings: {str(e)}"
        )


@router.put("/org", response_model=SettingsResponse)
async def update_org_settings(
    settings_request: OrgSettingsRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update organization settings (branding)"""
    try:
        settings = get_or_create_org_settings(db, current_user.org_id)

        # Update only provided fields
        updated_settings = settings.settings.copy()
        for field, value in settings_request.dict(exclude_unset=True).items():
            if value is not None:
                updated_settings[field] = value

        settings.settings = updated_settings
        settings.updated_by = current_user.id

        db.commit()
        db.refresh(settings)

        return SettingsResponse(
            id=settings.id,
            settings=settings.settings,
            updated_by=settings.updated_by,
            updated_at=settings.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization settings: {str(e)}"
        )


@router.get("/locale", response_model=SettingsResponse)
async def get_locale_settings(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get locale settings"""
    try:
        settings = get_or_create_tenant_settings(db, current_user.tenant_id, "locale")

        return SettingsResponse(
            id=settings.id,
            settings=settings.settings,
            updated_by=settings.updated_by or "system",
            updated_at=settings.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get locale settings: {str(e)}"
        )


@router.put("/locale", response_model=SettingsResponse)
async def update_locale_settings(
    settings_request: LocaleSettingsRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update locale settings"""
    try:
        settings = get_or_create_tenant_settings(db, current_user.tenant_id, "locale")

        # Update only provided fields
        updated_settings = settings.settings.copy()
        for field, value in settings_request.dict(exclude_unset=True).items():
            if value is not None:
                updated_settings[field] = value

        settings.settings = updated_settings
        settings.updated_by = current_user.id

        db.commit()
        db.refresh(settings)

        return SettingsResponse(
            id=settings.id,
            settings=settings.settings,
            updated_by=settings.updated_by,
            updated_at=settings.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update locale settings: {str(e)}"
        )


@router.get("/residency", response_model=SettingsResponse)
async def get_residency_settings(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get data residency settings"""
    try:
        settings = get_or_create_tenant_settings(db, current_user.tenant_id, "residency")

        return SettingsResponse(
            id=settings.id,
            settings=settings.settings,
            updated_by=settings.updated_by or "system",
            updated_at=settings.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get residency settings: {str(e)}"
        )


@router.put("/residency", response_model=SettingsResponse)
async def update_residency_settings(
    settings_request: ResidencySettingsRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update data residency settings"""
    try:
        settings = get_or_create_tenant_settings(db, current_user.tenant_id, "residency")

        # Update only provided fields
        updated_settings = settings.settings.copy()
        for field, value in settings_request.dict(exclude_unset=True).items():
            if value is not None:
                updated_settings[field] = value

        settings.settings = updated_settings
        settings.updated_by = current_user.id

        db.commit()
        db.refresh(settings)

        return SettingsResponse(
            id=settings.id,
            settings=settings.settings,
            updated_by=settings.updated_by,
            updated_at=settings.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update residency settings: {str(e)}"
        )


@router.get("/consent", response_model=SettingsResponse)
async def get_consent_settings(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get consent defaults settings"""
    try:
        settings = get_or_create_tenant_settings(db, current_user.tenant_id, "consent")

        return SettingsResponse(
            id=settings.id,
            settings=settings.settings,
            updated_by=settings.updated_by or "system",
            updated_at=settings.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get consent settings: {str(e)}"
        )


@router.put("/consent", response_model=SettingsResponse)
async def update_consent_settings(
    settings_request: ConsentSettingsRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update consent defaults settings"""
    try:
        settings = get_or_create_tenant_settings(db, current_user.tenant_id, "consent")

        # Update only provided fields
        updated_settings = settings.settings.copy()
        for field, value in settings_request.dict(exclude_unset=True).items():
            if value is not None:
                updated_settings[field] = value

        settings.settings = updated_settings
        settings.updated_by = current_user.id

        db.commit()
        db.refresh(settings)

        return SettingsResponse(
            id=settings.id,
            settings=settings.settings,
            updated_by=settings.updated_by,
            updated_at=settings.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update consent settings: {str(e)}"
        )


# Utility endpoint to get all settings for the dashboard
@router.get("/all")
async def get_all_settings(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all settings for dashboard configuration"""
    try:
        org_settings = get_or_create_org_settings(db, current_user.org_id)
        locale_settings = get_or_create_tenant_settings(db, current_user.tenant_id, "locale")
        residency_settings = get_or_create_tenant_settings(db, current_user.tenant_id, "residency")
        consent_settings = get_or_create_tenant_settings(db, current_user.tenant_id, "consent")

        return {
            "org": org_settings.settings,
            "locale": locale_settings.settings,
            "residency": residency_settings.settings,
            "consent": consent_settings.settings
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get all settings: {str(e)}"
        )
