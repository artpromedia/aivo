"""
Business logic services for ink capture functionality.

This module contains the core business logic for processing digital ink
strokes, managing sessions, storing data in S3, and publishing events.
"""
import json
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import boto3
import structlog
from botocore.exceptions import ClientError, NoCredentialsError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .models import InkPage, InkSession
from .schemas import (
    InkPageData,
    InkReadyEvent,
    StrokeRequest,
    StrokeResponse,
)

logger = structlog.get_logger(__name__)


class S3StorageService:
    """Service for storing ink data in AWS S3."""

    def __init__(self) -> None:
        """Initialize S3 client with configuration."""
        try:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region,
            )
            self.bucket_name = settings.s3_bucket_name
            self.key_prefix = settings.s3_key_prefix
        except NoCredentialsError:
            logger.warning(
                "AWS credentials not found, S3 functionality disabled"
            )
            self.s3_client = None

    def generate_s3_key(
        self, session_id: UUID, page_id: UUID, learner_id: UUID
    ) -> str:
        """Generate S3 key for ink page data."""
        date_str = datetime.utcnow().strftime("%Y/%m/%d")
        return (
            f"{self.key_prefix}{date_str}/learner_{learner_id}/"
            f"session_{session_id}/page_{page_id}.ndjson"
        )

    async def store_page_data(
        self, s3_key: str, page_data: InkPageData
    ) -> bool:
        """
        Store ink page data as NDJSON in S3.

        Args:
            s3_key: S3 object key for storage
            page_data: Page data to store

        Returns:
            True if successful, False otherwise
        """
        if not self.s3_client:
            logger.error("S3 client not available, skipping storage")
            return False

        try:
            # Convert page data to NDJSON format
            ndjson_data = page_data.model_dump_json() + "\n"

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=ndjson_data.encode("utf-8"),
                ContentType="application/x-ndjson",
                Metadata={
                    "session_id": str(page_data.session_id),
                    "learner_id": str(page_data.learner_id),
                    "subject": page_data.subject,
                    "page_number": str(page_data.page_number),
                    "stroke_count": str(len(page_data.strokes)),
                },
            )

            logger.info(
                "Stored page data in S3",
                s3_key=s3_key,
                session_id=page_data.session_id,
                stroke_count=len(page_data.strokes),
            )
            return True

        except ClientError as e:
            logger.error(
                "Failed to store page data in S3",
                error=str(e),
                s3_key=s3_key,
                session_id=page_data.session_id,
            )
            return False


class EventPublishingService:
    """Service for publishing ink recognition events."""

    def __init__(self) -> None:
        """Initialize event publishing service."""
        self.event_service_url = settings.event_service_url
        self.enabled = settings.enable_events

    async def publish_ink_ready_event(
        self,
        session_id: UUID,
        page_id: UUID,
        learner_id: UUID,
        subject: str,
        s3_key: str,
        stroke_count: int,
    ) -> UUID | None:
        """
        Publish INK_READY event for recognition processing.

        Args:
            session_id: Session identifier
            page_id: Page identifier
            learner_id: Learner ID
            subject: Subject area
            s3_key: S3 storage key
            stroke_count: Number of strokes

        Returns:
            Recognition job ID if successful, None otherwise
        """
        if not self.enabled:
            logger.info("Event publishing disabled, skipping INK_READY event")
            return None

        try:
            event = InkReadyEvent(
                session_id=session_id,
                page_id=page_id,
                learner_id=learner_id,
                subject=subject,
                s3_key=s3_key,
                stroke_count=stroke_count,
            )

            # In a real implementation, this would make an HTTP request
            # to the event service or publish to a message queue
            recognition_job_id = uuid4()

            logger.info(
                "Published INK_READY event",
                event_type=event.event_type,
                session_id=session_id,
                page_id=page_id,
                recognition_job_id=recognition_job_id,
            )

            return recognition_job_id

        except Exception as e:
            logger.error(
                "Failed to publish INK_READY event",
                error=str(e),
                session_id=session_id,
                page_id=page_id,
            )
            return None


class ConsentGateService:
    """Service for validating content consent and media policies."""

    @staticmethod
    async def validate_consent(
        learner_id: UUID, subject: str, metadata: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """
        Validate learner consent for data collection.

        Args:
            learner_id: Learner identifier
            subject: Subject area
            metadata: Additional metadata

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not settings.enable_consent_gate:
            return True, None

        # In a real implementation, this would check:
        # - Learner consent records
        # - Age verification
        # - Parental consent if required
        # - Subject-specific permissions

        logger.info(
            "Validating consent",
            learner_id=learner_id,
            subject=subject,
        )

        # Mock validation - always pass for now
        return True, None

    @staticmethod
    async def validate_media_policy(
        stroke_request: StrokeRequest,
    ) -> tuple[bool, str | None]:
        """
        Validate content against media policies.

        Args:
            stroke_request: Stroke submission request

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not settings.enable_media_gate:
            return True, None

        # In a real implementation, this would:
        # - Check for inappropriate content patterns
        # - Validate stroke data integrity
        # - Apply content filtering rules
        # - Check for spam or abuse patterns

        # Basic validation: check stroke counts and dimensions
        if len(stroke_request.strokes) > settings.max_strokes_per_request:
            return False, "Too many strokes in request"

        for stroke in stroke_request.strokes:
            if len(stroke.points) > settings.max_points_per_stroke:
                return False, f"Stroke {stroke.stroke_id} has too many points"

        logger.info(
            "Media policy validation passed",
            session_id=stroke_request.session_id,
            stroke_count=len(stroke_request.strokes),
        )

        return True, None


class InkCaptureService:
    """Main service for processing ink capture requests."""

    def __init__(self) -> None:
        """Initialize ink capture service with dependencies."""
        self.storage_service = S3StorageService()
        self.event_service = EventPublishingService()
        self.consent_service = ConsentGateService()

    async def get_or_create_session(
        self,
        session_id: UUID,
        learner_id: UUID,
        subject: str,
        db: AsyncSession,
    ) -> InkSession:
        """
        Get existing session or create a new one.

        Args:
            session_id: Session identifier
            learner_id: Learner ID
            subject: Subject area
            db: Database session

        Returns:
            InkSession model instance
        """
        # Check if session exists
        result = await db.execute(
            select(InkSession).where(InkSession.session_id == session_id)
        )
        existing_session = result.scalar_one_or_none()

        if existing_session:
            # Update last activity
            await db.execute(
                update(InkSession)
                .where(InkSession.session_id == session_id)
                .values(last_activity=datetime.utcnow())
            )
            await db.commit()
            return existing_session

        # Create new session
        new_session = InkSession(
            session_id=session_id,
            learner_id=learner_id,
            subject=subject,
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)

        logger.info(
            "Created new ink session",
            session_id=session_id,
            learner_id=learner_id,
            subject=subject,
        )

        return new_session

    async def process_strokes(
        self, stroke_request: StrokeRequest, db: AsyncSession
    ) -> StrokeResponse:
        """
        Process submitted ink strokes.

        Args:
            stroke_request: Stroke submission request
            db: Database session

        Returns:
            StrokeResponse with processing results

        Raises:
            ValueError: If validation fails
            RuntimeError: If processing fails
        """
        # Validate consent and media policies
        consent_valid, consent_error = (
            await self.consent_service.validate_consent(
                stroke_request.learner_id,
                stroke_request.subject,
                stroke_request.metadata,
            )
        )
        if not consent_valid:
            raise ValueError(f"Consent validation failed: {consent_error}")

        media_valid, media_error = (
            await self.consent_service.validate_media_policy(stroke_request)
        )
        if not media_valid:
            raise ValueError(f"Media policy validation failed: {media_error}")

        # Get or create session
        await self.get_or_create_session(
            stroke_request.session_id,
            stroke_request.learner_id,
            stroke_request.subject,
            db,
        )

        # Generate page ID and S3 key
        page_id = uuid4()
        s3_key = self.storage_service.generate_s3_key(
            stroke_request.session_id, page_id, stroke_request.learner_id
        )

        # Create page data structure
        page_data = InkPageData(
            page_id=page_id,
            session_id=stroke_request.session_id,
            learner_id=stroke_request.learner_id,
            subject=stroke_request.subject,
            page_number=stroke_request.page_number,
            canvas_width=stroke_request.canvas_width,
            canvas_height=stroke_request.canvas_height,
            strokes=stroke_request.strokes,
            metadata=stroke_request.metadata,
        )

        # Store in S3
        storage_success = await self.storage_service.store_page_data(
            s3_key, page_data
        )
        if not storage_success:
            raise RuntimeError("Failed to store page data in S3")

        # Create database record
        ink_page = InkPage(
            page_id=page_id,
            session_id=stroke_request.session_id,
            learner_id=stroke_request.learner_id,
            page_number=stroke_request.page_number,
            subject=stroke_request.subject,
            s3_key=s3_key,
            canvas_width=stroke_request.canvas_width,
            canvas_height=stroke_request.canvas_height,
            stroke_count=len(stroke_request.strokes),
            metadata_json=json.dumps(stroke_request.metadata),
        )
        db.add(ink_page)

        # Update session page count
        await db.execute(
            update(InkSession)
            .where(InkSession.session_id == stroke_request.session_id)
            .values(
                page_count=InkSession.page_count + 1,
                last_activity=datetime.utcnow(),
            )
        )

        await db.commit()
        await db.refresh(ink_page)

        # Publish recognition event
        recognition_job_id = await self.event_service.publish_ink_ready_event(
            stroke_request.session_id,
            page_id,
            stroke_request.learner_id,
            stroke_request.subject,
            s3_key,
            len(stroke_request.strokes),
        )

        # Update recognition job ID if event was published
        if recognition_job_id:
            await db.execute(
                update(InkPage)
                .where(InkPage.page_id == page_id)
                .values(
                    recognition_requested=True,
                    recognition_job_id=recognition_job_id,
                )
            )
            await db.commit()

        logger.info(
            "Successfully processed stroke request",
            session_id=stroke_request.session_id,
            page_id=page_id,
            stroke_count=len(stroke_request.strokes),
            recognition_job_id=recognition_job_id,
        )

        return StrokeResponse(
            session_id=stroke_request.session_id,
            page_id=page_id,
            s3_key=s3_key,
            stroke_count=len(stroke_request.strokes),
            recognition_job_id=recognition_job_id,
        )

    async def cleanup_expired_sessions(self, db: AsyncSession) -> int:
        """
        Clean up expired sessions.

        Args:
            db: Database session

        Returns:
            Number of sessions cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(
            minutes=settings.session_timeout_minutes
        )

        result = await db.execute(
            update(InkSession)
            .where(
                InkSession.last_activity < cutoff_time,
                InkSession.status == "active",
            )
            .values(status="expired")
        )

        await db.commit()
        expired_count = result.rowcount or 0

        if expired_count > 0:
            logger.info(f"Marked {expired_count} sessions as expired")

        return expired_count
