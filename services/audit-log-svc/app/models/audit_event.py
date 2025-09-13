"""Immutable audit event model with hash chain verification."""

import hashlib
import json
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import JSON, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class AuditEvent(Base, TimestampMixin):
    """
    Immutable audit event model with WORM compliance.

    This table is append-only and uses hash chaining for tamper detection.
    Once written, records cannot be modified or deleted.
    """

    __tablename__ = "audit_events"

    # Core audit fields
    timestamp: Mapped[datetime] = mapped_column(
        nullable=False,
        index=True,
        insert_default=lambda: datetime.utcnow(),
    )

    # Actor information
    actor: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="User ID or system identifier who performed the action"
    )

    actor_role: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Role of the actor at the time of action"
    )

    # Action details
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Action performed (create, update, delete, login, etc.)"
    )

    # Resource information
    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of resource affected (user, api_key, webhook, etc.)"
    )

    resource_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="ID of the specific resource affected"
    )

    # Change tracking
    before_state: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="State before the change (for updates/deletes)"
    )

    after_state: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="State after the change (for creates/updates)"
    )

    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 support
        nullable=True,
        comment="IP address of the request"
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User agent string from the request"
    )

    request_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Unique request ID for correlation"
    )

    session_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Session ID if applicable"
    )

    # Additional metadata
    metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional context-specific metadata"
    )

    # Hash chain for tamper detection
    current_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="SHA-256 hash of this record's content"
    )

    previous_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="Hash of the previous audit record in chain"
    )

    # Compliance fields
    retention_until: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Date when this record can be archived (compliance)"
    )

    compliance_flags: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Compliance-related flags and metadata"
    )

    # Database indexes for efficient querying
    __table_args__ = (
        Index('idx_audit_timestamp_desc', 'timestamp', postgresql_using='btree'),
        Index('idx_audit_actor_timestamp', 'actor', 'timestamp'),
        Index('idx_audit_action_timestamp', 'action', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_hash_chain', 'previous_hash', 'current_hash'),
        Index('idx_audit_request_correlation', 'request_id', 'session_id'),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<AuditEvent(id={self.id}, actor='{self.actor}', "
            f"action='{self.action}', resource='{self.resource_type}')>"
        )

    def calculate_hash(self, previous_hash: Optional[str] = None) -> str:
        """
        Calculate SHA-256 hash of this audit event's content.

        Args:
            previous_hash: Hash of the previous record in the chain

        Returns:
            SHA-256 hash as hexadecimal string
        """
        # Create deterministic content for hashing
        content = {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "actor": self.actor,
            "actor_role": self.actor_role,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "metadata": self.metadata,
            "previous_hash": previous_hash,
        }

        # Convert to JSON with sorted keys for deterministic hashing
        content_json = json.dumps(content, sort_keys=True, separators=(',', ':'))

        # Calculate SHA-256 hash
        return hashlib.sha256(content_json.encode('utf-8')).hexdigest()

    def verify_hash(self) -> bool:
        """
        Verify that the stored hash matches the calculated hash.

        Returns:
            True if hash is valid, False otherwise
        """
        calculated_hash = self.calculate_hash(self.previous_hash)
        return calculated_hash == self.current_hash

    @classmethod
    def create_audit_event(
        cls,
        actor: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        before_state: Optional[dict[str, Any]] = None,
        after_state: Optional[dict[str, Any]] = None,
        actor_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        previous_hash: Optional[str] = None,
        retention_until: Optional[datetime] = None,
        compliance_flags: Optional[dict[str, Any]] = None,
    ) -> "AuditEvent":
        """
        Create a new audit event with proper hash calculation.

        Args:
            actor: User ID or system identifier
            action: Action performed
            resource_type: Type of resource affected
            resource_id: ID of specific resource
            before_state: State before change
            after_state: State after change
            actor_role: Role of actor
            ip_address: IP address of request
            user_agent: User agent string
            request_id: Request ID for correlation
            session_id: Session ID if applicable
            metadata: Additional metadata
            previous_hash: Hash of previous record in chain
            retention_until: Retention date for compliance
            compliance_flags: Compliance metadata

        Returns:
            New AuditEvent instance with calculated hash
        """
        # Create the audit event
        event = cls(
            timestamp=datetime.utcnow(),
            actor=actor,
            actor_role=actor_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            session_id=session_id,
            metadata=metadata,
            previous_hash=previous_hash,
            retention_until=retention_until,
            compliance_flags=compliance_flags,
        )

        # Calculate and set the hash
        event.current_hash = event.calculate_hash(previous_hash)

        return event
