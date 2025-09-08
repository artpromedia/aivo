"""
Database models for enrollment router service.
"""

import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class ProvisionSource(str, enum.Enum):
    """Enrollment provision source."""

    DISTRICT = "district"
    PARENT = "parent"


class EnrollmentStatus(str, enum.Enum):
    """Enrollment processing status."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CHECKOUT_REQUIRED = "checkout_required"


class EnrollmentDecision(Base):
    """Records enrollment routing decisions."""

    __tablename__ = "enrollment_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Learner information
    learner_id: Mapped[str | None] = mapped_column(String(255), index=True)
    learner_email: Mapped[str | None] = mapped_column(String(255), index=True)
    learner_profile: Mapped[dict] = mapped_column(JSON)

    # Context information
    tenant_id: Mapped[int | None] = mapped_column(Integer, index=True)
    guardian_id: Mapped[str | None] = mapped_column(String(255), index=True)
    context: Mapped[dict] = mapped_column(JSON)

    # Decision results
    provision_source: Mapped[ProvisionSource] = mapped_column(Enum(ProvisionSource), index=True)
    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus), default=EnrollmentStatus.PENDING
    )

    # District enrollment details
    district_seats_available: Mapped[int | None] = mapped_column(Integer)
    district_seats_reserved: Mapped[int | None] = mapped_column(Integer)

    # Parent enrollment details
    checkout_session_id: Mapped[str | None] = mapped_column(String(255))
    checkout_url: Mapped[str | None] = mapped_column(Text)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Result metadata
    decision_metadata: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)


class DistrictSeatAllocation(Base):
    """Tracks district seat allocations and usage."""

    __tablename__ = "district_seat_allocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # District information
    tenant_id: Mapped[int] = mapped_column(Integer, index=True, unique=True)

    # Seat allocation
    total_seats: Mapped[int] = mapped_column(Integer, default=0)
    reserved_seats: Mapped[int] = mapped_column(Integer, default=0)
    used_seats: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @property
    def available_seats(self) -> int:
        """Calculate available seats."""
        return self.total_seats - self.used_seats - self.reserved_seats
