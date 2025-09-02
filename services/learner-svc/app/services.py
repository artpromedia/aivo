"""
Business logic services for learner management.
"""
import logging
from datetime import date, datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    Learner, Guardian, Teacher, Tenant, PrivateBrainRequest,
    ProvisionSource, learner_teacher_association
)
from .schemas import (
    LearnerCreate, LearnerUpdate, GuardianCreate, GuardianUpdate,
    TeacherCreate, TeacherUpdate, TenantCreate, TenantUpdate,
    PrivateBrainRequestEvent
)

logger = logging.getLogger(__name__)


class GradeCalculatorService:
    """Service to calculate default grade based on date of birth."""
    
    @staticmethod
    def calculate_grade_from_dob(dob: date, reference_date: Optional[date] = None) -> int:
        """
        Calculate grade based on date of birth.
        
        Grade calculation logic:
        - September 1st is the typical school year cutoff
        - Children who turn 5 before Sept 1st start Kindergarten (grade 0)
        - Children who turn 6 before Sept 1st start 1st grade, etc.
        
        Args:
            dob: Date of birth
            reference_date: Reference date for calculation (default: today)
            
        Returns:
            Grade level (-1 for pre-K, 0 for K, 1-12 for grades 1-12)
        """
        if reference_date is None:
            reference_date = date.today()
            
        # Determine current school year
        if reference_date.month >= 9:  # September or later
            current_school_year = reference_date.year
        else:  # Before September
            current_school_year = reference_date.year - 1
            
        # Calculate age as of September 1st of current school year
        sept_first = date(current_school_year, 9, 1)
        
        # Calculate age on Sept 1st
        age_on_sept_first = sept_first.year - dob.year
        if sept_first.replace(year=dob.year) < dob:
            age_on_sept_first -= 1
            
        # Convert age to grade (5 years old on Sept 1st = Kindergarten = grade 0)
        grade = age_on_sept_first - 5
        
        # Clamp to reasonable bounds
        if grade < -1:  # Too young for pre-K
            grade = -1
        elif grade > 12:  # Too old for K-12
            grade = 12
            
        return grade


class EventService:
    """Service for handling event publishing."""
    
    @staticmethod
    async def publish_private_brain_request(
        db: AsyncSession,
        learner_id: int
    ) -> PrivateBrainRequest:
        """
        Publish PRIVATE_BRAIN_REQUEST event.
        
        In a production system, this would integrate with a message queue
        like Redis, RabbitMQ, or cloud-native solutions.
        """
        try:
            # Create event record
            event_record = PrivateBrainRequest(
                learner_id=learner_id,
                event_type="PRIVATE_BRAIN_REQUEST"
            )
            
            db.add(event_record)
            await db.commit()
            await db.refresh(event_record)
            
            # In production, publish to message queue here
            event_data = PrivateBrainRequestEvent(
                learner_id=learner_id,
                timestamp=event_record.created_at
            )
            
            logger.info(f"Published PRIVATE_BRAIN_REQUEST event: {event_data.model_dump_json()}")
            
            # Update status to sent
            event_record.status = "sent"
            event_record.processed_at = datetime.now(timezone.utc)
            await db.commit()
            
            return event_record
            
        except Exception as e:
            logger.error(f"Failed to publish PRIVATE_BRAIN_REQUEST event for learner {learner_id}: {e}")
            if 'event_record' in locals():
                event_record.status = "failed"
                await db.commit()
            raise


class LearnerService:
    """Service for managing learners."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.grade_calculator = GradeCalculatorService()
        self.event_service = EventService()
    
    async def create_learner(self, learner_data: LearnerCreate) -> Learner:
        """Create a new learner with guardian-first approach."""
        try:
            # Verify guardian exists
            guardian_result = await self.db.execute(
                select(Guardian).where(Guardian.id == learner_data.guardian_id)
            )
            guardian = guardian_result.scalar_one_or_none()
            if not guardian:
                raise ValueError(f"Guardian with ID {learner_data.guardian_id} not found")
            
            # Verify tenant exists if provided
            if learner_data.tenant_id:
                tenant_result = await self.db.execute(
                    select(Tenant).where(Tenant.id == learner_data.tenant_id)
                )
                tenant = tenant_result.scalar_one_or_none()
                if not tenant:
                    raise ValueError(f"Tenant with ID {learner_data.tenant_id} not found")
            
            # Calculate default grade from DOB
            grade_default = self.grade_calculator.calculate_grade_from_dob(learner_data.dob)
            
            # Create learner
            learner = Learner(
                first_name=learner_data.first_name,
                last_name=learner_data.last_name,
                email=learner_data.email,
                dob=learner_data.dob,
                grade_default=grade_default,
                grade_current=learner_data.grade_current or grade_default,
                provision_source=learner_data.provision_source,
                guardian_id=learner_data.guardian_id,
                tenant_id=learner_data.tenant_id
            )
            
            self.db.add(learner)
            await self.db.commit()
            await self.db.refresh(learner)
            
            # Publish PRIVATE_BRAIN_REQUEST event
            await self.event_service.publish_private_brain_request(self.db, learner.id)
            
            logger.info(f"Created learner: {learner.id} with default grade: {grade_default}")
            return learner
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create learner: {e}")
            raise
    
    async def get_learner(self, learner_id: int, include_relations: bool = False) -> Optional[Learner]:
        """Get learner by ID."""
        query = select(Learner).where(Learner.id == learner_id)
        
        if include_relations:
            query = query.options(
                selectinload(Learner.guardian),
                selectinload(Learner.tenant),
                selectinload(Learner.teachers)
            )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_learners_by_guardian(self, guardian_id: int) -> List[Learner]:
        """Get all learners for a guardian."""
        result = await self.db.execute(
            select(Learner)
            .where(Learner.guardian_id == guardian_id)
            .options(selectinload(Learner.teachers))
        )
        return list(result.scalars().all())
    
    async def update_learner(self, learner_id: int, update_data: LearnerUpdate) -> Optional[Learner]:
        """Update learner information."""
        try:
            result = await self.db.execute(
                select(Learner).where(Learner.id == learner_id)
            )
            learner = result.scalar_one_or_none()
            
            if not learner:
                return None
            
            # Update fields
            update_dict = update_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(learner, field, value)
            
            await self.db.commit()
            await self.db.refresh(learner)
            
            return learner
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update learner {learner_id}: {e}")
            raise
    
    async def assign_teacher(self, learner_id: int, teacher_id: int, assigned_by: Optional[str] = None) -> bool:
        """Assign a teacher to a learner."""
        try:
            # Verify learner and teacher exist
            learner_result = await self.db.execute(
                select(Learner).where(Learner.id == learner_id)
            )
            learner = learner_result.scalar_one_or_none()
            if not learner:
                raise ValueError(f"Learner with ID {learner_id} not found")
            
            teacher_result = await self.db.execute(
                select(Teacher).where(Teacher.id == teacher_id)
            )
            teacher = teacher_result.scalar_one_or_none()
            if not teacher:
                raise ValueError(f"Teacher with ID {teacher_id} not found")
            
            # Check if assignment already exists
            existing_result = await self.db.execute(
                select(learner_teacher_association)
                .where(
                    and_(
                        learner_teacher_association.c.learner_id == learner_id,
                        learner_teacher_association.c.teacher_id == teacher_id
                    )
                )
            )
            if existing_result.first():
                logger.warning(f"Teacher {teacher_id} already assigned to learner {learner_id}")
                return False
            
            # Create assignment
            await self.db.execute(
                learner_teacher_association.insert().values(
                    learner_id=learner_id,
                    teacher_id=teacher_id,
                    assigned_by=assigned_by
                )
            )
            await self.db.commit()
            
            logger.info(f"Assigned teacher {teacher_id} to learner {learner_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to assign teacher {teacher_id} to learner {learner_id}: {e}")
            raise
    
    async def remove_teacher(self, learner_id: int, teacher_id: int) -> bool:
        """Remove a teacher assignment from a learner."""
        try:
            result = await self.db.execute(
                learner_teacher_association.delete().where(
                    and_(
                        learner_teacher_association.c.learner_id == learner_id,
                        learner_teacher_association.c.teacher_id == teacher_id
                    )
                )
            )
            await self.db.commit()
            
            if result.rowcount > 0:
                logger.info(f"Removed teacher {teacher_id} from learner {learner_id}")
                return True
            else:
                logger.warning(f"No assignment found between teacher {teacher_id} and learner {learner_id}")
                return False
                
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to remove teacher {teacher_id} from learner {learner_id}: {e}")
            raise
    
    async def assign_multiple_teachers(self, learner_id: int, teacher_ids: List[int], assigned_by: Optional[str] = None) -> Dict[int, bool]:
        """Assign multiple teachers to a learner."""
        results = {}
        
        for teacher_id in teacher_ids:
            try:
                success = await self.assign_teacher(learner_id, teacher_id, assigned_by)
                results[teacher_id] = success
            except Exception as e:
                logger.error(f"Failed to assign teacher {teacher_id}: {e}")
                results[teacher_id] = False
        
        return results


class GuardianService:
    """Service for managing guardians."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_guardian(self, guardian_data: GuardianCreate) -> Guardian:
        """Create a new guardian."""
        try:
            guardian = Guardian(**guardian_data.model_dump())
            self.db.add(guardian)
            await self.db.commit()
            await self.db.refresh(guardian)
            
            logger.info(f"Created guardian: {guardian.id}")
            return guardian
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create guardian: {e}")
            raise
    
    async def get_guardian(self, guardian_id: int) -> Optional[Guardian]:
        """Get guardian by ID."""
        result = await self.db.execute(
            select(Guardian).where(Guardian.id == guardian_id)
        )
        return result.scalar_one_or_none()


class TeacherService:
    """Service for managing teachers."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_teacher(self, teacher_data: TeacherCreate) -> Teacher:
        """Create a new teacher."""
        try:
            # Verify tenant exists
            tenant_result = await self.db.execute(
                select(Tenant).where(Tenant.id == teacher_data.tenant_id)
            )
            tenant = tenant_result.scalar_one_or_none()
            if not tenant:
                raise ValueError(f"Tenant with ID {teacher_data.tenant_id} not found")
            
            teacher = Teacher(**teacher_data.model_dump())
            self.db.add(teacher)
            await self.db.commit()
            await self.db.refresh(teacher)
            
            logger.info(f"Created teacher: {teacher.id}")
            return teacher
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create teacher: {e}")
            raise
    
    async def get_teacher(self, teacher_id: int) -> Optional[Teacher]:
        """Get teacher by ID."""
        result = await self.db.execute(
            select(Teacher).where(Teacher.id == teacher_id)
        )
        return result.scalar_one_or_none()


class TenantService:
    """Service for managing tenants."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_tenant(self, tenant_data: TenantCreate) -> Tenant:
        """Create a new tenant."""
        try:
            tenant = Tenant(**tenant_data.model_dump())
            self.db.add(tenant)
            await self.db.commit()
            await self.db.refresh(tenant)
            
            logger.info(f"Created tenant: {tenant.id}")
            return tenant
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create tenant: {e}")
            raise
    
    async def get_tenant(self, tenant_id: int) -> Optional[Tenant]:
        """Get tenant by ID."""
        result = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()
