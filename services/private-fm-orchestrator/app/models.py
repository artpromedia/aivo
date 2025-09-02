"""
Database models for private brain orchestrator.
"""
from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

Base = declarative_base()


class PrivateBrainStatus(str, Enum):
    """Status enum for private brain instances."""
    PENDING = "PENDING"
    CLONING = "CLONING"
    READY = "READY"
    ERROR = "ERROR"
    TERMINATED = "TERMINATED"


class PrivateBrainInstance(Base):
    """Model for tracking private brain instances per learner."""
    __tablename__ = "private_brain_instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Learner identification
    learner_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    
    # Namespace and checkpoint information
    ns_uid: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    checkpoint_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Status tracking
    status: Mapped[PrivateBrainStatus] = mapped_column(
        String, 
        nullable=False, 
        default=PrivateBrainStatus.PENDING
    )
    
    # Request tracking
    request_count: Mapped[int] = mapped_column(Integer, default=1)
    last_request_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    
    # Lifecycle timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    ready_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    def __repr__(self) -> str:
        return f"<PrivateBrainInstance(id={self.id}, learner_id={self.learner_id}, status='{self.status}', ns_uid='{self.ns_uid}')>"


class PrivateBrainRequest(Base):
    """Model for tracking individual private brain requests."""
    __tablename__ = "private_brain_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Learner identification
    learner_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Request metadata
    request_source: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # e.g., "learner-svc"
    request_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Processing status
    processed: Mapped[bool] = mapped_column(default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<PrivateBrainRequest(id={self.id}, learner_id={self.learner_id}, processed={self.processed})>"
