"""
Database models for learner service.
"""

import enum
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .database import Base


class ProvisionSource(enum.Enum):
    """Source of learner provision."""

    DISTRICT = "district"
    PARENT = "parent"


# Association table for many-to-many relationship between learners and teachers
learner_teacher_association = Table(
    "learner_teachers",
    Base.metadata,
    Column("learner_id", Integer, ForeignKey("learners.id"), primary_key=True),
    Column("teacher_id", Integer, ForeignKey("teachers.id"), primary_key=True),
    Column("assigned_at", DateTime(timezone=True), server_default=func.now()),
    Column("assigned_by", String, nullable=True),  # Who assigned the teacher
)


class Learner(Base):
    """Learner model with guardian-first approach."""

    __tablename__ = "learners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Core learner information
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)

    # Date of birth for grade calculation
    dob: Mapped[date] = mapped_column(Date, nullable=False)

    # Default grade calculated from DOB
    grade_default: Mapped[int] = mapped_column(Integer, nullable=False)

    # Current grade (can be overridden)
    grade_current: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Provision source
    provision_source: Mapped[ProvisionSource] = mapped_column(Enum(ProvisionSource), nullable=False)

    # Guardian relationship (guardian-first approach)
    guardian_id: Mapped[int] = mapped_column(Integer, ForeignKey("guardians.id"), nullable=False)
    guardian: Mapped["Guardian"] = relationship("Guardian", back_populates="learners")

    # Tenant relationship (optional for district provision)
    tenant_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=True)
    tenant: Mapped[Optional["Tenant"]] = relationship("Tenant", back_populates="learners")

    # Teacher relationships (many-to-many)
    teachers: Mapped[list["Teacher"]] = relationship(
        "Teacher", secondary=learner_teacher_association, back_populates="learners"
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Status
    is_active: Mapped[bool] = mapped_column(default=True)

    def __repr__(self) -> str:
        return f"<Learner(id={self.id}, name='{self.first_name} {self.last_name}', grade={self.grade_default})>"


class Guardian(Base):
    """Guardian model."""

    __tablename__ = "guardians"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Guardian information
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)

    # Learner relationships
    learners: Mapped[list[Learner]] = relationship("Learner", back_populates="guardian")

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Guardian(id={self.id}, name='{self.first_name} {self.last_name}', email='{self.email}')>"


class Teacher(Base):
    """Teacher model."""

    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Teacher information
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    # Subject/specialization
    subject: Mapped[str | None] = mapped_column(String, nullable=True)

    # Tenant relationship (teachers belong to tenants/districts)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=False)
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="teachers")

    # Learner relationships (many-to-many)
    learners: Mapped[list[Learner]] = relationship(
        "Learner", secondary=learner_teacher_association, back_populates="teachers"
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    is_active: Mapped[bool] = mapped_column(default=True)

    def __repr__(self) -> str:
        return f"<Teacher(id={self.id}, name='{self.first_name} {self.last_name}', subject='{self.subject}')>"


class Tenant(Base):
    """Tenant/District model."""

    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Tenant information
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, default="district")  # district, school, etc.

    # Contact information
    contact_email: Mapped[str | None] = mapped_column(String, nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    learners: Mapped[list[Learner]] = relationship("Learner", back_populates="tenant")
    teachers: Mapped[list[Teacher]] = relationship("Teacher", back_populates="tenant")

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    is_active: Mapped[bool] = mapped_column(default=True)

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name='{self.name}', type='{self.type}')>"


class PrivateBrainRequest(Base):
    """Track PRIVATE_BRAIN_REQUEST events."""

    __tablename__ = "private_brain_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Learner reference
    learner_id: Mapped[int] = mapped_column(Integer, ForeignKey("learners.id"), nullable=False)
    learner: Mapped[Learner] = relationship("Learner")

    # Event tracking
    event_type: Mapped[str] = mapped_column(String, default="PRIVATE_BRAIN_REQUEST")
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, sent, failed

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<PrivateBrainRequest(id={self.id}, learner_id={self.learner_id}, status='{self.status}')>"
