"""Database models for Evidence Service."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class EvidenceUpload(Base):
    """Evidence upload records."""
    
    __tablename__ = "evidence_uploads"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    learner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    s3_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    upload_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    processing_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
    )
    
    # Relationships
    extractions: Mapped[list["EvidenceExtraction"]] = relationship(
        back_populates="upload",
        cascade="all, delete-orphan",
    )
    goal_linkages: Mapped[list["IEPGoalLinkage"]] = relationship(
        back_populates="upload",
        cascade="all, delete-orphan",
    )
    audit_entries: Mapped[list["EvidenceAuditEntry"]] = relationship(
        back_populates="upload",
        cascade="all, delete-orphan",
    )


class EvidenceExtraction(Base):
    """Text extraction results from evidence."""
    
    __tablename__ = "evidence_extractions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    upload_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    extraction_method: Mapped[str] = mapped_column(String(50), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    subject_tags: Mapped[list] = mapped_column(JSON, default=list)
    extraction_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Relationships
    upload: Mapped["EvidenceUpload"] = relationship(back_populates="extractions")


class IEPGoal(Base):
    """IEP learning goals and objectives."""
    
    __tablename__ = "iep_goals"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    learner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    goal_text: Mapped[str] = mapped_column(Text, nullable=False)
    subject_area: Mapped[str] = mapped_column(String(100), nullable=False)
    goal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_criteria: Mapped[str] = mapped_column(Text, nullable=True)
    measurement_method: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    
    # Relationships
    evidence_linkages: Mapped[list["IEPGoalLinkage"]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan",
    )


class IEPGoalLinkage(Base):
    """Links between evidence and IEP goals."""
    
    __tablename__ = "iep_goal_linkages"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    upload_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    goal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    learner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    linkage_reason: Mapped[str] = mapped_column(Text, nullable=True)
    matching_keywords: Mapped[list] = mapped_column(JSON, default=list)
    teacher_validated: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    validated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    validation_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Relationships
    upload: Mapped["EvidenceUpload"] = relationship(back_populates="goal_linkages")
    goal: Mapped["IEPGoal"] = relationship(back_populates="evidence_linkages")


class EvidenceAuditEntry(Base):
    """Audit trail entries for evidence processing."""
    
    __tablename__ = "evidence_audit_entries"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    upload_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    learner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action_details: Mapped[dict] = mapped_column(JSON, default=dict)
    performed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
    
    # SHA-256 audit chain fields
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    chain_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    upload: Mapped["EvidenceUpload"] = relationship(back_populates="audit_entries")
