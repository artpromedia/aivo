"""SHA-256 audit chain implementation for evidence tracking."""

import hashlib
import json
import logging
import uuid
from datetime import datetime
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import EvidenceAuditEntry, EvidenceUpload

logger = logging.getLogger(__name__)


class AuditChain:
    """SHA-256 audit chain for evidence integrity tracking."""

    def __init__(
        self,
        private_key_path: str | None = None,
        public_key_path: str | None = None,
    ) -> None:
        """Initialize audit chain.

        Args:
            private_key_path: Path to RSA private key for signing
            public_key_path: Path to RSA public key for verification
        """
        self.private_key = None
        self.public_key = None

        if private_key_path:
            self._load_private_key(private_key_path)
        if public_key_path:
            self._load_public_key(public_key_path)

    def _load_private_key(self, key_path: str) -> None:
        """Load RSA private key for signing."""
        try:
            with open(key_path, "rb") as key_file:
                self.private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                )
            logger.info("Loaded private key for audit signing")
        except Exception as e:
            logger.error("Failed to load private key: %s", e)

    def _load_public_key(self, key_path: str) -> None:
        """Load RSA public key for verification."""
        try:
            with open(key_path, "rb") as key_file:
                self.public_key = serialization.load_pem_public_key(
                    key_file.read(),
                )
            logger.info("Loaded public key for audit verification")
        except Exception as e:
            logger.error("Failed to load public key: %s", e)

    def generate_content_hash(self, data: Any) -> str:
        """Generate SHA-256 hash of content.

        Args:
            data: Data to hash (will be JSON serialized)

        Returns:
            Hex string of SHA-256 hash
        """
        if isinstance(data, str | bytes):
            content = data if isinstance(data, bytes) else data.encode("utf-8")
        else:
            # Serialize complex data structures deterministically
            content = json.dumps(
                data,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")

        hash_obj = hashlib.sha256()
        hash_obj.update(content)
        return hash_obj.hexdigest()

    def generate_chain_hash(
        self,
        content_hash: str,
        previous_hash: str | None,
        timestamp: datetime,
        action_details: dict[str, Any],
    ) -> str:
        """Generate chain hash linking to previous entry.

        Args:
            content_hash: Hash of the content
            previous_hash: Hash of previous chain entry
            timestamp: Timestamp of the action
            action_details: Details of the action

        Returns:
            Hex string of chain hash
        """
        chain_data = {
            "content_hash": content_hash,
            "previous_hash": previous_hash or "",
            "timestamp": timestamp.isoformat(),
            "action_details": action_details,
        }

        chain_content = json.dumps(
            chain_data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

        hash_obj = hashlib.sha256()
        hash_obj.update(chain_content)
        return hash_obj.hexdigest()

    def sign_entry(self, chain_hash: str) -> str | None:
        """Sign audit entry with RSA private key.

        Args:
            chain_hash: Chain hash to sign

        Returns:
            Base64 encoded signature or None if no private key
        """
        if not self.private_key:
            return None

        try:
            signature = self.private_key.sign(
                chain_hash.encode("utf-8"),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )

            import base64

            return base64.b64encode(signature).decode("utf-8")

        except Exception as e:
            logger.error("Failed to sign audit entry: %s", e)
            return None

    def verify_signature(self, chain_hash: str, signature: str) -> bool:
        """Verify audit entry signature.

        Args:
            chain_hash: Chain hash that was signed
            signature: Base64 encoded signature

        Returns:
            True if signature is valid
        """
        if not self.public_key or not signature:
            return False

        try:
            import base64

            signature_bytes = base64.b64decode(signature.encode("utf-8"))

            self.public_key.verify(
                signature_bytes,
                chain_hash.encode("utf-8"),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True

        except Exception as e:
            logger.error("Signature verification failed: %s", e)
            return False

    async def create_audit_entry(
        self,
        db: AsyncSession,
        upload_id: uuid.UUID,
        learner_id: uuid.UUID,
        action_type: str,
        action_details: dict[str, Any],
        performed_by: uuid.UUID,
        content: Any | None = None,
    ) -> EvidenceAuditEntry:
        """Create new audit chain entry.

        Args:
            db: Database session
            upload_id: ID of evidence upload
            learner_id: ID of learner
            action_type: Type of action being audited
            action_details: Details of the action
            performed_by: ID of user performing action
            content: Optional content to hash

        Returns:
            Created audit entry
        """
        # Generate content hash
        if content is not None:
            content_hash = self.generate_content_hash(content)
        else:
            content_hash = self.generate_content_hash(action_details)

        # Get previous hash from chain
        previous_hash = await self._get_latest_chain_hash(db, learner_id)

        # Generate timestamp
        timestamp = datetime.utcnow()

        # Generate chain hash
        chain_hash = self.generate_chain_hash(
            content_hash,
            previous_hash,
            timestamp,
            action_details,
        )

        # Sign the entry
        signature = self.sign_entry(chain_hash)

        # Create audit entry
        audit_entry = EvidenceAuditEntry(
            upload_id=upload_id,
            learner_id=learner_id,
            action_type=action_type,
            action_details=action_details,
            performed_by=performed_by,
            content_hash=content_hash,
            previous_hash=previous_hash,
            chain_hash=chain_hash,
            signature=signature,
        )

        db.add(audit_entry)
        await db.commit()

        logger.info(
            "Created audit entry %s for upload %s (action: %s)",
            audit_entry.id,
            upload_id,
            action_type,
        )

        return audit_entry

    async def _get_latest_chain_hash(
        self,
        db: AsyncSession,
        learner_id: uuid.UUID,
    ) -> str | None:
        """Get the latest chain hash for a learner.

        Args:
            db: Database session
            learner_id: ID of learner

        Returns:
            Latest chain hash or None if no entries
        """
        result = await db.execute(
            select(EvidenceAuditEntry.chain_hash)
            .where(EvidenceAuditEntry.learner_id == learner_id)
            .order_by(desc(EvidenceAuditEntry.timestamp))
            .limit(1),
        )

        latest_hash = result.scalar_one_or_none()
        return latest_hash

    async def verify_chain_integrity(
        self,
        db: AsyncSession,
        learner_id: uuid.UUID,
        verify_signatures: bool = True,
    ) -> dict[str, Any]:
        """Verify integrity of audit chain for a learner.

        Args:
            db: Database session
            learner_id: ID of learner
            verify_signatures: Whether to verify RSA signatures

        Returns:
            Verification results
        """
        # Get all audit entries for learner, ordered by timestamp
        result = await db.execute(
            select(EvidenceAuditEntry)
            .where(EvidenceAuditEntry.learner_id == learner_id)
            .order_by(EvidenceAuditEntry.timestamp),
        )
        entries = result.scalars().all()

        if not entries:
            return {
                "valid": True,
                "total_entries": 0,
                "verified_entries": 0,
                "broken_links": [],
                "invalid_signatures": [],
                "errors": [],
            }

        verification_results = {
            "valid": True,
            "total_entries": len(entries),
            "verified_entries": 0,
            "broken_links": [],
            "invalid_signatures": [],
            "errors": [],
        }

        previous_hash = None

        for i, entry in enumerate(entries):
            try:
                # Verify chain linkage
                expected_chain_hash = self.generate_chain_hash(
                    entry.content_hash,
                    previous_hash,
                    entry.timestamp,
                    entry.action_details,
                )

                if entry.chain_hash != expected_chain_hash:
                    verification_results["valid"] = False
                    verification_results["broken_links"].append(
                        {
                            "entry_id": str(entry.id),
                            "position": i,
                            "expected_hash": expected_chain_hash,
                            "actual_hash": entry.chain_hash,
                        }
                    )
                    continue

                # Verify signature if available
                if verify_signatures and entry.signature:
                    if not self.verify_signature(entry.chain_hash, entry.signature):
                        verification_results["valid"] = False
                        verification_results["invalid_signatures"].append(
                            {
                                "entry_id": str(entry.id),
                                "position": i,
                            }
                        )
                        continue

                # Check previous hash linkage
                if entry.previous_hash != previous_hash:
                    verification_results["valid"] = False
                    verification_results["broken_links"].append(
                        {
                            "entry_id": str(entry.id),
                            "position": i,
                            "expected_previous": previous_hash,
                            "actual_previous": entry.previous_hash,
                        }
                    )
                    continue

                verification_results["verified_entries"] += 1
                previous_hash = entry.chain_hash

            except Exception as e:
                verification_results["valid"] = False
                verification_results["errors"].append(
                    {
                        "entry_id": str(entry.id),
                        "position": i,
                        "error": str(e),
                    }
                )

        logger.info(
            "Chain verification for learner %s: %s (%d/%d entries verified)",
            learner_id,
            "VALID" if verification_results["valid"] else "INVALID",
            verification_results["verified_entries"],
            verification_results["total_entries"],
        )

        return verification_results

    async def get_audit_trail(
        self,
        db: AsyncSession,
        upload_id: uuid.UUID | None = None,
        learner_id: uuid.UUID | None = None,
        action_type: str | None = None,
        limit: int = 100,
    ) -> list[EvidenceAuditEntry]:
        """Get audit trail entries with optional filters.

        Args:
            db: Database session
            upload_id: Optional upload ID filter
            learner_id: Optional learner ID filter
            action_type: Optional action type filter
            limit: Maximum number of entries to return

        Returns:
            List of audit entries
        """
        query = select(EvidenceAuditEntry).order_by(
            desc(EvidenceAuditEntry.timestamp),
        )

        if upload_id:
            query = query.where(EvidenceAuditEntry.upload_id == upload_id)

        if learner_id:
            query = query.where(EvidenceAuditEntry.learner_id == learner_id)

        if action_type:
            query = query.where(EvidenceAuditEntry.action_type == action_type)

        query = query.limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    async def export_audit_chain(
        self,
        db: AsyncSession,
        learner_id: uuid.UUID,
        include_content: bool = False,
    ) -> dict[str, Any]:
        """Export complete audit chain for a learner.

        Args:
            db: Database session
            learner_id: ID of learner
            include_content: Whether to include full content hashes

        Returns:
            Exportable audit chain data
        """
        # Get all entries for learner
        entries = await self.get_audit_trail(
            db,
            learner_id=learner_id,
            limit=10000,  # Large limit for complete export
        )

        # Verify chain integrity
        verification = await self.verify_chain_integrity(db, learner_id)

        # Format for export
        export_data = {
            "learner_id": str(learner_id),
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_entries": len(entries),
            "chain_verification": verification,
            "entries": [],
        }

        for entry in reversed(entries):  # Chronological order
            entry_data = {
                "id": str(entry.id),
                "upload_id": str(entry.upload_id),
                "action_type": entry.action_type,
                "action_details": entry.action_details,
                "performed_by": str(entry.performed_by),
                "timestamp": entry.timestamp.isoformat(),
                "chain_hash": entry.chain_hash,
                "previous_hash": entry.previous_hash,
                "has_signature": bool(entry.signature),
            }

            if include_content:
                entry_data["content_hash"] = entry.content_hash
                entry_data["signature"] = entry.signature

            export_data["entries"].append(entry_data)

        # Generate export hash for integrity
        export_data["export_hash"] = self.generate_content_hash(export_data["entries"])

        logger.info(
            "Exported audit chain for learner %s: %d entries",
            learner_id,
            len(entries),
        )

        return export_data

    async def audit_upload_action(
        self,
        db: AsyncSession,
        upload: EvidenceUpload,
        action_type: str,
        performed_by: uuid.UUID,
        additional_details: dict[str, Any] | None = None,
    ) -> EvidenceAuditEntry:
        """Create audit entry for upload-related action.

        Args:
            db: Database session
            upload: Evidence upload
            action_type: Type of action
            performed_by: ID of user performing action
            additional_details: Additional action details

        Returns:
            Created audit entry
        """
        action_details = {
            "original_filename": upload.original_filename,
            "file_type": upload.file_type,
            "file_size": upload.file_size,
            "s3_key": upload.s3_key,
            "upload_timestamp": upload.upload_timestamp.isoformat(),
        }

        if additional_details:
            action_details.update(additional_details)

        return await self.create_audit_entry(
            db=db,
            upload_id=upload.id,
            learner_id=upload.learner_id,
            action_type=action_type,
            action_details=action_details,
            performed_by=performed_by,
            content=upload.content_hash,
        )

    async def get_audit_statistics(
        self,
        db: AsyncSession,
        learner_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Get audit chain statistics.

        Args:
            db: Database session
            learner_id: Optional learner filter

        Returns:
            Statistics dictionary
        """
        query = select(EvidenceAuditEntry)

        if learner_id:
            query = query.where(EvidenceAuditEntry.learner_id == learner_id)

        result = await db.execute(query)
        entries = result.scalars().all()

        if not entries:
            return {
                "total_entries": 0,
                "unique_learners": 0,
                "action_types": {},
                "entries_with_signatures": 0,
                "chain_integrity_rate": 0.0,
            }

        # Calculate statistics
        unique_learners = len({entry.learner_id for entry in entries})
        action_types = {}
        signed_entries = 0

        for entry in entries:
            action_types[entry.action_type] = action_types.get(entry.action_type, 0) + 1
            if entry.signature:
                signed_entries += 1

        # Check chain integrity for sample of learners (if not filtered)
        integrity_rate = 1.0  # Default to valid if single learner
        if not learner_id and unique_learners > 0:
            sample_learners = list({entry.learner_id for entry in entries})[:10]
            valid_chains = 0

            for sample_learner in sample_learners:
                verification = await self.verify_chain_integrity(
                    db,
                    sample_learner,
                    verify_signatures=False,  # Skip signatures for speed
                )
                if verification["valid"]:
                    valid_chains += 1

            integrity_rate = valid_chains / len(sample_learners)

        return {
            "total_entries": len(entries),
            "unique_learners": unique_learners,
            "action_types": action_types,
            "entries_with_signatures": signed_entries,
            "signature_rate": signed_entries / len(entries),
            "chain_integrity_rate": integrity_rate,
        }
