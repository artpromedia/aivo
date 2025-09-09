"""Core services for Edge Bundler functionality."""
# flake8: noqa: E501
# ruff: noqa: ANN101, ANN204, I001  # Self annotations, init return type, import sorting
# pylint: disable=broad-exception-caught,W0718  # Exception catching is appropriate for robustness

import asyncio
import hashlib
import json
import os
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

import structlog
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Bundle,
    BundleAsset,
    BundleDownload,
    BundleStatus,
    CRDTMergeLog,
    CompressionType,
)
from app.schemas import (
    BundleManifest,
    BundleRequest,
    CRDTConfig,
    CRDTMergeRequest,
    CRDTMergeResponse,
    CRDTOperation,
)

logger = structlog.get_logger(__name__)


class BundleService:
    """Service for creating and managing offline lesson bundles."""

    def __init__(self) -> None:
        """Initialize the bundle service."""
        self.storage_path = Path(os.getenv("BUNDLE_STORAGE_PATH", "/tmp/bundles"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.signing_key_path = os.getenv("BUNDLE_SIGNING_KEY", "/etc/bundler/signing.key")
        self.max_concurrent_builds = int(os.getenv("MAX_CONCURRENT_BUILDS", "5"))
        self._build_semaphore = asyncio.Semaphore(self.max_concurrent_builds)

    async def create_bundle(
        self,
        request: BundleRequest,
        db: AsyncSession,
        _created_by: str | None = None,
    ) -> Bundle:
        """Create a new offline bundle."""
        # Generate bundle name if not provided
        bundle_name = (
            request.bundle_name or
            f"bundle_{request.learner_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )

        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(hours=request.offline_duration_hours)

        # Create bundle record
        bundle = Bundle(
            learner_id=request.learner_id,
            subjects=request.subjects,
            bundle_name=bundle_name,
            max_bundle_size=request.max_bundle_size,
            max_precache_size=request.max_precache_size,
            compression_type=request.compression_type,
            bundle_version=request.bundle_version,
            expires_at=expires_at,
            status=BundleStatus.PENDING,
        )

        db.add(bundle)
        await db.commit()
        await db.refresh(bundle)

        # Start background bundle creation
        asyncio.create_task(self._build_bundle_async(bundle.bundle_id, request, db))

        logger.info(
            "Bundle creation started",
            bundle_id=bundle.bundle_id,
            learner_id=request.learner_id,
            subjects=request.subjects,
        )

        return bundle

    async def _build_bundle_async(
        self,
        bundle_id: UUID,
        request: BundleRequest,
        db: AsyncSession,
    ) -> None:
        """Build bundle asynchronously."""
        async with self._build_semaphore:
            try:
                await self._update_bundle_status(bundle_id, BundleStatus.PROCESSING, db)

                # Create bundle directory
                bundle_dir = self.storage_path / str(bundle_id)
                bundle_dir.mkdir(parents=True, exist_ok=True)

                # Gather lessons and assets
                assets = await self._gather_content(request, bundle_dir)

                # Check size constraints
                total_size = sum(asset.file_size for asset in assets)
                precache_size = sum(asset.file_size for asset in assets if asset.is_precache)

                if total_size > request.max_bundle_size:
                    raise ValueError(
                        f"Bundle size ({total_size}) exceeds limit ({request.max_bundle_size})"
                    )

                if precache_size > request.max_precache_size:
                    raise ValueError(
                        f"Precache size ({precache_size}) exceeds limit "
                        f"({request.max_precache_size})"
                    )

                # Create manifest
                crdt_config = CRDTConfig(
                    enable_crdt=True,
                    vector_clock_node_id=f"bundle_{bundle_id}",
                    merge_strategy="last_writer_wins",
                    sync_granularity="lesson",
                )

                manifest = BundleManifest(
                    bundle_id=bundle_id,
                    version=request.bundle_version,
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(hours=request.offline_duration_hours),
                    learner_id=request.learner_id,
                    subjects=request.subjects,
                    compression_type=request.compression_type,
                    total_size=total_size,
                    precache_size=precache_size,
                    assets=assets,
                    crdt_config=crdt_config,
                    checksum="",  # Will be calculated after bundle creation
                )

                # Save manifest
                manifest_path = bundle_dir / "manifest.json"
                with open(manifest_path, "w", encoding="utf-8") as f:
                    f.write(manifest.json(indent=2))

                # Create tarball
                bundle_path = bundle_dir / f"{bundle_id}.tar.gz"
                await self._create_tarball(bundle_dir, bundle_path, request.compression_type)

                # Calculate checksums
                sha256_hash = await self._calculate_checksum(bundle_path)

                # Sign bundle if signing key exists
                is_signed = False
                signature_path = None
                if os.path.exists(self.signing_key_path):
                    signature_path = await self._sign_bundle(bundle_path)
                    is_signed = True

                # Update bundle record
                await self._update_bundle_completion(
                    bundle_id,
                    bundle_path=str(bundle_path),
                    manifest_path=str(manifest_path),
                    sha256_hash=sha256_hash,
                    actual_size=total_size,
                    precache_size=precache_size,
                    is_signed=is_signed,
                    signature_path=signature_path,
                    lesson_count=len([a for a in assets if a.asset_type == "lesson"]),
                    asset_count=len(assets),
                    adapter_count=len([a for a in assets if a.asset_type == "adapter"]),
                    db=db,
                )

                # Store asset records
                await self._store_asset_records(bundle_id, assets, db)

                logger.info(
                    "Bundle creation completed",
                    bundle_id=bundle_id,
                    size=total_size,
                    assets=len(assets),
                )

            except Exception as e:  # pylint: disable=broad-exception-caught,W0718
                logger.error("Bundle creation failed", bundle_id=bundle_id, error=str(e))
                await self._update_bundle_status(
                    bundle_id, BundleStatus.FAILED, db, error_message=str(e)
                )

    async def _gather_content(self, request: BundleRequest, bundle_dir: Path) -> list:
        """Gather lessons and assets for the bundle."""
        # This would integrate with lesson registry and content services
        # For now, create mock content structure

        assets = []
        content_dir = bundle_dir / "content"
        content_dir.mkdir(exist_ok=True)

        # Mock lesson content for each subject
        for subject in request.subjects:
            subject_dir = content_dir / subject
            subject_dir.mkdir(exist_ok=True)

            # Create mock lesson files
            for i in range(3):  # 3 lessons per subject
                lesson_name = f"lesson_{i+1}.json"
                lesson_path = subject_dir / lesson_name

                lesson_content = {
                    "id": f"{subject}_lesson_{i+1}",
                    "title": f"Lesson {i+1} - {subject.title()}",
                    "content": f"Mock content for {subject} lesson {i+1}",
                    "crdt_version": "1.0.0",
                    "last_modified": datetime.utcnow().isoformat(),
                }

                with open(lesson_path, "w", encoding="utf-8") as f:
                    json.dump(lesson_content, f, indent=2)

                assets.append(type('Asset', (), {
                    'asset_type': 'lesson',
                    'asset_name': lesson_name,
                    'file_path': str(lesson_path.relative_to(bundle_dir)),
                    'file_size': lesson_path.stat().st_size,
                    'content_id': lesson_content["id"],
                    'subject': subject,
                    'is_precache': i == 0,  # First lesson is precached
                    'priority': 10 if i == 0 else 100,
                })())

            # Add subject adapter if requested
            if request.include_adapters:
                adapter_name = f"{subject}_adapter.js"
                adapter_path = subject_dir / adapter_name

                adapter_content = f"""
// Adapter for {subject} lessons
class {subject.title()}Adapter {{
    constructor() {{
        this.subject = '{subject}';
        this.version = '1.0.0';
    }}

    async loadLesson(lessonId) {{
        // Load lesson content with CRDT support
        return await this.crdtLoader.load(lessonId);
    }}

    async saveProgress(lessonId, progress) {{
        // Save with CRDT merge capability
        return await this.crdtStore.merge(lessonId, progress);
    }}
}}

export default {subject.title()}Adapter;
"""

                with open(adapter_path, "w", encoding="utf-8") as f:
                    f.write(adapter_content)

                assets.append(type('Asset', (), {
                    'asset_type': 'adapter',
                    'asset_name': adapter_name,
                    'file_path': str(adapter_path.relative_to(bundle_dir)),
                    'file_size': adapter_path.stat().st_size,
                    'content_id': f"{subject}_adapter",
                    'subject': subject,
                    'is_precache': True,  # Adapters are always precached
                    'priority': 1,
                })())

        return assets

    async def _create_tarball(
        self, source_dir: Path, output_path: Path, compression: CompressionType
    ) -> None:
        """Create compressed tarball of bundle content."""
        compression_map = {
            CompressionType.GZIP: "gz",
            CompressionType.BROTLI: "bz2",  # Using bz2 as fallback for brotli
            CompressionType.ZSTD: "gz",     # Using gz as fallback for zstd
        }

        mode = f"w:{compression_map[compression]}"

        with tarfile.open(output_path, mode) as tar:
            tar.add(source_dir / "content", arcname="content")
            tar.add(source_dir / "manifest.json", arcname="manifest.json")

    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of bundle file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    async def _sign_bundle(self, bundle_path: Path) -> str:
        """Sign bundle with private key (mock implementation)."""
        # In production, use proper cryptographic signing
        signature_path = bundle_path.with_suffix(".sig")

        # Mock signature creation
        with open(signature_path, "w", encoding="utf-8") as f:
            f.write(f"MOCK_SIGNATURE_{bundle_path.name}_{datetime.utcnow().isoformat()}")

        return str(signature_path)

    async def _update_bundle_status(
        self,
        bundle_id: UUID,
        status: BundleStatus,
        db: AsyncSession,
        error_message: str | None = None,
    ) -> None:
        """Update bundle status."""
        update_data = {"status": status, "updated_at": datetime.utcnow()}

        if status == BundleStatus.PROCESSING:
            update_data["processing_started_at"] = datetime.utcnow()
        elif status in [BundleStatus.COMPLETED, BundleStatus.FAILED]:
            update_data["processing_completed_at"] = datetime.utcnow()

        if error_message:
            update_data["error_message"] = error_message

        await db.execute(
            update(Bundle)
            .where(Bundle.bundle_id == bundle_id)
            .values(**update_data)
        )
        await db.commit()

    async def _update_bundle_completion(
        self,
        bundle_id: UUID,
        bundle_path: str,
        manifest_path: str,
        sha256_hash: str,
        actual_size: int,
        precache_size: int,
        is_signed: bool,
        signature_path: str | None,
        lesson_count: int,
        asset_count: int,
        adapter_count: int,
        db: AsyncSession,
    ) -> None:
        """Update bundle with completion data."""
        await db.execute(
            update(Bundle)
            .where(Bundle.bundle_id == bundle_id)
            .values(
                status=BundleStatus.COMPLETED,
                bundle_path=bundle_path,
                manifest_path=manifest_path,
                sha256_hash=sha256_hash,
                actual_size=actual_size,
                precache_size=precache_size,
                is_signed=is_signed,
                signature_path=signature_path,
                lesson_count=lesson_count,
                asset_count=asset_count,
                adapter_count=adapter_count,
                processing_completed_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        await db.commit()

    async def _store_asset_records(self, bundle_id: UUID, assets: list, db: AsyncSession) -> None:
        """Store individual asset records."""
        for asset in assets:
            asset_record = BundleAsset(
                bundle_id=bundle_id,
                asset_type=asset.asset_type,
                asset_name=asset.asset_name,
                file_path=asset.file_path,
                file_size=asset.file_size,
                content_id=asset.content_id,
                subject=asset.subject,
                is_precache=asset.is_precache,
                priority=asset.priority,
            )
            db.add(asset_record)

        await db.commit()

    async def get_bundle(self, bundle_id: UUID, db: AsyncSession) -> Bundle | None:
        """Get bundle by ID."""
        result = await db.execute(
            select(Bundle).where(Bundle.bundle_id == bundle_id)
        )
        return result.scalar_one_or_none()

    async def list_bundles(
        self,
        learner_id: UUID | None = None,
        status: BundleStatus | None = None,
        limit: int = 50,
        offset: int = 0,
        db: AsyncSession = None,
    ) -> tuple[list[Bundle], int]:
        """List bundles with optional filtering."""
        query = select(Bundle)
        count_query = select(Bundle.bundle_id)

        if learner_id:
            query = query.where(Bundle.learner_id == learner_id)
            count_query = count_query.where(Bundle.learner_id == learner_id)

        if status:
            query = query.where(Bundle.status == status)
            count_query = count_query.where(Bundle.status == status)

        query = query.order_by(Bundle.created_at.desc()).limit(limit).offset(offset)

        result = await db.execute(query)
        bundles = result.scalars().all()

        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        return bundles, total


class CRDTService:
    """Service for handling CRDT operations and conflict resolution."""

    async def merge_operations(
        self,
        request: CRDTMergeRequest,
        db: AsyncSession,
    ) -> CRDTMergeResponse:
        """Merge CRDT operations from offline client."""
        accepted_operations = []
        conflicted_operations = []
        server_operations = []

        # Process each operation
        for operation in request.operations:
            try:
                # Check for conflicts using vector clocks
                conflict = await self._detect_conflict(operation, db)

                if conflict:
                    conflicted_operations.append(operation.operation_id)
                    # Apply conflict resolution
                    resolved_op = await self._resolve_conflict(operation, conflict, db)
                    if resolved_op:
                        server_operations.append(resolved_op)
                else:
                    # Accept operation
                    accepted_operations.append(operation.operation_id)
                    await self._apply_operation(
                        operation, request.bundle_id, request.learner_id, db
                    )

            except Exception as e:  # pylint: disable=broad-exception-caught,W0718
                logger.error("Failed to process CRDT operation",
                           operation_id=operation.operation_id, error=str(e))
                conflicted_operations.append(operation.operation_id)

        # Update vector clock
        updated_vector_clock = await self._update_vector_clock(
            request.client_vector_clock, request.learner_id, db
        )

        return CRDTMergeResponse(
            accepted_operations=accepted_operations,
            conflicted_operations=conflicted_operations,
            server_operations=server_operations,
            updated_vector_clock=updated_vector_clock,
            conflicts_resolved=len([
                op for op in server_operations if op.operation_type == "merge"
            ]),
        )

    async def _detect_conflict(self, operation: CRDTOperation, db: AsyncSession) -> dict | None:
        """Detect if operation conflicts with existing state."""
        # Check for concurrent modifications using vector clocks
        result = await db.execute(
            select(CRDTMergeLog)
            .where(
                and_(
                    CRDTMergeLog.content_id == operation.content_id,  # pylint: disable=no-member
                    CRDTMergeLog.operation_type.in_(["create", "update"]),  # pylint: disable=no-member
                    CRDTMergeLog.created_at > operation.timestamp - timedelta(minutes=5),  # pylint: disable=no-member
                )
            )
        )

        existing_ops = result.scalars().all()

        for existing_op in existing_ops:
            # Compare vector clocks to detect concurrent modifications
            if self._is_concurrent(operation.vector_clock, existing_op.vector_clock):
                return {
                    "existing_operation": existing_op,
                    "conflict_type": "concurrent_modification",
                }

        return None

    def _is_concurrent(self, clock1: dict[str, int], clock2: dict[str, int]) -> bool:
        """Check if two vector clocks represent concurrent operations."""
        # Two clocks are concurrent if neither dominates the other
        clock1_dominates = all(
            clock1.get(node, 0) >= clock2.get(node, 0) for node in clock2
        )
        clock2_dominates = all(
            clock2.get(node, 0) >= clock1.get(node, 0) for node in clock1
        )

        return not (clock1_dominates or clock2_dominates)

    async def _resolve_conflict(
        self,
        operation: CRDTOperation,
        conflict: dict,
        _db: AsyncSession,
    ) -> CRDTOperation | None:
        """Resolve CRDT conflict using last-writer-wins strategy."""
        existing_op = conflict["existing_operation"]

        # Use timestamp-based resolution (last writer wins)
        if operation.timestamp > existing_op.created_at:
            # New operation wins, create merge operation
            merge_operation = CRDTOperation(
                operation_id=UUID(int=0),  # Generate new UUID
                operation_type="merge",
                content_type=operation.content_type,
                content_id=operation.content_id,
                vector_clock=self._merge_vector_clocks(
                    operation.vector_clock, existing_op.vector_clock
                ),
                operation_data={
                    "winner": operation.operation_data,
                    "loser": existing_op.operation_data,
                    "resolution_strategy": "last_writer_wins",
                },
                timestamp=datetime.utcnow(),
            )

            return merge_operation

        return None

    def _merge_vector_clocks(
        self, clock1: dict[str, int], clock2: dict[str, int]
    ) -> dict[str, int]:
        """Merge two vector clocks by taking the maximum of each component."""
        all_nodes = set(clock1.keys()) | set(clock2.keys())
        return {
            node: max(clock1.get(node, 0), clock2.get(node, 0))
            for node in all_nodes
        }

    async def _apply_operation(
        self,
        operation: CRDTOperation,
        bundle_id: UUID,
        learner_id: UUID,
        db: AsyncSession,
    ) -> None:
        """Apply CRDT operation to the database."""
        merge_log = CRDTMergeLog(
            bundle_id=bundle_id,
            learner_id=learner_id,
            operation_type=operation.operation_type,
            content_type=operation.content_type,
            content_id=operation.content_id,
            vector_clock=operation.vector_clock,
            operation_data=operation.operation_data,
            is_applied=True,
        )

        db.add(merge_log)
        await db.commit()

    async def _update_vector_clock(
        self,
        client_clock: dict[str, int],
        learner_id: UUID,
        _db: AsyncSession,
    ) -> dict[str, int]:
        """Update and return the latest vector clock for the client."""
        # In production, this would maintain per-client vector clocks
        # For now, return an incremented clock
        server_node = f"server_{learner_id}"
        updated_clock = client_clock.copy()
        updated_clock[server_node] = updated_clock.get(server_node, 0) + 1

        return updated_clock


class DownloadService:
    """Service for handling bundle downloads."""

    async def create_download(
        self,
        bundle_id: UUID,
        learner_id: UUID,
        user_agent: str | None,
        client_ip: str | None,
        client_version: str | None,
        db: AsyncSession,
    ) -> BundleDownload:
        """Create a new download record."""
        download = BundleDownload(
            bundle_id=bundle_id,
            learner_id=learner_id,
            user_agent=user_agent,
            client_ip=client_ip,
            client_version=client_version,
        )

        db.add(download)
        await db.commit()
        await db.refresh(download)

        return download

    async def complete_download(
        self,
        download_id: UUID,
        download_size: int,
        db: AsyncSession,
    ) -> None:
        """Mark download as completed."""
        await db.execute(
            update(BundleDownload)
            .where(BundleDownload.download_id == download_id)
            .values(
                is_completed=True,
                download_completed_at=datetime.utcnow(),
                download_size=download_size,
            )
        )
        await db.commit()
