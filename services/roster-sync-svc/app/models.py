"""Database models for roster synchronization service."""
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class ConnectorType(str, Enum):
    """Supported roster import connector types."""
    
    ONEROSTER = "oneroster"
    CLEVER = "clever"
    CSV = "csv"


class SyncStatus(str, Enum):
    """Roster sync job status."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SCIMStatus(str, Enum):
    """SCIM provisioning status."""
    
    PENDING = "pending"
    PROVISIONED = "provisioned"
    FAILED = "failed"
    UPDATED = "updated"
    DELETED = "deleted"


class UserRole(str, Enum):
    """User roles in the system."""
    
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"
    STAFF = "staff"
    PARENT = "parent"
    GUARDIAN = "guardian"


class RecordStatus(str, Enum):
    """Record status for entities."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"
    SUSPENDED = "suspended"


class District(Base):
    """District/Organization model."""
    
    __tablename__ = "districts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sis_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    state_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    nces_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    status: Mapped[RecordStatus] = mapped_column(default=RecordStatus.ACTIVE)
    
    # Metadata
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    schools: Mapped[List["School"]] = relationship(
        "School", back_populates="district", cascade="all, delete-orphan"
    )
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="district", cascade="all, delete-orphan"
    )
    sync_jobs: Mapped[List["SyncJob"]] = relationship(
        "SyncJob", back_populates="district"
    )


class School(Base):
    """School model."""
    
    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    district_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("districts.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sis_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    state_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    nces_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    low_grade: Mapped[Optional[str]] = mapped_column(String(10))
    high_grade: Mapped[Optional[str]] = mapped_column(String(10))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    address_street: Mapped[Optional[str]] = mapped_column(String(255))
    address_city: Mapped[Optional[str]] = mapped_column(String(100))
    address_state: Mapped[Optional[str]] = mapped_column(String(10))
    address_zip: Mapped[Optional[str]] = mapped_column(String(20))
    principal_name: Mapped[Optional[str]] = mapped_column(String(255))
    principal_email: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[RecordStatus] = mapped_column(default=RecordStatus.ACTIVE)
    
    # Metadata
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    district: Mapped["District"] = relationship("District", back_populates="schools")
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="school", cascade="all, delete-orphan"
    )
    classes: Mapped[List["Class"]] = relationship(
        "Class", back_populates="school", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        UniqueConstraint("district_id", "external_id", name="uq_school_district_external"),
    )


class User(Base):
    """User model for students, teachers, and staff."""
    
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    district_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("districts.id"), nullable=False
    )
    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id")
    )
    
    # Core user data
    username: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100))
    title: Mapped[Optional[str]] = mapped_column(String(50))
    role: Mapped[UserRole] = mapped_column(nullable=False)
    
    # Student-specific fields
    grade_level: Mapped[Optional[str]] = mapped_column(String(10))
    graduation_year: Mapped[Optional[int]] = mapped_column(Integer)
    birth_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    
    # External identifiers
    sis_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    state_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    # Contact information
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    address: Mapped[Optional[str]] = mapped_column(Text)
    
    # Status and SCIM
    status: Mapped[RecordStatus] = mapped_column(default=RecordStatus.ACTIVE)
    scim_status: Mapped[SCIMStatus] = mapped_column(default=SCIMStatus.PENDING)
    scim_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    scim_error: Mapped[Optional[str]] = mapped_column(Text)
    scim_last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Metadata
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    district: Mapped["District"] = relationship("District", back_populates="users")
    school: Mapped[Optional["School"]] = relationship("School", back_populates="users")
    enrollments: Mapped[List["Enrollment"]] = relationship(
        "Enrollment", back_populates="user", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        UniqueConstraint("district_id", "external_id", name="uq_user_district_external"),
        UniqueConstraint("district_id", "email", name="uq_user_district_email"),
    )


class Course(Base):
    """Course model."""
    
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    district_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("districts.id"), nullable=False
    )
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    course_code: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    course_number: Mapped[Optional[str]] = mapped_column(String(100))
    subject: Mapped[Optional[str]] = mapped_column(String(100))
    grade_level: Mapped[Optional[str]] = mapped_column(String(10))
    description: Mapped[Optional[str]] = mapped_column(Text)
    credits: Mapped[Optional[int]] = mapped_column(Integer)
    sis_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    status: Mapped[RecordStatus] = mapped_column(default=RecordStatus.ACTIVE)
    
    # Metadata
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    classes: Mapped[List["Class"]] = relationship(
        "Class", back_populates="course", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        UniqueConstraint("district_id", "external_id", name="uq_course_district_external"),
    )


class Class(Base):
    """Class/Section model."""
    
    __tablename__ = "classes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    course_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id")
    )
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    class_code: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    section_number: Mapped[Optional[str]] = mapped_column(String(50))
    subject: Mapped[Optional[str]] = mapped_column(String(100))
    grade_level: Mapped[Optional[str]] = mapped_column(String(10))
    period: Mapped[Optional[str]] = mapped_column(String(50))
    room: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Term information
    term_name: Mapped[Optional[str]] = mapped_column(String(255))
    term_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    term_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Primary teacher
    primary_teacher_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    
    sis_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    status: Mapped[RecordStatus] = mapped_column(default=RecordStatus.ACTIVE)
    
    # Metadata
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    school: Mapped["School"] = relationship("School", back_populates="classes")
    course: Mapped[Optional["Course"]] = relationship("Course", back_populates="classes")
    primary_teacher: Mapped[Optional["User"]] = relationship("User")
    enrollments: Mapped[List["Enrollment"]] = relationship(
        "Enrollment", back_populates="class_", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        UniqueConstraint("school_id", "external_id", name="uq_class_school_external"),
    )


class Enrollment(Base):
    """Enrollment model linking users to classes."""
    
    __tablename__ = "enrollments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False
    )
    
    role: Mapped[UserRole] = mapped_column(nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[RecordStatus] = mapped_column(default=RecordStatus.ACTIVE)
    
    # Metadata
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="enrollments")
    class_: Mapped["Class"] = relationship("Class", back_populates="enrollments")
    
    __table_args__ = (
        UniqueConstraint("user_id", "class_id", name="uq_enrollment_user_class"),
    )


class SyncJob(Base):
    """Roster synchronization job tracking."""
    
    __tablename__ = "sync_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    district_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("districts.id"), nullable=False
    )
    
    connector_type: Mapped[ConnectorType] = mapped_column(nullable=False)
    job_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Job configuration
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Job status and progress
    status: Mapped[SyncStatus] = mapped_column(default=SyncStatus.PENDING)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Results
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_created: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Webhook notifications
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500))
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(255))
    webhook_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Celery task tracking
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    district: Mapped["District"] = relationship("District", back_populates="sync_jobs")
    logs: Mapped[List["SyncLog"]] = relationship(
        "SyncLog", back_populates="sync_job", cascade="all, delete-orphan"
    )


class SyncLog(Base):
    """Detailed logging for sync operations."""
    
    __tablename__ = "sync_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sync_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sync_jobs.id"), nullable=False
    )
    
    level: Mapped[str] = mapped_column(String(20), nullable=False)  # INFO, WARNING, ERROR
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Record context
    record_type: Mapped[Optional[str]] = mapped_column(String(50))  # user, school, class, etc.
    record_id: Mapped[Optional[str]] = mapped_column(String(255))
    external_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Relationships
    sync_job: Mapped["SyncJob"] = relationship("SyncJob", back_populates="logs")


class ConnectorConfig(Base):
    """Connector configuration for different roster sources."""
    
    __tablename__ = "connector_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    district_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("districts.id"), nullable=False
    )
    
    connector_type: Mapped[ConnectorType] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Connection configuration
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Credentials (encrypted)
    credentials: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_sync_status: Mapped[Optional[SyncStatus]] = mapped_column()
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    
    __table_args__ = (
        UniqueConstraint("district_id", "name", name="uq_connector_district_name"),
    )
