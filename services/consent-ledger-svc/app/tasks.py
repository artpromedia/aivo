"""
Celery tasks for background processing of consent operations.

Handles data exports, deletions, and maintenance tasks.
"""
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict
from uuid import UUID

from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.models import DataExportRequest, DeletionRequest, RequestStatus
from app.services.cascade_delete import CascadeDeleteService
from app.services.data_export import DataExportService
from config.settings import get_settings

import logging

logger = logging.getLogger(__name__)

# Initialize Celery
settings = get_settings()
celery_app = Celery(
    "consent_ledger",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)

# Task routing
celery_app.conf.task_routes = {
    "app.tasks.process_data_export": {"queue": "exports"},
    "app.tasks.process_data_deletion": {"queue": "deletions"},
    "app.tasks.cleanup_expired_exports": {"queue": "maintenance"},
    "app.tasks.verify_deletion_completion": {"queue": "verification"},
}


async def get_async_session() -> AsyncSession:
    """Get async database session."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session()


def run_async_task(coro):
    """Helper to run async functions in Celery tasks."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def process_data_export(self, request_id: str) -> Dict[str, Any]:
    """
    Process data export request in background.
    
    Ensures completion within 10-day GDPR requirement.
    """
    try:
        logger.info(f"Processing data export request {request_id}")
        
        async def _process_export():
            async with get_async_session() as session:
                # Initialize export service
                export_service = DataExportService(
                    db_session=session,
                    export_storage_path=Path(settings.EXPORT_STORAGE_PATH),
                    # Add other clients based on configuration
                )
                
                # Process the export
                export_request = await export_service.process_export_request(
                    UUID(request_id)
                )
                
                return {
                    "success": True,
                    "request_id": request_id,
                    "status": export_request.status.value,
                    "file_size": export_request.export_file_size_bytes,
                    "completed_at": export_request.completed_at.isoformat() if export_request.completed_at else None,
                }
        
        result = run_async_task(_process_export())
        logger.info(f"Data export {request_id} completed successfully")
        return result
        
    except Exception as exc:
        logger.error(f"Data export {request_id} failed: {str(exc)}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying data export {request_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        # Mark as failed after max retries
        async def _mark_failed():
            async with get_async_session() as session:
                from sqlalchemy import select
                stmt = select(DataExportRequest).where(DataExportRequest.id == UUID(request_id))
                result = await session.execute(stmt)
                export_request = result.scalar_one_or_none()
                
                if export_request:
                    export_request.status = RequestStatus.FAILED
                    export_request.error_message = str(exc)
                    await session.commit()
        
        run_async_task(_mark_failed())
        
        return {
            "success": False,
            "request_id": request_id,
            "error": str(exc),
            "retries": self.request.retries,
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=600)
def process_data_deletion(self, request_id: str) -> Dict[str, Any]:
    """
    Process data deletion request with cascaded deletes.
    
    Removes data from all connected systems.
    """
    try:
        logger.info(f"Processing data deletion request {request_id}")
        
        async def _process_deletion():
            async with get_async_session() as session:
                from sqlalchemy import select
                
                # Get deletion request
                stmt = select(DeletionRequest).where(DeletionRequest.id == UUID(request_id))
                result = await session.execute(stmt)
                deletion_request = result.scalar_one_or_none()
                
                if not deletion_request:
                    raise ValueError(f"Deletion request {request_id} not found")
                
                # Initialize cascade delete service
                cascade_service = CascadeDeleteService(
                    db_session=session,
                    # Add clients based on configuration
                )
                
                # Execute cascaded deletion
                result = await cascade_service.execute_cascaded_deletion(deletion_request)
                return result
        
        result = run_async_task(_process_deletion())
        logger.info(f"Data deletion {request_id} completed successfully")
        return result
        
    except Exception as exc:
        logger.error(f"Data deletion {request_id} failed: {str(exc)}")
        
        # Retry logic with exponential backoff
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying data deletion {request_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        # Mark as failed after max retries
        async def _mark_failed():
            async with get_async_session() as session:
                from sqlalchemy import select
                stmt = select(DeletionRequest).where(DeletionRequest.id == UUID(request_id))
                result = await session.execute(stmt)
                deletion_request = result.scalar_one_or_none()
                
                if deletion_request:
                    deletion_request.status = RequestStatus.FAILED
                    deletion_request.error_message = str(exc)
                    await session.commit()
        
        run_async_task(_mark_failed())
        
        return {
            "success": False,
            "request_id": request_id,
            "error": str(exc),
            "retries": self.request.retries,
        }


@celery_app.task
def cleanup_expired_exports() -> Dict[str, Any]:
    """
    Clean up expired export files and requests.
    
    Runs daily to maintain storage hygiene.
    """
    try:
        logger.info("Starting cleanup of expired exports")
        
        async def _cleanup():
            async with get_async_session() as session:
                from sqlalchemy import select
                
                cleanup_stats = {
                    "files_deleted": 0,
                    "requests_cleaned": 0,
                    "bytes_freed": 0,
                }
                
                # Find expired export requests
                cutoff_date = datetime.utcnow() - timedelta(days=30)  # 30 days retention
                
                stmt = select(DataExportRequest).where(
                    DataExportRequest.download_expires_at < datetime.utcnow()
                ).where(
                    DataExportRequest.completed_at < cutoff_date
                )
                
                result = await session.execute(stmt)
                expired_requests = result.scalars().all()
                
                for request in expired_requests:
                    try:
                        # Delete export file if it exists
                        if request.export_file_path:
                            file_path = Path(request.export_file_path)
                            if file_path.exists():
                                file_size = file_path.stat().st_size
                                file_path.unlink()
                                cleanup_stats["files_deleted"] += 1
                                cleanup_stats["bytes_freed"] += file_size
                                logger.info(f"Deleted expired export file: {file_path}")
                        
                        # Clear file references
                        request.export_file_path = None
                        request.download_url = None
                        cleanup_stats["requests_cleaned"] += 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to clean up request {request.id}: {str(e)}")
                
                await session.commit()
                
                logger.info(f"Cleanup completed: {cleanup_stats}")
                return cleanup_stats
        
        return run_async_task(_cleanup())
        
    except Exception as exc:
        logger.error(f"Cleanup task failed: {str(exc)}")
        return {
            "success": False,
            "error": str(exc),
        }


@celery_app.task
def verify_deletion_completion(request_id: str) -> Dict[str, Any]:
    """
    Verify that data deletion was completed successfully.
    
    Runs after deletion to ensure compliance.
    """
    try:
        logger.info(f"Verifying deletion completion for request {request_id}")
        
        async def _verify():
            async with get_async_session() as session:
                from sqlalchemy import select
                
                # Get deletion request
                stmt = select(DeletionRequest).where(DeletionRequest.id == UUID(request_id))
                result = await session.execute(stmt)
                deletion_request = result.scalar_one_or_none()
                
                if not deletion_request:
                    raise ValueError(f"Deletion request {request_id} not found")
                
                # Initialize cascade delete service
                cascade_service = CascadeDeleteService(db_session=session)
                
                # Verify deletion
                verification_result = await cascade_service.verify_deletion_completion(
                    deletion_request.user_id
                )
                
                return verification_result
        
        result = run_async_task(_verify())
        logger.info(f"Deletion verification for {request_id} completed")
        return result
        
    except Exception as exc:
        logger.error(f"Deletion verification {request_id} failed: {str(exc)}")
        return {
            "success": False,
            "request_id": request_id,
            "error": str(exc),
        }


@celery_app.task
def check_overdue_exports() -> Dict[str, Any]:
    """
    Check for export requests approaching 10-day deadline.
    
    Sends alerts for requests that need attention.
    """
    try:
        logger.info("Checking for overdue export requests")
        
        async def _check_overdue():
            async with get_async_session() as session:
                from sqlalchemy import select
                
                # Find requests approaching deadline (8+ days old)
                warning_date = datetime.utcnow() - timedelta(days=8)
                overdue_date = datetime.utcnow() - timedelta(days=10)
                
                # Warning requests (8-10 days)
                warning_stmt = select(DataExportRequest).where(
                    DataExportRequest.status.in_([RequestStatus.PENDING, RequestStatus.IN_PROGRESS])
                ).where(
                    DataExportRequest.requested_at < warning_date
                ).where(
                    DataExportRequest.requested_at > overdue_date
                )
                
                warning_result = await session.execute(warning_stmt)
                warning_requests = warning_result.scalars().all()
                
                # Overdue requests (>10 days)
                overdue_stmt = select(DataExportRequest).where(
                    DataExportRequest.status.in_([RequestStatus.PENDING, RequestStatus.IN_PROGRESS])
                ).where(
                    DataExportRequest.requested_at < overdue_date
                )
                
                overdue_result = await session.execute(overdue_stmt)
                overdue_requests = overdue_result.scalars().all()
                
                # Mark overdue requests as failed
                for request in overdue_requests:
                    request.status = RequestStatus.FAILED
                    request.error_message = "Export request exceeded 10-day GDPR deadline"
                    logger.warning(f"Marked export request {request.id} as failed (overdue)")
                
                await session.commit()
                
                return {
                    "warning_requests": len(warning_requests),
                    "overdue_requests": len(overdue_requests),
                    "warning_request_ids": [str(r.id) for r in warning_requests],
                    "overdue_request_ids": [str(r.id) for r in overdue_requests],
                }
        
        result = run_async_task(_check_overdue())
        logger.info(f"Overdue check completed: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Overdue check failed: {str(exc)}")
        return {
            "success": False,
            "error": str(exc),
        }


# Periodic tasks configuration
celery_app.conf.beat_schedule = {
    "cleanup-expired-exports": {
        "task": "app.tasks.cleanup_expired_exports",
        "schedule": 86400.0,  # Daily
    },
    "check-overdue-exports": {
        "task": "app.tasks.check_overdue_exports", 
        "schedule": 3600.0,  # Hourly
    },
}
