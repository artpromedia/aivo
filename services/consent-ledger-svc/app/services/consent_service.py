"""
Core consent management service.

Handles consent lifecycle, parental rights, and GDPR/COPPA compliance.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    AuditAction,
    AuditLog,
    ConsentRecord,
    ConsentStatus,
    ConsentType,
    ParentalRight,
    ParentalRightType,
    PreferenceSettings,
    is_valid_email,
    requires_parental_consent,
)

logger = logging.getLogger(__name__)


def generate_verification_token() -> str:
    """Helper function to generate secure verification token."""
    return secrets.token_urlsafe(32)


def hash_audit_data(data: dict[str, Any]) -> str:
    """Helper function to create tamper-evident hash for audit logs."""
    data_str = str(sorted(data.items()))
    return hashlib.sha256(data_str.encode()).hexdigest()


def is_consent_expired(expires_at: datetime | None) -> bool:
    """Helper function to check if consent has expired."""
    if expires_at is None:
        return False
    return datetime.utcnow() > expires_at


class ConsentService:
    """
    Core service for managing user consent and preferences.

    Handles GDPR Article 6 legal basis and COPPA parental consent.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def grant_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        legal_basis: str,
        purpose: str,
        data_categories: list[str],
        user_age: int | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None,
        location: str | None = None,
        created_by: str | None = None,
    ) -> ConsentRecord:
        """
        Grant consent for a specific purpose and data categories.

        Handles parental consent requirements for minors.
        """
        logger.info(f"Granting consent for user {user_id}, type: {consent_type.value}")

        # Check if parental consent is required
        needs_parental_consent = requires_parental_consent(user_age)

        # Create consent record
        consent_record = ConsentRecord(
            user_id=user_id,
            consent_type=consent_type,
            status=ConsentStatus.PENDING if needs_parental_consent else ConsentStatus.GRANTED,
            legal_basis=legal_basis,
            purpose=purpose,
            data_categories=data_categories,
            user_agent=user_agent,
            ip_address=ip_address,
            location=location,
            requires_parental_consent=needs_parental_consent,
            created_by=created_by,
        )

        if not needs_parental_consent:
            consent_record.granted_at = datetime.utcnow()
        else:
            # Generate parental verification token
            consent_record.parent_verification_token = generate_verification_token()

        self.db_session.add(consent_record)
        await self.db_session.flush()

        # Create audit log
        await self._create_audit_log(
            action=AuditAction.CONSENT_GRANTED,
            user_id=user_id,
            consent_record_id=consent_record.id,
            actor_id=created_by or user_id,
            actor_type="user" if not needs_parental_consent else "system",
            details={
                "consent_type": consent_type.value,
                "legal_basis": legal_basis,
                "requires_parental_consent": needs_parental_consent,
                "data_categories": data_categories,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        await self.db_session.commit()

        logger.info(
            f"Consent granted for user {user_id} (requires_parental: {needs_parental_consent})"
        )
        return consent_record

    async def revoke_consent(
        self,
        consent_id: UUID,
        revoked_by: str,
        reason: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ConsentRecord:
        """
        Revoke previously granted consent.

        Triggers cascaded deletion if applicable.
        """
        # Get consent record
        stmt = select(ConsentRecord).where(ConsentRecord.id == consent_id)
        result = await self.db_session.execute(stmt)
        consent_record = result.scalar_one_or_none()

        if not consent_record:
            raise ValueError(f"Consent record {consent_id} not found")

        if consent_record.status == ConsentStatus.REVOKED:
            raise ValueError("Consent already revoked")

        logger.info(f"Revoking consent {consent_id} for user {consent_record.user_id}")

        # Update consent record
        old_status = consent_record.status
        consent_record.status = ConsentStatus.REVOKED
        consent_record.revoked_at = datetime.utcnow()

        # Create audit log
        await self._create_audit_log(
            action=AuditAction.CONSENT_REVOKED,
            user_id=consent_record.user_id,
            consent_record_id=consent_record.id,
            actor_id=revoked_by,
            actor_type="user",
            details={
                "consent_type": consent_record.consent_type.value,
                "reason": reason,
                "previous_status": old_status.value,
            },
            old_values={"status": old_status.value},
            new_values={"status": ConsentStatus.REVOKED.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        await self.db_session.commit()

        logger.info(f"Consent {consent_id} revoked successfully")
        return consent_record

    async def verify_parental_consent(
        self,
        verification_token: str,
        parent_email: str,
        ip_address: str | None = None,
    ) -> ConsentRecord:
        """
        Verify parental consent using verification token.

        Completes COPPA compliance process.
        """
        # Find consent record by verification token
        stmt = select(ConsentRecord).where(
            ConsentRecord.parent_verification_token == verification_token
        )
        result = await self.db_session.execute(stmt)
        consent_record = result.scalar_one_or_none()

        if not consent_record:
            raise ValueError("Invalid verification token")

        if not is_valid_email(parent_email):
            raise ValueError("Invalid parent email address")

        logger.info(f"Verifying parental consent for user {consent_record.user_id}")

        # Update consent record
        consent_record.status = ConsentStatus.GRANTED
        consent_record.granted_at = datetime.utcnow()
        consent_record.parent_email = parent_email
        consent_record.parent_verified_at = datetime.utcnow()
        consent_record.parental_consent_given = True

        # Clear verification token
        consent_record.parent_verification_token = None

        # Create audit log
        await self._create_audit_log(
            action=AuditAction.CONSENT_GRANTED,
            user_id=consent_record.user_id,
            consent_record_id=consent_record.id,
            actor_id=parent_email,
            actor_type="parent",
            details={
                "consent_type": consent_record.consent_type.value,
                "parental_verification": True,
                "parent_email": parent_email,
            },
            ip_address=ip_address,
        )

        await self.db_session.commit()

        logger.info(f"Parental consent verified for user {consent_record.user_id}")
        return consent_record

    async def get_user_consents(
        self,
        user_id: str,
        include_revoked: bool = False,
    ) -> list[ConsentRecord]:
        """Get all consent records for a user."""
        stmt = select(ConsentRecord).where(ConsentRecord.user_id == user_id)

        if not include_revoked:
            stmt = stmt.where(ConsentRecord.status != ConsentStatus.REVOKED)

        stmt = stmt.options(selectinload(ConsentRecord.preferences))

        result = await self.db_session.execute(stmt)
        return result.scalars().all()

    async def check_consent_status(
        self,
        user_id: str,
        consent_type: ConsentType,
    ) -> ConsentRecord | None:
        """Check if user has valid consent for specific type."""
        stmt = (
            select(ConsentRecord)
            .where(ConsentRecord.user_id == user_id)
            .where(ConsentRecord.consent_type == consent_type)
            .where(ConsentRecord.status == ConsentStatus.GRANTED)
        )

        result = await self.db_session.execute(stmt)
        consent_record = result.scalar_one_or_none()

        # Check if consent has expired
        if consent_record and is_consent_expired(consent_record.expires_at):
            consent_record.status = ConsentStatus.EXPIRED
            await self.db_session.commit()
            return None

        return consent_record

    async def update_preferences(
        self,
        consent_id: UUID,
        preferences: dict[str, Any],
        updated_by: str,
    ) -> PreferenceSettings:
        """Update user preference settings."""
        # Get consent record
        stmt = (
            select(ConsentRecord)
            .options(selectinload(ConsentRecord.preferences))
            .where(ConsentRecord.id == consent_id)
        )
        result = await self.db_session.execute(stmt)
        consent_record = result.scalar_one_or_none()

        if not consent_record:
            raise ValueError(f"Consent record {consent_id} not found")

        # Get or create preferences
        if consent_record.preferences:
            preference_settings = consent_record.preferences[0]
            old_values = {
                "email_notifications": preference_settings.email_notifications,
                "analytics_tracking": preference_settings.analytics_tracking,
                # Add other fields as needed
            }
        else:
            preference_settings = PreferenceSettings(consent_record_id=consent_id)
            self.db_session.add(preference_settings)
            old_values = {}

        # Update preferences
        for key, value in preferences.items():
            if hasattr(preference_settings, key):
                setattr(preference_settings, key, value)

        # Create audit log
        await self._create_audit_log(
            action=AuditAction.CONSENT_UPDATED,
            user_id=consent_record.user_id,
            consent_record_id=consent_record.id,
            actor_id=updated_by,
            actor_type="user",
            details={
                "preferences_updated": list(preferences.keys()),
            },
            old_values=old_values,
            new_values=preferences,
        )

        await self.db_session.commit()
        return preference_settings

    async def _create_audit_log(
        self,
        action: AuditAction,
        user_id: str,
        actor_id: str,
        actor_type: str,
        details: dict[str, Any] | None = None,
        consent_record_id: UUID | None = None,
        export_request_id: UUID | None = None,
        deletion_request_id: UUID | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
        legal_basis: str | None = None,
    ) -> AuditLog:
        """Create audit log entry with integrity protection."""
        audit_data = {
            "action": action.value,
            "user_id": user_id,
            "actor_id": actor_id,
            "actor_type": actor_type,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {},
            "old_values": old_values,
            "new_values": new_values,
        }

        # Generate integrity checksum
        checksum = hash_audit_data(audit_data)

        audit_log = AuditLog(
            action=action,
            user_id=user_id,
            actor_id=actor_id,
            actor_type=actor_type,
            consent_record_id=consent_record_id,
            export_request_id=export_request_id,
            deletion_request_id=deletion_request_id,
            details=details,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            legal_basis=legal_basis,
            checksum=checksum,
        )

        self.db_session.add(audit_log)
        return audit_log


class ParentalRightsService:
    """
    Service for managing parental rights and controls under COPPA.

    Handles parent-child relationships and rights verification.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def establish_parental_right(
        self,
        parent_email: str,
        child_user_id: str,
        right_type: ParentalRightType,
        verification_method: str = "email",
    ) -> ParentalRight:
        """Establish parental right over child's data."""
        if not is_valid_email(parent_email):
            raise ValueError("Invalid parent email address")

        logger.info(f"Establishing parental right for {parent_email} over child {child_user_id}")

        # Generate verification token
        verification_token = generate_verification_token()

        parental_right = ParentalRight(
            parent_email=parent_email,
            child_user_id=child_user_id,
            right_type=right_type,
            verification_token=verification_token,
            verification_method=verification_method,
            expires_at=datetime.utcnow() + timedelta(days=365),  # 1 year expiration
        )

        self.db_session.add(parental_right)
        await self.db_session.commit()

        return parental_right

    async def verify_parental_right(
        self,
        verification_token: str,
        ip_address: str | None = None,
    ) -> ParentalRight:
        """Verify parental right using verification token."""
        stmt = select(ParentalRight).where(ParentalRight.verification_token == verification_token)
        result = await self.db_session.execute(stmt)
        parental_right = result.scalar_one_or_none()

        if not parental_right:
            raise ValueError("Invalid verification token")

        # Update verification status
        parental_right.verified_at = datetime.utcnow()
        parental_right.verification_token = None  # Clear token after use

        await self.db_session.commit()
        return parental_right

    async def get_parental_rights(
        self,
        parent_email: str,
        active_only: bool = True,
    ) -> list[ParentalRight]:
        """Get all parental rights for a parent."""
        stmt = select(ParentalRight).where(ParentalRight.parent_email == parent_email)

        if active_only:
            stmt = stmt.where(ParentalRight.is_active is True)

        result = await self.db_session.execute(stmt)
        return result.scalars().all()

    async def revoke_parental_right(
        self,
        right_id: UUID,
        revoked_by: str,
    ) -> ParentalRight:
        """Revoke parental right."""
        stmt = select(ParentalRight).where(ParentalRight.id == right_id)
        result = await self.db_session.execute(stmt)
        parental_right = result.scalar_one_or_none()

        if not parental_right:
            raise ValueError(f"Parental right {right_id} not found")

        parental_right.is_active = False
        await self.db_session.commit()

        return parental_right
