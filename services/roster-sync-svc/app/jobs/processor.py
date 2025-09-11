"""Celery job processor for roster synchronization tasks."""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from celery import Celery
from celery.exceptions import Retry

from app.connectors.base import BaseConnector, ConnectorError
from app.connectors.oneroster import OneRosterConnector
from app.models import ConnectorType, SyncStatus

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    "roster-sync",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)


class RosterSyncJob:
    """Roster synchronization job processor."""
    
    def __init__(self, job_id: str, config: Dict[str, Any]):
        """Initialize job processor."""
        self.job_id = job_id
        self.config = config
        self.connector: Optional[BaseConnector] = None
        self.progress_percent = 0
        self.current_step = ""
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
    async def progress_callback(self, message: str, percent: int) -> None:
        """Update job progress."""
        self.current_step = message
        self.progress_percent = percent
        
        # Update job status in database
        # This would typically update the SyncJob record
        logger.info(f"Job {self.job_id} - {message} ({percent}%)")
        
        # Update Celery task state
        current_task = celery_app.current_task
        if current_task:
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "current_step": message,
                    "progress_percent": percent,
                    "job_id": self.job_id
                }
            )
    
    def get_connector(self, connector_type: str, config: Dict[str, Any]) -> BaseConnector:
        """Get connector instance based on type."""
        connector_map = {
            ConnectorType.ONEROSTER: OneRosterConnector,
            # ConnectorType.CLEVER: CleverConnector,
            # ConnectorType.CSV: CSVConnector,
        }
        
        connector_class = connector_map.get(connector_type)
        if not connector_class:
            raise ValueError(f"Unsupported connector type: {connector_type}")
        
        return connector_class(config)
    
    async def run(self) -> Dict[str, Any]:
        """Execute the roster sync job."""
        try:
            self.start_time = datetime.now()
            
            # Initialize connector
            connector_type = self.config.get("connector_type")
            connector_config = self.config.get("connector_config", {})
            
            self.connector = self.get_connector(connector_type, connector_config)
            
            await self.progress_callback("Initializing connector", 5)
            
            # Test connection
            await self.progress_callback("Testing connection", 10)
            connection_test = await self.connector.test_connection()
            
            if not connection_test.get("success"):
                raise ConnectorError(f"Connection test failed: {connection_test.get('message')}")
            
            # Sync data
            await self.progress_callback("Starting data synchronization", 15)
            
            results = await self.connector.sync_data(self.progress_callback)
            
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            
            # Calculate totals
            total_processed = sum(r.get("processed", 0) for r in results.values() if isinstance(r, dict))
            total_created = sum(r.get("created", 0) for r in results.values() if isinstance(r, dict))
            total_updated = sum(r.get("updated", 0) for r in results.values() if isinstance(r, dict))
            total_failed = sum(r.get("failed", 0) for r in results.values() if isinstance(r, dict))
            
            final_result = {
                "job_id": self.job_id,
                "status": SyncStatus.COMPLETED,
                "duration_seconds": int(duration),
                "total_processed": total_processed,
                "total_created": total_created,
                "total_updated": total_updated,
                "total_failed": total_failed,
                "detailed_results": results,
                "started_at": self.start_time.isoformat(),
                "completed_at": self.end_time.isoformat()
            }
            
            logger.info(f"Job {self.job_id} completed successfully: {total_processed} records processed")
            return final_result
            
        except Exception as e:
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
            
            error_result = {
                "job_id": self.job_id,
                "status": SyncStatus.FAILED,
                "error": str(e),
                "duration_seconds": int(duration),
                "started_at": self.start_time.isoformat() if self.start_time else None,
                "failed_at": self.end_time.isoformat()
            }
            
            logger.error(f"Job {self.job_id} failed: {e}")
            raise
            
        finally:
            # Clean up connector
            if self.connector:
                try:
                    await self.connector.disconnect()
                except Exception as e:
                    logger.warning(f"Error disconnecting connector: {e}")


@celery_app.task(bind=True, name="roster_sync.sync_roster_data")
def sync_roster_data(self, job_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery task to synchronize roster data.
    
    Args:
        job_config: Configuration for the sync job including:
            - job_id: Unique job identifier
            - connector_type: Type of connector (oneroster, clever, csv)
            - connector_config: Connector-specific configuration
            - district_id: District identifier
            - webhook_url: Optional webhook for progress notifications
            
    Returns:
        Dict containing job results
    """
    job_id = job_config.get("job_id", str(uuid.uuid4()))
    
    # Update task state
    self.update_state(
        state="PROGRESS",
        meta={
            "current_step": "Initializing job",
            "progress_percent": 0,
            "job_id": job_id
        }
    )
    
    # Create job processor
    job_processor = RosterSyncJob(job_id, job_config)
    
    try:
        # Run async job in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(job_processor.run())
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Celery task failed for job {job_id}: {e}")
        
        # Update task state to failure
        self.update_state(
            state="FAILURE",
            meta={
                "error": str(e),
                "job_id": job_id
            }
        )
        raise


@celery_app.task(name="roster_sync.test_connector")
def test_connector(connector_type: str, connector_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test a connector configuration.
    
    Args:
        connector_type: Type of connector to test
        connector_config: Connector configuration
        
    Returns:
        Dict containing test results
    """
    async def _test():
        job_processor = RosterSyncJob(str(uuid.uuid4()), {})
        connector = job_processor.get_connector(connector_type, connector_config)
        
        try:
            result = await connector.test_connection()
            return result
        finally:
            await connector.disconnect()
    
    # Run async test in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(_test())
    finally:
        loop.close()


@celery_app.task(name="roster_sync.cleanup_old_jobs")
def cleanup_old_jobs(days_old: int = 30) -> Dict[str, Any]:
    """
    Clean up old job records and logs.
    
    Args:
        days_old: Age threshold for cleanup
        
    Returns:
        Dict containing cleanup results
    """
    # This would typically clean up old SyncJob and SyncLog records
    # from the database that are older than the specified threshold
    
    logger.info(f"Cleaning up jobs older than {days_old} days")
    
    # Placeholder implementation
    return {
        "cleaned_jobs": 0,
        "cleaned_logs": 0,
        "days_old": days_old
    }


@celery_app.task(name="roster_sync.send_webhook_notification")
def send_webhook_notification(webhook_url: str, webhook_secret: str, payload: Dict[str, Any]) -> bool:
    """
    Send webhook notification for job completion.
    
    Args:
        webhook_url: Webhook endpoint URL
        webhook_secret: Secret for webhook authentication
        payload: Notification payload
        
    Returns:
        bool: Success status
    """
    import hashlib
    import hmac
    import httpx
    
    try:
        # Create signature
        payload_str = str(payload).encode("utf-8")
        signature = hmac.new(
            webhook_secret.encode("utf-8"),
            payload_str,
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"sha256={signature}",
            "User-Agent": "Roster-Sync-Service/1.0"
        }
        
        with httpx.Client(timeout=30) as client:
            response = client.post(webhook_url, json=payload, headers=headers)
            response.raise_for_status()
            
        logger.info(f"Webhook notification sent successfully to {webhook_url}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send webhook notification: {e}")
        return False


# Task routing configuration
celery_app.conf.task_routes = {
    "roster_sync.sync_roster_data": {"queue": "sync"},
    "roster_sync.test_connector": {"queue": "test"},
    "roster_sync.cleanup_old_jobs": {"queue": "maintenance"},
    "roster_sync.send_webhook_notification": {"queue": "notifications"},
}

# Periodic tasks configuration
celery_app.conf.beat_schedule = {
    "cleanup-old-jobs": {
        "task": "roster_sync.cleanup_old_jobs",
        "schedule": 86400.0,  # Daily
        "args": (30,)  # 30 days old
    },
}

if __name__ == "__main__":
    # For development - start worker
    celery_app.start()
