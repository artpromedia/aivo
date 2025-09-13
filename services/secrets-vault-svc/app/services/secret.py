"""Sfrom typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4 management service with encryption and audit logging."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import (
    AccessLevel,
    AuditAction,
    Namespace,
    Secret,
    SecretAccessLog,
    SecretAuditLog,
    SecretStatus,
    SecretType,
    SecretVersion,
)
from .encryption import EncryptionService, get_encryption_service


class SecretNotFoundError(Exception):
    """Exception raised when secret is not found."""
    pass


class AccessDeniedError(Exception):
    """Exception raised when access to secret is denied."""
    pass


class SecretExpiredError(Exception):
    """Exception raised when secret has expired."""
    pass


class NamespaceNotFoundError(Exception):
    """Exception raised when namespace is not found."""
    pass


class SecretService:
    """Service for managing secrets with encryption and audit logging."""

    def __init__(self, db: AsyncSession, encryption_service: Optional[EncryptionService] = None):
        """Initialize secret service."""
        self.db = db
        self.encryption_service = encryption_service or get_encryption_service()

    async def _log_audit(
        self,
        secret_id: str,
        action: AuditAction,
        actor: Optional[str] = None,
        actor_type: str = "service",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> SecretAuditLog:
        """Log audit event."""
        audit_log = SecretAuditLog(
            secret_id=secret_id,
            action=action,
            actor=actor,
            actor_type=actor_type,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            details=details,
            old_values=old_values,
            new_values=new_values,
            success=success,
            error_message=error_message,
        )
        self.db.add(audit_log)
        return audit_log

    async def _log_access(
        self,
        secret_id: str,
        accessor: Optional[str] = None,
        accessor_type: str = "service",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        service_name: Optional[str] = None,
        request_id: Optional[str] = None,
        access_method: str = "api",
        success: bool = True,
        error_message: Optional[str] = None,
        response_time_ms: Optional[int] = None,
    ) -> SecretAccessLog:
        """Log access event."""
        access_log = SecretAccessLog(
            secret_id=secret_id,
            accessor=accessor,
            accessor_type=accessor_type,
            ip_address=ip_address,
            user_agent=user_agent,
            service_name=service_name,
            request_id=request_id,
            access_method=access_method,
            success=success,
            error_message=error_message,
            response_time_ms=response_time_ms,
        )
        self.db.add(access_log)
        return access_log

    async def _check_access(
        self,
        secret: Secret,
        accessor: Optional[str] = None,
        service_name: Optional[str] = None,
        required_level: AccessLevel = AccessLevel.READ_ONLY,
    ) -> bool:
        """Check if accessor has permission to access secret."""
        # Check if secret is active
        if secret.status != SecretStatus.ACTIVE:
            return False

        # Check if secret has expired
        if secret.expires_at and secret.expires_at < datetime.utcnow():
            return False

        # Check access level
        if secret.access_level == AccessLevel.ADMIN and required_level == AccessLevel.ADMIN:
            return True
        elif secret.access_level == AccessLevel.READ_WRITE and required_level in [
            AccessLevel.READ_ONLY,
            AccessLevel.READ_WRITE,
        ]:
            return True
        elif secret.access_level == AccessLevel.READ_ONLY and required_level == AccessLevel.READ_ONLY:
            return True

        # Check allowed services
        if service_name and secret.allowed_services:
            if service_name not in secret.allowed_services:
                return False

        # Check allowed users
        if accessor and secret.allowed_users:
            if accessor not in secret.allowed_users:
                return False

        return True

    async def create_secret(
        self,
        name: str,
        value: str,
        namespace: str,
        secret_type: SecretType,
        description: Optional[str] = None,
        tenant_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        access_level: AccessLevel = AccessLevel.READ_ONLY,
        allowed_services: Optional[List[str]] = None,
        allowed_users: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
        rotation_interval_days: Optional[int] = None,
        auto_rotate: bool = False,
        created_by: Optional[str] = None,
        encryption_key_id: str = "default",
    ) -> Secret:
        """Create a new secret with encryption."""
        try:
            # Verify namespace exists
            namespace_result = await self.db.execute(
                select(Namespace).where(Namespace.name == namespace)
            )
            if not namespace_result.scalar_one_or_none():
                raise NamespaceNotFoundError(f"Namespace '{namespace}' not found")

            # Encrypt the secret value
            encrypted_value, key_id, algorithm, salt, nonce = await self.encryption_service.encrypt(
                value, encryption_key_id
            )

            # Create secret record
            secret = Secret(
                name=name,
                description=description,
                namespace=namespace,
                tenant_id=tenant_id,
                secret_type=secret_type,
                encrypted_value=encrypted_value,
                encryption_key_id=key_id,
                encryption_algorithm=algorithm,
                salt=salt,
                nonce=nonce,
                tags=tags,
                secret_metadata=metadata,
                access_level=access_level,
                allowed_services=allowed_services,
                allowed_users=allowed_users,
                expires_at=expires_at,
                rotation_interval_days=rotation_interval_days,
                auto_rotate=auto_rotate,
                created_by=created_by,
            )

            self.db.add(secret)
            await self.db.flush()  # Get the ID

            # Create initial version
            version = SecretVersion(
                secret_id=secret.id,
                version_number=1,
                encrypted_value=encrypted_value,
                encryption_key_id=key_id,
                encryption_algorithm=algorithm,
                salt=salt,
                nonce=nonce,
                metadata_snapshot=metadata,
                created_by=created_by,
                change_reason="Initial creation",
            )
            self.db.add(version)

            # Log audit event
            await self._log_audit(
                secret.id,
                AuditAction.CREATE,
                actor=created_by,
                details={"secret_type": secret_type.value, "namespace": namespace},
                new_values={"name": name, "status": SecretStatus.ACTIVE.value},
            )

            await self.db.commit()
            return secret

        except Exception as e:
            await self.db.rollback()
            raise

    async def get_secret(
        self,
        secret_id: str,
        accessor: Optional[str] = None,
        service_name: Optional[str] = None,
        decrypt: bool = False,
    ) -> Secret:
        """Get secret by ID with access control."""
        result = await self.db.execute(
            select(Secret)
            .options(selectinload(Secret.audit_logs), selectinload(Secret.access_logs))
            .where(Secret.id == secret_id, Secret.is_deleted == False)
        )
        secret = result.scalar_one_or_none()

        if not secret:
            raise SecretNotFoundError(f"Secret with ID {secret_id} not found")

        # Check access permissions
        if not await self._check_access(secret, accessor, service_name, AccessLevel.READ_ONLY):
            await self._log_access(
                secret_id,
                accessor=accessor,
                service_name=service_name,
                success=False,
                error_message="Access denied",
            )
            raise AccessDeniedError("Access denied to secret")

        # Update access tracking
        secret.last_accessed_at = datetime.utcnow()
        secret.access_count += 1

        # Log access
        await self._log_access(
            secret_id,
            accessor=accessor,
            service_name=service_name,
            success=True,
        )

        await self.db.commit()
        return secret

    async def get_secret_value(
        self,
        secret_id: str,
        accessor: Optional[str] = None,
        service_name: Optional[str] = None,
    ) -> str:
        """Get decrypted secret value with access control."""
        secret = await self.get_secret(secret_id, accessor, service_name)

        # Check if secret has expired
        if secret.expires_at and secret.expires_at < datetime.utcnow():
            raise SecretExpiredError("Secret has expired")

        # Decrypt the value
        try:
            decrypted_value = await self.encryption_service.decrypt(
                secret.encrypted_value,
                secret.encryption_key_id,
                secret.encryption_algorithm,
                secret.salt,
                secret.nonce,
            )
            return decrypted_value
        except Exception as e:
            await self._log_access(
                secret_id,
                accessor=accessor,
                service_name=service_name,
                success=False,
                error_message=f"Decryption failed: {e}",
            )
            raise

    async def update_secret(
        self,
        secret_id: str,
        name: Optional[str] = None,
        value: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        access_level: Optional[AccessLevel] = None,
        allowed_services: Optional[List[str]] = None,
        allowed_users: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
        rotation_interval_days: Optional[int] = None,
        auto_rotate: Optional[bool] = None,
        updated_by: Optional[str] = None,
    ) -> Secret:
        """Update secret with versioning and audit logging."""
        try:
            secret = await self.get_secret(secret_id)

            # Check write access
            if not await self._check_access(secret, updated_by, required_level=AccessLevel.READ_WRITE):
                raise AccessDeniedError("Write access denied to secret")

            # Store old values for audit
            old_values = {
                "name": secret.name,
                "description": secret.description,
                "access_level": secret.access_level.value,
                "expires_at": secret.expires_at.isoformat() if secret.expires_at else None,
            }

            # Update fields
            new_values = {}
            if name is not None:
                secret.name = name
                new_values["name"] = name

            if description is not None:
                secret.description = description
                new_values["description"] = description

            if tags is not None:
                secret.tags = tags
                new_values["tags"] = tags

            if metadata is not None:
                secret.secret_metadata = metadata
                new_values["metadata"] = metadata

            if access_level is not None:
                secret.access_level = access_level
                new_values["access_level"] = access_level.value

            if allowed_services is not None:
                secret.allowed_services = allowed_services
                new_values["allowed_services"] = allowed_services

            if allowed_users is not None:
                secret.allowed_users = allowed_users
                new_values["allowed_users"] = allowed_users

            if expires_at is not None:
                secret.expires_at = expires_at
                new_values["expires_at"] = expires_at.isoformat()

            if rotation_interval_days is not None:
                secret.rotation_interval_days = rotation_interval_days
                new_values["rotation_interval_days"] = rotation_interval_days

            if auto_rotate is not None:
                secret.auto_rotate = auto_rotate
                new_values["auto_rotate"] = auto_rotate

            # If value is being updated, encrypt and create new version
            if value is not None:
                encrypted_value, key_id, algorithm, salt, nonce = await self.encryption_service.encrypt(
                    value, secret.encryption_key_id
                )

                secret.encrypted_value = encrypted_value
                secret.salt = salt
                secret.nonce = nonce
                secret.version += 1

                # Create new version record
                version = SecretVersion(
                    secret_id=secret.id,
                    version_number=secret.version,
                    encrypted_value=encrypted_value,
                    encryption_key_id=key_id,
                    encryption_algorithm=algorithm,
                    salt=salt,
                    nonce=nonce,
                    metadata_snapshot=secret.secret_metadata,
                    created_by=updated_by,
                    change_reason="Value updated",
                )
                self.db.add(version)
                new_values["version"] = secret.version

            secret.updated_by = updated_by

            # Log audit event
            await self._log_audit(
                secret.id,
                AuditAction.UPDATE,
                actor=updated_by,
                old_values=old_values,
                new_values=new_values,
            )

            await self.db.commit()
            return secret

        except Exception as e:
            await self.db.rollback()
            raise

    async def rotate_secret(
        self,
        secret_id: str,
        new_value: str,
        rotated_by: Optional[str] = None,
        reason: str = "Manual rotation",
    ) -> Secret:
        """Rotate secret value with new encryption."""
        try:
            secret = await self.get_secret(secret_id)

            # Check admin access for rotation
            if not await self._check_access(secret, rotated_by, required_level=AccessLevel.ADMIN):
                raise AccessDeniedError("Admin access required for secret rotation")

            # Encrypt new value
            encrypted_value, key_id, algorithm, salt, nonce = await self.encryption_service.encrypt(
                new_value, secret.encryption_key_id
            )

            # Update secret
            secret.encrypted_value = encrypted_value
            secret.salt = salt
            secret.nonce = nonce
            secret.version += 1
            secret.last_rotated_at = datetime.utcnow()
            secret.updated_by = rotated_by

            # Create new version record
            version = SecretVersion(
                secret_id=secret.id,
                version_number=secret.version,
                encrypted_value=encrypted_value,
                encryption_key_id=key_id,
                encryption_algorithm=algorithm,
                salt=salt,
                nonce=nonce,
                metadata_snapshot=secret.secret_metadata,
                created_by=rotated_by,
                change_reason=reason,
            )
            self.db.add(version)

            # Log audit event
            await self._log_audit(
                secret.id,
                AuditAction.ROTATE,
                actor=rotated_by,
                details={"reason": reason, "new_version": secret.version},
            )

            await self.db.commit()
            return secret

        except Exception as e:
            await self.db.rollback()
            raise

    async def delete_secret(
        self,
        secret_id: str,
        deleted_by: Optional[str] = None,
        hard_delete: bool = False,
    ) -> None:
        """Delete secret (soft delete by default)."""
        try:
            secret = await self.get_secret(secret_id)

            # Check admin access for deletion
            if not await self._check_access(secret, deleted_by, required_level=AccessLevel.ADMIN):
                raise AccessDeniedError("Admin access required for secret deletion")

            if hard_delete:
                # Hard delete - remove from database
                await self.db.delete(secret)
                action = AuditAction.DELETE
            else:
                # Soft delete - mark as deleted
                secret.is_deleted = True
                secret.deleted_at = datetime.utcnow()
                secret.deleted_by = deleted_by
                secret.status = SecretStatus.INACTIVE
                action = AuditAction.DELETE

            # Log audit event
            await self._log_audit(
                secret.id,
                action,
                actor=deleted_by,
                details={"hard_delete": hard_delete},
            )

            await self.db.commit()

        except Exception as e:
            await self.db.rollback()
            raise

    async def list_secrets(
        self,
        namespace: Optional[str] = None,
        tenant_id: Optional[str] = None,
        secret_type: Optional[SecretType] = None,
        status: Optional[SecretStatus] = None,
        accessor: Optional[str] = None,
        service_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Secret]:
        """List secrets with filtering and access control."""
        query = select(Secret).where(Secret.is_deleted == False)

        # Apply filters
        if namespace:
            query = query.where(Secret.namespace == namespace)

        if tenant_id:
            query = query.where(Secret.tenant_id == tenant_id)

        if secret_type:
            query = query.where(Secret.secret_type == secret_type)

        if status:
            query = query.where(Secret.status == status)

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        secrets = result.scalars().all()

        # Filter by access control
        accessible_secrets = []
        for secret in secrets:
            if await self._check_access(secret, accessor, service_name, AccessLevel.READ_ONLY):
                accessible_secrets.append(secret)

        return accessible_secrets

    async def check_expiring_secrets(self, days_ahead: int = 7) -> List[Secret]:
        """Get secrets that will expire within specified days."""
        expiry_threshold = datetime.utcnow() + timedelta(days=days_ahead)

        result = await self.db.execute(
            select(Secret).where(
                and_(
                    Secret.expires_at <= expiry_threshold,
                    Secret.status == SecretStatus.ACTIVE,
                    Secret.is_deleted == False,
                )
            )
        )
        return result.scalars().all()

    async def check_rotation_due_secrets(self) -> List[Secret]:
        """Get secrets that are due for rotation."""
        current_time = datetime.utcnow()

        result = await self.db.execute(
            select(Secret).where(
                and_(
                    Secret.auto_rotate == True,
                    Secret.rotation_interval_days.isnot(None),
                    Secret.status == SecretStatus.ACTIVE,
                    Secret.is_deleted == False,
                    or_(
                        Secret.last_rotated_at.is_(None),
                        Secret.last_rotated_at + timedelta(days=Secret.rotation_interval_days) <= current_time,
                    ),
                )
            )
        )
        return result.scalars().all()
