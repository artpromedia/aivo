"""
Database models for internationalization service.

SQLAlchemy models for managing translations and accessibility metadata.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class SupportedLocale(str, Enum):
    """Supported locale codes including African languages."""
    
    # Primary languages
    EN_US = "en-US"  # English (United States)
    EN_GB = "en-GB"  # English (United Kingdom)
    
    # African languages
    IG_NG = "ig-NG"  # Igbo (Nigeria) 
    YO_NG = "yo-NG"  # Yoruba (Nigeria)
    HA_NG = "ha-NG"  # Hausa (Nigeria)
    EFI_NG = "efi-NG"  # Efik (Nigeria)
    SW_KE = "sw-KE"  # Swahili (Kenya)
    SW_TZ = "sw-TZ"  # Swahili (Tanzania)
    XH_ZA = "xh-ZA"  # Xhosa (South Africa)
    
    # European languages
    ES_ES = "es-ES"  # Spanish (Spain)
    FR_FR = "fr-FR"  # French (France)
    DE_DE = "de-DE"  # German (Germany)
    PT_BR = "pt-BR"  # Portuguese (Brazil)
    
    # Asian languages
    ZH_CN = "zh-CN"  # Chinese (Simplified)
    JA_JP = "ja-JP"  # Japanese
    KO_KR = "ko-KR"  # Korean
    HI_IN = "hi-IN"  # Hindi (India)
    AR_SA = "ar-SA"  # Arabic (Saudi Arabia)


class AccessibilityLevel(str, Enum):
    """WCAG accessibility compliance levels."""
    
    A = "A"
    AA = "AA"
    AAA = "AAA"


def generate_uuid() -> UUID:
    """Generate UUID for primary keys."""
    return uuid4()


def is_rtl_locale(locale: str) -> bool:
    """Check if locale uses right-to-left text direction."""
    rtl_locales = ["ar-SA"]
    return locale in rtl_locales


def get_locale_display_name(locale: str) -> str:
    """Get human-readable display name for locale."""
    locale_names = {
        "en-US": "English (United States)",
        "en-GB": "English (United Kingdom)",
        "ig-NG": "Igbo (Nigeria)",
        "yo-NG": "Yoruba (Nigeria)", 
        "ha-NG": "Hausa (Nigeria)",
        "efi-NG": "Efik (Nigeria)",
        "sw-KE": "Swahili (Kenya)",
        "sw-TZ": "Swahili (Tanzania)",
        "xh-ZA": "Xhosa (South Africa)",
        "es-ES": "Español (España)",
        "fr-FR": "Français (France)",
        "de-DE": "Deutsch (Deutschland)",
        "pt-BR": "Português (Brasil)",
        "zh-CN": "中文 (简体)",
        "ja-JP": "日本語",
        "ko-KR": "한국어",
        "hi-IN": "हनद (भरत)",
        "ar-SA": "العربية (السعودية)",
    }
    return locale_names.get(locale, locale)


class TranslationKey(Base):
    """Translation key and metadata model."""
    
    __tablename__ = "translation_keys"
    
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    context: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    source_file: Mapped[Optional[str]] = mapped_column(String(500))
    source_line: Mapped[Optional[int]]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_review: Mapped[bool] = mapped_column(Boolean, default=False)
    accessibility_notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    translations: Mapped[List["Translation"]] = relationship(
        "Translation",
        back_populates="translation_key",
        cascade="all, delete-orphan"
    )


class Translation(Base):
    """Translation model for specific locales."""
    
    __tablename__ = "translations"
    
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    key_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False,
        index=True
    )
    locale: Mapped[str] = mapped_column(String(10), index=True)
    value: Mapped[str] = mapped_column(Text)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    translator_id: Mapped[Optional[str]] = mapped_column(String(255))
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(255))
    quality_score: Mapped[Optional[float]]
    accessibility_compliant: Mapped[bool] = mapped_column(Boolean, default=True)
    wcag_level: Mapped[str] = mapped_column(
        String(3),
        default=AccessibilityLevel.AA
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    translation_key: Mapped["TranslationKey"] = relationship(
        "TranslationKey",
        back_populates="translations"
    )


class LocaleConfiguration(Base):
    """Locale configuration and metadata."""
    
    __tablename__ = "locale_configurations"
    
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    locale: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    native_name: Mapped[str] = mapped_column(String(100))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_rtl: Mapped[bool] = mapped_column(Boolean, default=False)
    completion_percentage: Mapped[float] = mapped_column(default=0.0)
    fallback_locale: Mapped[Optional[str]] = mapped_column(String(10))
    date_format: Mapped[str] = mapped_column(String(50), default="%Y-%m-%d")
    time_format: Mapped[str] = mapped_column(String(50), default="%H:%M:%S")
    number_format: Mapped[Dict] = mapped_column(JSON, default=dict)
    currency_format: Mapped[Dict] = mapped_column(JSON, default=dict)
    accessibility_config: Mapped[Dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


class AccessibilityAudit(Base):
    """Accessibility audit results for translations."""
    
    __tablename__ = "accessibility_audits"
    
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    translation_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False,
        index=True
    )
    audit_type: Mapped[str] = mapped_column(String(50))  # "automated", "manual"
    wcag_level: Mapped[str] = mapped_column(String(3))
    score: Mapped[float]  # 0-100 percentage
    issues_found: Mapped[List[Dict]] = mapped_column(JSON, default=list)
    recommendations: Mapped[List[str]] = mapped_column(JSON, default=list)
    auditor_id: Mapped[Optional[str]] = mapped_column(String(255))
    audit_tool: Mapped[Optional[str]] = mapped_column(String(100))
    audit_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    next_audit_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )


class TranslationRequest(Base):
    """Translation request workflow model."""
    
    __tablename__ = "translation_requests"
    
    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    key_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=False,
        index=True
    )
    target_locale: Mapped[str] = mapped_column(String(10))
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    requester_id: Mapped[str] = mapped_column(String(255))
    assigned_translator_id: Mapped[Optional[str]] = mapped_column(String(255))
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
