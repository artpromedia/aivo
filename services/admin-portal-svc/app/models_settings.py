"""
Database models for organization and tenant settings
"""

from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
import uuid

from .database import Base


class OrgSettings(Base):
    """Organization-level settings (branding, etc.)"""
    __tablename__ = "org_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(String, nullable=False, unique=True, index=True)
    settings = Column(JSONB, nullable=False, default={})
    updated_by = Column(String, nullable=True)  # User ID who last updated
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<OrgSettings(org_id='{self.org_id}')>"


class TenantSettings(Base):
    """Tenant-level settings (locale, residency, consent)"""
    __tablename__ = "tenant_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, index=True)
    setting_type = Column(String, nullable=False)  # 'locale', 'residency', 'consent'
    settings = Column(JSONB, nullable=False, default={})
    updated_by = Column(String, nullable=True)  # User ID who last updated
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Composite unique constraint on tenant_id + setting_type
    __table_args__ = (
        {'schema': None}  # Ensure we're using the default schema
    )

    def __repr__(self):
        return f"<TenantSettings(tenant_id='{self.tenant_id}', type='{self.setting_type}')>"
