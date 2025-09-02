"""
Business logic services for enrollment router.
"""
import logging
from datetime import datetime
from typing import Optional, Union, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import httpx

from .models import (
    EnrollmentDecision, DistrictSeatAllocation, 
    ProvisionSource, EnrollmentStatus
)
from .schemas import (
    EnrollmentRequest, LearnerProfile, EnrollmentContext,
    DistrictEnrollmentResult, ParentEnrollmentResult,
    EnrollmentEvent
)

logger = logging.getLogger(__name__)


class DistrictSeatService:
    """Service for managing district seat allocations."""
    
    async def get_allocation(
        self, 
        db: AsyncSession, 
        tenant_id: int
    ) -> Optional[DistrictSeatAllocation]:
        """Get district seat allocation by tenant ID."""
        result = await db.execute(
            select(DistrictSeatAllocation).where(
                and_(
                    DistrictSeatAllocation.tenant_id == tenant_id,
                    DistrictSeatAllocation.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def has_available_seats(
        self, 
        db: AsyncSession, 
        tenant_id: int, 
        seats_needed: int = 1
    ) -> bool:
        """Check if district has available seats."""
        allocation = await self.get_allocation(db, tenant_id)
        if not allocation:
            return False
        return allocation.available_seats >= seats_needed
    
    async def reserve_seats(
        self, 
        db: AsyncSession, 
        tenant_id: int, 
        seats_to_reserve: int = 1
    ) -> bool:
        """Reserve seats for district enrollment."""
        allocation = await self.get_allocation(db, tenant_id)
        if not allocation or allocation.available_seats < seats_to_reserve:
            return False
        
        allocation.reserved_seats += seats_to_reserve
        await db.commit()
        await db.refresh(allocation)
        
        logger.info(
            f"Reserved {seats_to_reserve} seats for tenant {tenant_id}. "
            f"Available: {allocation.available_seats}"
        )
        return True

    async def create_allocation(
        self,
        db: AsyncSession,
        tenant_id: int,
        total_seats: int
    ) -> DistrictSeatAllocation:
        """Create new district seat allocation."""
        allocation = DistrictSeatAllocation(
            tenant_id=tenant_id,
            total_seats=total_seats
        )
        db.add(allocation)
        await db.commit()
        await db.refresh(allocation)
        return allocation


class PaymentService:
    """Service for handling payment-related operations."""
    
    def __init__(self, payment_service_url: str = "http://localhost:8001"):
        self.payment_service_url = payment_service_url
    
    async def create_checkout_session(
        self,
        guardian_id: str,
        learner_profile: LearnerProfile,
        context: EnrollmentContext
    ) -> Dict[str, Any]:
        """Create checkout session for parent enrollment."""
        checkout_data = {
            "guardian_id": guardian_id,
            "plan_type": "monthly",  # Default plan
            "seats": 1,
            "success_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
            "has_sibling_discount": False,
            "metadata": {
                "learner_email": learner_profile.email,
                "learner_name": f"{learner_profile.first_name} {learner_profile.last_name}",
                "enrollment_context": context.model_dump()
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.payment_service_url}/checkout/sessions",
                    json=checkout_data,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Checkout session creation failed: {e.response.text}")
            raise


class EventService:
    """Service for publishing enrollment events."""
    
    async def publish_enrollment_decision(
        self,
        decision: EnrollmentDecision
    ) -> None:
        """Publish enrollment decision event."""
        event = EnrollmentEvent(
            decision_id=decision.id,
            provision_source=decision.provision_source,
            tenant_id=decision.tenant_id,
            guardian_id=decision.guardian_id,
            learner_email=decision.learner_profile.get("email", ""),
            status=decision.status,
            timestamp=decision.created_at,
            metadata=decision.decision_metadata
        )
        
        # In a real implementation, this would publish to a message queue
        # For now, we'll just log the event
        logger.info(f"Published enrollment event: {event.model_dump_json()}")


class EnrollmentRouterService:
    """Main service for routing enrollment decisions."""
    
    def __init__(self):
        self.district_service = DistrictSeatService()
        self.payment_service = PaymentService()
        self.event_service = EventService()
    
    async def route_enrollment(
        self,
        db: AsyncSession,
        request: EnrollmentRequest
    ) -> Union[DistrictEnrollmentResult, ParentEnrollmentResult]:
        """Route enrollment based on context and availability."""
        
        # Create enrollment decision record
        decision = EnrollmentDecision(
            learner_id=request.learner_profile.learner_id,
            learner_email=request.learner_profile.email,
            learner_profile=request.learner_profile.model_dump(),
            tenant_id=request.context.tenant_id,
            guardian_id=request.context.guardian_id,
            context=request.context.model_dump(),
            provision_source=ProvisionSource.PARENT,  # Default, will be updated
            status=EnrollmentStatus.PENDING
        )
        
        try:
            # Check if this is a district enrollment
            if request.context.tenant_id:
                result = await self._process_district_enrollment(
                    db, request, decision
                )
            else:
                result = await self._process_parent_enrollment(
                    db, request, decision
                )
            
            # Save the decision
            db.add(decision)
            await db.commit()
            await db.refresh(decision)
            
            # Update result with decision ID
            result.decision_id = decision.id
            
            # Publish event
            await self.event_service.publish_enrollment_decision(decision)
            
            return result
            
        except Exception as e:
            decision.status = EnrollmentStatus.FAILED
            decision.error_message = str(e)
            db.add(decision)
            await db.commit()
            logger.error(f"Enrollment routing failed: {e}")
            raise
    
    async def _process_district_enrollment(
        self,
        db: AsyncSession,
        request: EnrollmentRequest,
        decision: EnrollmentDecision
    ) -> DistrictEnrollmentResult:
        """Process district-provisioned enrollment."""
        tenant_id = request.context.tenant_id
        
        # Check if district has available seats
        has_seats = await self.district_service.has_available_seats(
            db, tenant_id, 1
        )
        
        if has_seats:
            # Reserve seat for district enrollment
            reserved = await self.district_service.reserve_seats(
                db, tenant_id, 1
            )
            
            if reserved:
                allocation = await self.district_service.get_allocation(db, tenant_id)
                
                # Update decision
                decision.provision_source = ProvisionSource.DISTRICT
                decision.status = EnrollmentStatus.COMPLETED
                decision.district_seats_available = allocation.available_seats
                decision.district_seats_reserved = 1
                decision.decision_metadata = {
                    "allocation_id": allocation.id,
                    "seats_reserved": 1
                }
                
                return DistrictEnrollmentResult(
                    status=EnrollmentStatus.COMPLETED,
                    tenant_id=tenant_id,
                    seats_reserved=1,
                    seats_available=allocation.available_seats,
                    decision_id=0,  # Will be updated after save
                    message="Successfully enrolled via district allocation"
                )
        
        # Fall back to parent payment if no district seats available
        logger.info(
            f"No district seats available for tenant {tenant_id}, "
            f"falling back to parent payment"
        )
        return await self._process_parent_enrollment(db, request, decision)
    
    async def _process_parent_enrollment(
        self,
        db: AsyncSession,
        request: EnrollmentRequest,
        decision: EnrollmentDecision
    ) -> ParentEnrollmentResult:
        """Process parent-paid enrollment."""
        guardian_id = request.context.guardian_id
        
        # Generate guardian ID if not provided or empty
        if not guardian_id:
            guardian_id = f"guardian_{request.learner_profile.email}"
        
        try:
            # Create checkout session
            checkout_result = await self.payment_service.create_checkout_session(
                guardian_id=guardian_id,
                learner_profile=request.learner_profile,
                context=request.context
            )
            
            # Update decision
            decision.provision_source = ProvisionSource.PARENT
            decision.status = EnrollmentStatus.CHECKOUT_REQUIRED
            decision.guardian_id = guardian_id
            decision.checkout_session_id = checkout_result.get("session_id")
            decision.checkout_url = checkout_result.get("session_url")
            decision.decision_metadata = {
                "checkout_session": checkout_result
            }
            
            return ParentEnrollmentResult(
                status=EnrollmentStatus.CHECKOUT_REQUIRED,
                guardian_id=guardian_id,
                checkout_session_id=checkout_result.get("session_id"),
                checkout_url=checkout_result.get("session_url"),
                decision_id=0,  # Will be updated after save
                message="Checkout session created for parent payment"
            )
            
        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}")
            decision.status = EnrollmentStatus.FAILED
            decision.error_message = str(e)
            
            return ParentEnrollmentResult(
                status=EnrollmentStatus.FAILED,
                guardian_id=guardian_id,
                decision_id=0,
                message=f"Failed to create checkout session: {str(e)}"
            )
