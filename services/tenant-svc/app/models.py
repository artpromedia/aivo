"""
Database models for tenant service.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from sqlalchemy.sql import func

Base = declarative_base()


class TenantKind(str, Enum):
    """Types of tenants in the system."""
    DISTRICT = "district"
    SCHOOL = "school"


class SeatState(str, Enum):
    """States a seat can be in."""
    FREE = "free"
    RESERVED = "reserved"
    ASSIGNED = "assigned"


class UserRole(str, Enum):
    """User roles within a tenant."""
    ADMIN = "admin"
    MANAGER = "manager"
    TEACHER = "teacher"
    LEARNER = "learner"


class Tenant(Base):
    """
    Represents a tenant in the multi-tenant system.
    Can be either a district (parent) or school (child).
    """
    __tablename__ = "tenant"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[TenantKind] = mapped_column(SQLEnum(TenantKind), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("tenant.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    parent: Mapped[Optional["Tenant"]] = relationship(
        "Tenant", remote_side=[id], back_populates="children"
    )
    children: Mapped[List["Tenant"]] = relationship(
        "Tenant", back_populates="parent"
    )
    seats: Mapped[List["Seat"]] = relationship(
        "Seat", back_populates="tenant", cascade="all, delete-orphan"
    )
    user_roles: Mapped[List["UserTenantRole"]] = relationship(
        "UserTenantRole", back_populates="tenant", cascade="all, delete-orphan"
    )


class Seat(Base):
    """
    Represents a seat that can be allocated to learners.
    """
    __tablename__ = "seat"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenant.id"), nullable=False, index=True
    )
    state: Mapped[SeatState] = mapped_column(SQLEnum(SeatState), default=SeatState.FREE)
    learner_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    reserved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="seats")
    audit_entries: Mapped[List["SeatAudit"]] = relationship(
        "SeatAudit", back_populates="seat", cascade="all, delete-orphan"
    )


class UserTenantRole(Base):
    """
    Junction table for user roles within specific tenants.
    """
    __tablename__ = "user_tenant_role"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenant.id"), nullable=False, index=True
    )
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="user_roles")

    __table_args__ = (
        # Ensure unique user-tenant-role combination
        {"schema": None},
    )


class SeatAudit(Base):
    """
    Audit trail for seat state changes.
    """
    __tablename__ = "seat_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    seat_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("seat.id"), nullable=False, index=True
    )
    previous_state: Mapped[Optional[SeatState]] = mapped_column(SQLEnum(SeatState), nullable=True)
    new_state: Mapped[SeatState] = mapped_column(SQLEnum(SeatState), nullable=False)
    previous_learner_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    new_learner_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    changed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    seat: Mapped["Seat"] = relationship("Seat", back_populates="audit_entries")
