"""
Business logic services for private brain orchestrator.
"""
import asyncio
import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from .database import AsyncSessionLocal
from .models import PrivateBrainInstance, PrivateBrainRequest, PrivateBrainStatus
from .schemas import PrivateBrainRequestCreate, PrivateBrainInstanceUpdate

logger = logging.getLogger(__name__)


class NamespaceService:
    """Service for managing learner namespaces."""
    
    @staticmethod
    def generate_namespace_uid(learner_id: int) -> str:
        """Generate a unique namespace UID for a learner."""
        # Create a deterministic but unique namespace identifier
        base_string = f"learner-{learner_id}-{uuid.uuid4()}"
        namespace_hash = hashlib.sha256(base_string.encode()).hexdigest()[:16]
        return f"ns-{namespace_hash}"
    
    @staticmethod
    def generate_checkpoint_hash() -> str:
        """Generate a checkpoint hash (simulated)."""
        # In a real implementation, this would be based on the actual model state
        return hashlib.sha256(f"checkpoint-{uuid.uuid4()}".encode()).hexdigest()[:32]


class PrivateBrainOrchestrator:
    """Main orchestrator service for private brain instances."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.namespace_service = NamespaceService()
    
    async def request_private_brain(
        self, 
        request_data: PrivateBrainRequestCreate
    ) -> Tuple[PrivateBrainInstance, bool]:
        """
        Process a private brain request.
        
        Returns:
            Tuple of (instance, is_new_request)
        """
        learner_id = request_data.learner_id
        
        # Log the incoming request
        await self._log_request(request_data)
        
        # Check if instance already exists
        result = await self.db.execute(
            select(PrivateBrainInstance).where(
                PrivateBrainInstance.learner_id == learner_id
            )
        )
        existing_instance = result.scalar_one_or_none()
        
        if existing_instance:
            # Update request tracking for idempotency
            existing_instance.request_count += 1
            existing_instance.last_request_at = datetime.now(timezone.utc)
            
            await self.db.commit()
            await self.db.refresh(existing_instance)
            
            logger.info(f"Existing private brain instance found for learner {learner_id}, count: {existing_instance.request_count}")
            return existing_instance, False
        
        # Create new instance
        try:
            instance = PrivateBrainInstance(
                learner_id=learner_id,
                status=PrivateBrainStatus.PENDING,
                request_count=1,
                last_request_at=datetime.now(timezone.utc)
            )
            
            self.db.add(instance)
            await self.db.commit()
            await self.db.refresh(instance)
            
            logger.info(f"Created new private brain instance for learner {learner_id}")
            
            # Start async cloning process
            asyncio.create_task(self._clone_private_brain(instance.id))
            
            return instance, True
            
        except IntegrityError:
            # Handle race condition where another request created the instance
            await self.db.rollback()
            return await self.request_private_brain(request_data)
    
    async def get_status(self, learner_id: int) -> Optional[PrivateBrainInstance]:
        """Get the status of a private brain instance for a learner."""
        result = await self.db.execute(
            select(PrivateBrainInstance).where(
                PrivateBrainInstance.learner_id == learner_id
            )
        )
        return result.scalar_one_or_none()
    
    async def update_instance(
        self, 
        instance_id: int, 
        update_data: PrivateBrainInstanceUpdate
    ) -> Optional[PrivateBrainInstance]:
        """Update a private brain instance (internal use)."""
        result = await self.db.execute(
            select(PrivateBrainInstance).where(
                PrivateBrainInstance.id == instance_id
            )
        )
        instance = result.scalar_one_or_none()
        
        if not instance:
            return None
        
        # Apply updates
        for field, value in update_data.model_dump(exclude_unset=True).items():
            if hasattr(instance, field):
                setattr(instance, field, value)
        
        # Set ready_at timestamp if status is changing to READY
        if update_data.status == PrivateBrainStatus.READY and instance.status != PrivateBrainStatus.READY:
            instance.ready_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(instance)
        
        logger.info(f"Updated private brain instance {instance_id}: {update_data.model_dump(exclude_unset=True)}")
        return instance
    
    async def _log_request(self, request_data: PrivateBrainRequestCreate) -> None:
        """Log the private brain request for auditing."""
        request_log = PrivateBrainRequest(
            learner_id=request_data.learner_id,
            request_source=request_data.request_source,
            request_id=request_data.request_id
        )
        
        self.db.add(request_log)
        await self.db.commit()
    
    async def _clone_private_brain(self, instance_id: int) -> None:
        """
        Simulate private brain cloning process.
        This would integrate with actual ML model cloning in production.
        """
        try:
            # Create a new session for the background task
            async with AsyncSessionLocal() as session:
                orchestrator = PrivateBrainOrchestrator(session)
                
                # Update to CLONING status
                await orchestrator._update_instance_status(
                    instance_id, 
                    PrivateBrainStatus.CLONING,
                    "Cloning private brain model..."
                )
                
                # Simulate cloning process
                await asyncio.sleep(2)  # Simulate work
                
                # Generate checkpoint hash (simulate model checkpoints)
                checkpoint_hash = f"ckpt_{instance_id}_{asyncio.get_event_loop().time():.0f}"
                
                # Update to READY status
                await orchestrator._update_instance_status(
                    instance_id,
                    PrivateBrainStatus.READY,
                    ready_at=datetime.now(timezone.utc),
                    checkpoint_hash=checkpoint_hash
                )
                
                logger.info(f"Private brain cloning completed for instance {instance_id}")
                
        except Exception as e:
            logger.error(f"Error during private brain cloning for instance {instance_id}: {e}")
            # Create a new session for error handling
            try:
                async with AsyncSessionLocal() as session:
                    orchestrator = PrivateBrainOrchestrator(session)
                    await orchestrator._update_instance_status(
                        instance_id,
                        PrivateBrainStatus.ERROR,
                        error_message=str(e)
                    )
            except Exception as cleanup_error:
                logger.error(f"Failed to update error status for instance {instance_id}: {cleanup_error}")
    
    async def _update_instance_status(
        self, 
        instance_id: int, 
        status: PrivateBrainStatus,
        error_message: Optional[str] = None
    ) -> None:
        """Helper to update instance status."""
        update_data = PrivateBrainInstanceUpdate(
            status=status,
            error_message=error_message
        )
        await self.update_instance(instance_id, update_data)
