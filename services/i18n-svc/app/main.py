"""
FastAPI application for i18n service.

Main application with API endpoints for translation management.
"""
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.models import Base
from app.schemas import (
    TranslationCreate, TranslationResponse, TranslationUpdate,
    LocaleConfigCreate, LocaleConfigResponse,
    AccessibilityAuditResponse, AccessibilityStatsResponse
)
from app.services.translation_service import TranslationService, LocaleService
from app.services.accessibility_service import AccessibilityService


# Database setup
DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/i18n_db"
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup on shutdown
    await engine.dispose()


# FastAPI app setup
app = FastAPI(
    title="AIVO i18n Service",
    description="Internationalization service with accessibility compliance",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_db_session() -> AsyncSession:
    """Get database session dependency."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_translation_service(
    db: AsyncSession = Depends(get_db_session)
) -> TranslationService:
    """Get translation service dependency."""
    return TranslationService(db)


async def get_locale_service(
    db: AsyncSession = Depends(get_db_session)
) -> LocaleService:
    """Get locale service dependency."""
    return LocaleService(db)


async def get_accessibility_service(
    db: AsyncSession = Depends(get_db_session)
) -> AccessibilityService:
    """Get accessibility service dependency."""
    return AccessibilityService(db)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "aivo-i18n"}


# Translation endpoints
@app.post("/translations", response_model=TranslationResponse)
async def create_translation(
    translation: TranslationCreate,
    service: TranslationService = Depends(get_translation_service)
):
    """Create new translation."""
    try:
        result = await service.create_translation(
            key=translation.key,
            locale=translation.locale,
            value=translation.value,
            context=translation.context,
            description=translation.description
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/translations", response_model=List[TranslationResponse])
async def list_translations(
    locale: Optional[str] = Query(None, description="Filter by locale"),
    key: Optional[str] = Query(None, description="Filter by translation key"),
    approved_only: bool = Query(True, description="Only return approved translations"),
    limit: int = Query(100, le=1000, description="Number of translations to return"),
    service: TranslationService = Depends(get_translation_service)
):
    """List translations with filtering."""
    return await service.get_translations(
        locale=locale,
        key=key,
        approved_only=approved_only,
        limit=limit
    )


@app.get("/translations/{translation_id}", response_model=TranslationResponse)
async def get_translation(
    translation_id: UUID,
    service: TranslationService = Depends(get_translation_service)
):
    """Get specific translation by ID."""
    translation = await service.get_translation_by_id(translation_id)
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")
    return translation


@app.put("/translations/{translation_id}", response_model=TranslationResponse)
async def update_translation(
    translation_id: UUID,
    translation_update: TranslationUpdate,
    service: TranslationService = Depends(get_translation_service)
):
    """Update existing translation."""
    try:
        result = await service.update_translation(
            translation_id=translation_id,
            value=translation_update.value,
            context=translation_update.context,
            description=translation_update.description,
            is_approved=translation_update.is_approved
        )
        if not result:
            raise HTTPException(status_code=404, detail="Translation not found")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/translations/{translation_id}")
async def delete_translation(
    translation_id: UUID,
    service: TranslationService = Depends(get_translation_service)
):
    """Delete translation."""
    success = await service.delete_translation(translation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Translation not found")
    return {"message": "Translation deleted successfully"}


@app.post("/translations/{translation_id}/approve")
async def approve_translation(
    translation_id: UUID,
    service: TranslationService = Depends(get_translation_service)
):
    """Approve translation for use."""
    success = await service.approve_translation(translation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Translation not found")
    return {"message": "Translation approved successfully"}


# Bulk operations
@app.get("/translations/locale/{locale}/export")
async def export_locale_translations(
    locale: str,
    approved_only: bool = Query(True),
    service: TranslationService = Depends(get_translation_service)
):
    """Export all translations for a locale as JSON."""
    translations = await service.get_locale_translations(locale, approved_only)
    return {
        "locale": locale,
        "count": len(translations),
        "translations": {t.key: t.value for t in translations}
    }


@app.post("/translations/bulk-import")
async def bulk_import_translations(
    translations_data: Dict[str, Dict[str, str]],
    service: TranslationService = Depends(get_translation_service)
):
    """Bulk import translations. Format: {locale: {key: value}}."""
    imported_count = 0
    errors = []
    
    for locale, translations in translations_data.items():
        for key, value in translations.items():
            try:
                await service.create_translation(
                    key=key,
                    locale=locale,
                    value=value
                )
                imported_count += 1
            except Exception as e:
                errors.append(f"Error importing {locale}.{key}: {str(e)}")
    
    return {
        "imported_count": imported_count,
        "errors": errors,
        "success": len(errors) == 0
    }


# Locale configuration endpoints
@app.post("/locales", response_model=LocaleConfigResponse)
async def create_locale_config(
    locale_config: LocaleConfigCreate,
    service: LocaleService = Depends(get_locale_service)
):
    """Create locale configuration."""
    try:
        result = await service.create_locale_config(
            locale=locale_config.locale,
            display_name=locale_config.display_name,
            is_rtl=locale_config.is_rtl,
            is_enabled=locale_config.is_enabled,
            fallback_locale=locale_config.fallback_locale
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/locales", response_model=List[LocaleConfigResponse])
async def list_locale_configs(
    enabled_only: bool = Query(False),
    service: LocaleService = Depends(get_locale_service)
):
    """List locale configurations."""
    return await service.get_locale_configs(enabled_only=enabled_only)


@app.get("/locales/{locale}/stats")
async def get_locale_stats(
    locale: str,
    service: LocaleService = Depends(get_locale_service)
):
    """Get translation completion statistics for locale."""
    stats = await service.get_locale_completion_stats(locale)
    if not stats:
        raise HTTPException(status_code=404, detail="Locale configuration not found")
    return stats


# Accessibility endpoints
@app.post("/accessibility/audit/{translation_id}", response_model=AccessibilityAuditResponse)
async def audit_translation(
    translation_id: UUID,
    audit_type: str = Query("automated", description="Audit type"),
    auditor_id: Optional[str] = Query(None, description="Auditor ID"),
    service: AccessibilityService = Depends(get_accessibility_service)
):
    """Perform accessibility audit on translation."""
    try:
        result = await service.audit_translation(
            translation_id=translation_id,
            audit_type=audit_type,
            auditor_id=auditor_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/accessibility/audit/locale/{locale}")
async def bulk_audit_locale(
    locale: str,
    audit_type: str = Query("automated"),
    batch_size: int = Query(50, le=100),
    service: AccessibilityService = Depends(get_accessibility_service)
):
    """Perform bulk accessibility audit for locale."""
    result = await service.bulk_audit_locale(
        locale=locale,
        audit_type=audit_type,
        batch_size=batch_size
    )
    return result


@app.get("/accessibility/stats", response_model=AccessibilityStatsResponse)
async def get_accessibility_stats(
    locale: Optional[str] = Query(None),
    service: AccessibilityService = Depends(get_accessibility_service)
):
    """Get accessibility compliance statistics."""
    return await service.get_accessibility_stats(locale=locale)


@app.get("/accessibility/audits", response_model=List[AccessibilityAuditResponse])
async def get_audit_history(
    translation_id: Optional[UUID] = Query(None),
    locale: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    service: AccessibilityService = Depends(get_accessibility_service)
):
    """Get accessibility audit history."""
    return await service.get_audit_history(
        translation_id=translation_id,
        locale=locale,
        limit=limit
    )


# Search and filtering
@app.get("/search/translations")
async def search_translations(
    query: str = Query(..., min_length=1, description="Search query"),
    locale: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    service: TranslationService = Depends(get_translation_service)
):
    """Search translations by key or value."""
    return await service.search_translations(
        query=query,
        locale=locale,
        limit=limit
    )


@app.get("/translations/missing/{locale}")
async def get_missing_translations(
    locale: str,
    reference_locale: str = Query("en-US", description="Reference locale"),
    service: TranslationService = Depends(get_translation_service)
):
    """Get translations missing in target locale compared to reference."""
    return await service.get_missing_translations(
        target_locale=locale,
        reference_locale=reference_locale
    )


# Analytics endpoints
@app.get("/analytics/completion")
async def get_completion_analytics(
    service: LocaleService = Depends(get_locale_service)
):
    """Get completion analytics for all locales."""
    configs = await service.get_locale_configs(enabled_only=True)
    analytics = []
    
    for config in configs:
        stats = await service.get_locale_completion_stats(config.locale)
        analytics.append({
            "locale": config.locale,
            "display_name": config.display_name,
            "completion_percentage": stats["completion_percentage"],
            "total_translations": stats["total_translations"],
            "translated_count": stats["translated_count"],
            "is_enabled": config.is_enabled
        })
    
    # Sort by completion percentage
    analytics.sort(key=lambda x: x["completion_percentage"], reverse=True)
    
    return {
        "locales": analytics,
        "summary": {
            "total_locales": len(analytics),
            "fully_complete": len([a for a in analytics if a["completion_percentage"] == 100]),
            "partially_complete": len([a for a in analytics if 0 < a["completion_percentage"] < 100]),
            "empty_locales": len([a for a in analytics if a["completion_percentage"] == 0])
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
