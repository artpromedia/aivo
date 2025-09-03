"""
Database models for the Approval Service.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, String, DateTime, Boolean, Text, Integer, 
    ForeignKey, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .enums import (
    ApprovalStatus, ParticipantRole, DecisionType, 
    ApprovalType, Priority, NotificationChannel
)

Base = declarative_base()


class Approval(Base):
    """Main approval request model."""
    __tablename__ = "approvals"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(100), nullable=False, index=True)
    
    # Approval metadata
    approval_type = Column(SQLEnum(ApprovalType), nullable=False)
    status = Column(SQLEnum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING)
    priority = Column(SQLEnum(Priority), nullable=False, default=Priority.NORMAL)
    
    # Resource information
    resource_type = Column(String(100), nullable=False)  # e.g., "iep_document", "assessment"
    resource_id = Column(String(200), nullable=False)
    resource_data = Column(JSON, nullable=True)  # Additional resource metadata
    
    # Approval details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(String(200), nullable=False)
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Workflow configuration
    required_participants = Column(Integer, nullable=False, default=2)
    require_all_participants = Column(Boolean, nullable=False, default=True)
    
    # External integration
    webhook_url = Column(String(1000), nullable=True)
    webhook_events = Column(JSON, nullable=True)  # List of events to send
    callback_data = Column(JSON, nullable=True)  # Data to include in callbacks
    
    # Relationships
    participants = relationship("ApprovalParticipant", back_populates="approval", cascade="all, delete-orphan")
    decisions = relationship("ApprovalDecision", back_populates="approval", cascade="all, delete-orphan")
    notifications = relationship("ApprovalNotification", back_populates="approval", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_approvals_tenant_status', 'tenant_id', 'status'),
        Index('ix_approvals_resource', 'resource_type', 'resource_id'),
        Index('ix_approvals_expires_at', 'expires_at'),
        Index('ix_approvals_created_by', 'created_by'),
    )
    
    @property
    def is_expired(self) -> bool:
        """Check if approval has expired."""
        now = datetime.now(timezone.utc)
        expires_at = self.expires_at
        
        # Handle timezone-naive expires_at from database
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        return now > expires_at
    
    @property
    def approval_progress(self) -> Dict[str, Any]:
        """Get approval progress information."""
        total_participants = len(self.participants)
        approved_count = sum(1 for p in self.participants if p.has_approved)
        rejected_count = sum(1 for p in self.participants if p.has_rejected)
        pending_count = total_participants - approved_count - rejected_count
        
        return {
            "total_participants": total_participants,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "pending_count": pending_count,
            "completion_percentage": (approved_count / total_participants * 100) if total_participants > 0 else 0
        }


class ApprovalParticipant(Base):
    """Participant in an approval workflow."""
    __tablename__ = "approval_participants"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_id = Column(UUID(as_uuid=True), ForeignKey("approvals.id"), nullable=False)
    
    # Participant information
    user_id = Column(String(200), nullable=False)
    email = Column(String(320), nullable=False)
    role = Column(SQLEnum(ParticipantRole), nullable=False)
    display_name = Column(String(200), nullable=False)
    
    # Participation status
    is_required = Column(Boolean, nullable=False, default=True)
    has_responded = Column(Boolean, nullable=False, default=False)
    notified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    participant_metadata = Column(JSON, nullable=True)  # Additional participant data
    
    # Relationships
    approval = relationship("Approval", back_populates="participants")
    decisions = relationship("ApprovalDecision", back_populates="participant")
    
    # Indexes
    __table_args__ = (
        Index('ix_participants_approval_id', 'approval_id'),
        Index('ix_participants_user_id', 'user_id'),
        Index('ix_participants_role', 'role'),
    )
    
    @property
    def has_approved(self) -> bool:
        """Check if participant has approved."""
        return any(d.decision_type == DecisionType.APPROVE for d in self.decisions)
    
    @property
    def has_rejected(self) -> bool:
        """Check if participant has rejected."""
        return any(d.decision_type == DecisionType.REJECT for d in self.decisions)
    
    @property
    def latest_decision(self) -> Optional['ApprovalDecision']:
        """Get the latest decision by this participant."""
        if not self.decisions:
            return None
        return max(self.decisions, key=lambda d: d.created_at)


class ApprovalDecision(Base):
    """Decision made by a participant."""
    __tablename__ = "approval_decisions"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_id = Column(UUID(as_uuid=True), ForeignKey("approvals.id"), nullable=False)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("approval_participants.id"), nullable=False)
    
    # Decision details
    decision_type = Column(SQLEnum(DecisionType), nullable=False)
    comments = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ip_address = Column(String(45), nullable=True)  # Support IPv6
    user_agent = Column(String(500), nullable=True)
    decision_metadata = Column(JSON, nullable=True)
    
    # Relationships
    approval = relationship("Approval", back_populates="decisions")
    participant = relationship("ApprovalParticipant", back_populates="decisions")
    
    # Indexes
    __table_args__ = (
        Index('ix_decisions_approval_id', 'approval_id'),
        Index('ix_decisions_participant_id', 'participant_id'),
        Index('ix_decisions_created_at', 'created_at'),
    )


class ApprovalNotification(Base):
    """Notification sent for approval events."""
    __tablename__ = "approval_notifications"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_id = Column(UUID(as_uuid=True), ForeignKey("approvals.id"), nullable=False)
    
    # Notification details
    recipient_user_id = Column(String(200), nullable=False)
    recipient_email = Column(String(320), nullable=False)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    
    # Content
    subject = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    
    # Status
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    notification_metadata = Column(JSON, nullable=True)
    
    # Relationships
    approval = relationship("Approval", back_populates="notifications")
    
    # Indexes
    __table_args__ = (
        Index('ix_notifications_approval_id', 'approval_id'),
        Index('ix_notifications_recipient', 'recipient_user_id'),
        Index('ix_notifications_sent_at', 'sent_at'),
    )
