"""
Translation service for i18n management.

Core service for managing translations with accessibility compliance.
"""
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AccessibilityLevel,
    LocaleConfiguration,
    SupportedLocale,
    Translation,
    TranslationKey,
    get_locale_display_name,
    is_rtl_locale,
)


def validate_locale_code(locale: str) -> bool:
    """Validate if locale code is supported."""
    supported_codes = [loc.value for loc in SupportedLocale]
    return locale in supported_codes


def get_fallback_locale(locale: str) -> str:
    """Get fallback locale for given locale."""
    fallback_map = {
        "ig-NG": "en-US",
        "yo-NG": "en-US", 
        "ha-NG": "en-US",
        "efi-NG": "en-US",
        "sw-KE": "en-US",
        "sw-TZ": "sw-KE",
        "xh-ZA": "en-GB",
        "es-ES": "en-US",
        "fr-FR": "en-US",
        "de-DE": "en-US",
        "pt-BR": "en-US",
        "zh-CN": "en-US",
        "ja-JP": "en-US",
        "ko-KR": "en-US",
        "hi-IN": "en-US",
        "ar-SA": "en-US",
    }
    return fallback_map.get(locale, "en-US")


def calculate_completion_percentage(total_keys: int, translated_keys: int) -> float:
    """Calculate translation completion percentage."""
    if total_keys == 0:
        return 100.0
    return round((translated_keys / total_keys) * 100, 2)


class TranslationService:
    """Service for managing translations and localization."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_translation(
        self,
        key: str,
        locale: str,
        fallback: bool = True
    ) -> Optional[str]:
        """
        Get translation for key and locale.
        
        Returns translation value or fallback if not found.
        """
        # Try to get translation for requested locale
        stmt = (
            select(Translation.value)
            .join(TranslationKey)
            .where(
                and_(
                    TranslationKey.key == key,
                    Translation.locale == locale,
                    Translation.is_approved == True,
                    TranslationKey.is_active == True
                )
            )
        )
        result = await self.db.execute(stmt)
        translation = result.scalar_one_or_none()
        
        if translation:
            return translation
            
        # Try fallback locale if enabled
        if fallback:
            fallback_locale = get_fallback_locale(locale)
            if fallback_locale != locale:
                return await self.get_translation(key, fallback_locale, False)
        
        return None
    
    async def get_translations_bulk(
        self,
        keys: List[str],
        locale: str,
        fallback: bool = True
    ) -> Dict[str, str]:
        """
        Get multiple translations efficiently.
        
        Returns dictionary mapping keys to translated values.
        """
        # Get translations for requested locale
        stmt = (
            select(TranslationKey.key, Translation.value)
            .join(Translation)
            .where(
                and_(
                    TranslationKey.key.in_(keys),
                    Translation.locale == locale,
                    Translation.is_approved == True,
                    TranslationKey.is_active == True
                )
            )
        )
        result = await self.db.execute(stmt)
        translations = dict(result.fetchall())
        
        # Get missing keys for fallback
        if fallback:
            missing_keys = [k for k in keys if k not in translations]
            if missing_keys:
                fallback_locale = get_fallback_locale(locale)
                if fallback_locale != locale:
                    fallback_translations = await self.get_translations_bulk(
                        missing_keys, fallback_locale, False
                    )
                    translations.update(fallback_translations)
        
        return translations
    
    async def create_translation_key(
        self,
        key: str,
        context: Optional[str] = None,
        description: Optional[str] = None,
        source_file: Optional[str] = None,
        source_line: Optional[int] = None,
        accessibility_notes: Optional[str] = None
    ) -> TranslationKey:
        """Create new translation key."""
        translation_key = TranslationKey(
            key=key,
            context=context,
            description=description,
            source_file=source_file,
            source_line=source_line,
            accessibility_notes=accessibility_notes
        )
        
        self.db.add(translation_key)
        await self.db.commit()
        await self.db.refresh(translation_key)
        
        return translation_key
    
    async def create_translation(
        self,
        key_id: UUID,
        locale: str,
        value: str,
        translator_id: Optional[str] = None,
        auto_approve: bool = False,
        wcag_level: AccessibilityLevel = AccessibilityLevel.AA
    ) -> Translation:
        """Create new translation."""
        if not validate_locale_code(locale):
            raise ValueError(f"Unsupported locale: {locale}")
        
        translation = Translation(
            key_id=key_id,
            locale=locale,
            value=value,
            translator_id=translator_id,
            is_approved=auto_approve,
            wcag_level=wcag_level.value
        )
        
        self.db.add(translation)
        await self.db.commit()
        await self.db.refresh(translation)
        
        return translation
    
    async def update_translation(
        self,
        translation_id: UUID,
        value: str,
        translator_id: Optional[str] = None,
        requires_review: bool = True
    ) -> Optional[Translation]:
        """Update existing translation."""
        stmt = select(Translation).where(Translation.id == translation_id)
        result = await self.db.execute(stmt)
        translation = result.scalar_one_or_none()
        
        if not translation:
            return None
        
        translation.value = value
        translation.translator_id = translator_id
        translation.is_approved = not requires_review
        
        await self.db.commit()
        await self.db.refresh(translation)
        
        return translation
    
    async def approve_translation(
        self,
        translation_id: UUID,
        reviewer_id: str,
        quality_score: Optional[float] = None
    ) -> Optional[Translation]:
        """Approve translation after review."""
        stmt = select(Translation).where(Translation.id == translation_id)
        result = await self.db.execute(stmt)
        translation = result.scalar_one_or_none()
        
        if not translation:
            return None
        
        translation.is_approved = True
        translation.reviewer_id = reviewer_id
        translation.quality_score = quality_score
        
        await self.db.commit()
        await self.db.refresh(translation)
        
        return translation
    
    async def get_locale_stats(self, locale: str) -> Dict:
        """Get translation statistics for locale."""
        # Total keys
        total_stmt = select(TranslationKey).where(TranslationKey.is_active == True)
        total_result = await self.db.execute(total_stmt)
        total_keys = len(total_result.fetchall())
        
        # Translated keys
        translated_stmt = (
            select(Translation)
            .join(TranslationKey)
            .where(
                and_(
                    Translation.locale == locale,
                    Translation.is_approved == True,
                    TranslationKey.is_active == True
                )
            )
        )
        translated_result = await self.db.execute(translated_stmt)
        translated_keys = len(translated_result.fetchall())
        
        completion_percentage = calculate_completion_percentage(
            total_keys, translated_keys
        )
        
        return {
            "locale": locale,
            "display_name": get_locale_display_name(locale),
            "total_keys": total_keys,
            "translated_keys": translated_keys,
            "completion_percentage": completion_percentage,
            "is_rtl": is_rtl_locale(locale),
        }
    
    async def search_translations(
        self,
        query: str,
        locale: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """Search translations by key or value."""
        conditions = [
            or_(
                TranslationKey.key.ilike(f"%{query}%"),
                Translation.value.ilike(f"%{query}%")
            ),
            TranslationKey.is_active == True
        ]
        
        if locale:
            conditions.append(Translation.locale == locale)
        
        stmt = (
            select(TranslationKey, Translation)
            .join(Translation)
            .where(and_(*conditions))
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.db.execute(stmt)
        rows = result.fetchall()
        
        # Count total results
        count_stmt = (
            select(TranslationKey.id)
            .join(Translation)
            .where(and_(*conditions))
        )
        count_result = await self.db.execute(count_stmt)
        total = len(count_result.fetchall())
        
        translations = []
        for key, translation in rows:
            translations.append({
                "key": key.key,
                "locale": translation.locale,
                "value": translation.value,
                "is_approved": translation.is_approved,
                "quality_score": translation.quality_score,
                "wcag_level": translation.wcag_level,
                "updated_at": translation.updated_at
            })
        
        return translations, total
    
    async def get_missing_translations(
        self, locale: str, limit: int = 100
    ) -> List[str]:
        """Get list of keys missing translations for locale."""
        # Get all active keys
        all_keys_stmt = (
            select(TranslationKey.key)
            .where(TranslationKey.is_active == True)
        )
        all_keys_result = await self.db.execute(all_keys_stmt)
        all_keys = {row[0] for row in all_keys_result.fetchall()}
        
        # Get translated keys for locale
        translated_stmt = (
            select(TranslationKey.key)
            .join(Translation)
            .where(
                and_(
                    Translation.locale == locale,
                    Translation.is_approved == True,
                    TranslationKey.is_active == True
                )
            )
        )
        translated_result = await self.db.execute(translated_stmt)
        translated_keys = {row[0] for row in translated_result.fetchall()}
        
        # Find missing keys
        missing_keys = list(all_keys - translated_keys)
        return missing_keys[:limit]


class LocaleService:
    """Service for managing locale configurations."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_enabled_locales(self) -> List[LocaleConfiguration]:
        """Get all enabled locale configurations."""
        stmt = (
            select(LocaleConfiguration)
            .where(LocaleConfiguration.is_enabled == True)
            .order_by(LocaleConfiguration.display_name)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_locale_config(self, locale: str) -> Optional[LocaleConfiguration]:
        """Get locale configuration by code."""
        stmt = select(LocaleConfiguration).where(
            LocaleConfiguration.locale == locale
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_completion_percentage(self, locale: str) -> Optional[float]:
        """Update and return completion percentage for locale."""
        translation_service = TranslationService(self.db)
        stats = await translation_service.get_locale_stats(locale)
        
        config = await self.get_locale_config(locale)
        if config:
            config.completion_percentage = stats["completion_percentage"]
            await self.db.commit()
            return stats["completion_percentage"]
        
        return None
