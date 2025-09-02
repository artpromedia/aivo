"""
Tests for teacher multi-attach functionality.
"""
import pytest
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Learner, Guardian, Teacher, Tenant, learner_teacher_association, ProvisionSource
from app.services import LearnerService
from app.schemas import LearnerCreate


class TestTeacherMultiAttach:
    """Test teacher multi-attach functionality."""
    
    @pytest.mark.asyncio
    async def test_assign_single_teacher(
        self, 
        db_session: AsyncSession, 
        sample_guardian: Guardian,
        sample_teacher: Teacher
    ):
        """Test assigning a single teacher to a learner."""
        service = LearnerService(db_session)
        
        # Create learner
        learner_data = LearnerCreate(
            first_name="Student",
            last_name="One",
            dob=date(2015, 6, 15),
            provision_source=ProvisionSource.PARENT,
            guardian_id=sample_guardian.id
        )
        
        learner = await service.create_learner(learner_data)
        
        # Assign teacher
        success = await service.assign_teacher(
            learner.id, 
            sample_teacher.id, 
            assigned_by="test_admin"
        )
        
        assert success is True
        
        # Verify assignment in database
        result = await db_session.execute(
            select(learner_teacher_association)
            .where(
                learner_teacher_association.c.learner_id == learner.id,
                learner_teacher_association.c.teacher_id == sample_teacher.id
            )
        )
        assignment = result.first()
        
        assert assignment is not None
        assert assignment.learner_id == learner.id
        assert assignment.teacher_id == sample_teacher.id
        assert assignment.assigned_by == "test_admin"
        assert assignment.assigned_at is not None
    
    @pytest.mark.asyncio
    async def test_assign_multiple_teachers(
        self, 
        db_session: AsyncSession, 
        sample_guardian: Guardian,
        sample_teacher: Teacher,
        second_teacher: Teacher
    ):
        """Test assigning multiple teachers to a learner."""
        service = LearnerService(db_session)
        
        # Create learner
        learner_data = LearnerCreate(
            first_name="Student",
            last_name="Multi",
            dob=date(2015, 6, 15),
            provision_source=ProvisionSource.PARENT,
            guardian_id=sample_guardian.id
        )
        
        learner = await service.create_learner(learner_data)
        
        # Assign multiple teachers
        teacher_ids = [sample_teacher.id, second_teacher.id]
        results = await service.assign_multiple_teachers(
            learner.id,
            teacher_ids,
            assigned_by="bulk_admin"
        )
        
        # Verify results
        assert len(results) == 2
        assert results[sample_teacher.id] is True
        assert results[second_teacher.id] is True
        
        # Verify assignments in database
        assignments_result = await db_session.execute(
            select(learner_teacher_association)
            .where(learner_teacher_association.c.learner_id == learner.id)
        )
        assignments = assignments_result.fetchall()
        
        assert len(assignments) == 2
        assigned_teacher_ids = [a.teacher_id for a in assignments]
        assert sample_teacher.id in assigned_teacher_ids
        assert second_teacher.id in assigned_teacher_ids
    
    @pytest.mark.asyncio
    async def test_assign_duplicate_teacher(
        self, 
        db_session: AsyncSession, 
        sample_guardian: Guardian,
        sample_teacher: Teacher
    ):
        """Test assigning the same teacher twice (should fail second time)."""
        service = LearnerService(db_session)
        
        # Create learner
        learner_data = LearnerCreate(
            first_name="Duplicate",
            last_name="Test",
            dob=date(2015, 6, 15),
            provision_source=ProvisionSource.PARENT,
            guardian_id=sample_guardian.id
        )
        
        learner = await service.create_learner(learner_data)
        
        # First assignment should succeed
        success1 = await service.assign_teacher(learner.id, sample_teacher.id)
        assert success1 is True
        
        # Second assignment should fail (duplicate)
        success2 = await service.assign_teacher(learner.id, sample_teacher.id)
        assert success2 is False
    
    @pytest.mark.asyncio
    async def test_remove_teacher_assignment(
        self, 
        db_session: AsyncSession, 
        sample_guardian: Guardian,
        sample_teacher: Teacher
    ):
        """Test removing a teacher assignment."""
        service = LearnerService(db_session)
        
        # Create learner and assign teacher
        learner_data = LearnerCreate(
            first_name="Remove",
            last_name="Test",
            dob=date(2015, 6, 15),
            provision_source=ProvisionSource.PARENT,
            guardian_id=sample_guardian.id
        )
        
        learner = await service.create_learner(learner_data)
        await service.assign_teacher(learner.id, sample_teacher.id)
        
        # Verify assignment exists
        result = await db_session.execute(
            select(learner_teacher_association)
            .where(
                learner_teacher_association.c.learner_id == learner.id,
                learner_teacher_association.c.teacher_id == sample_teacher.id
            )
        )
        assert result.first() is not None
        
        # Remove assignment
        success = await service.remove_teacher(learner.id, sample_teacher.id)
        assert success is True
        
        # Verify assignment was removed
        result = await db_session.execute(
            select(learner_teacher_association)
            .where(
                learner_teacher_association.c.learner_id == learner.id,
                learner_teacher_association.c.teacher_id == sample_teacher.id
            )
        )
        assert result.first() is None
    
    @pytest.mark.asyncio
    async def test_remove_nonexistent_assignment(
        self, 
        db_session: AsyncSession, 
        sample_guardian: Guardian,
        sample_teacher: Teacher
    ):
        """Test removing a teacher assignment that doesn't exist."""
        service = LearnerService(db_session)
        
        # Create learner (no teacher assigned)
        learner_data = LearnerCreate(
            first_name="NoAssign",
            last_name="Test",
            dob=date(2015, 6, 15),
            provision_source=ProvisionSource.PARENT,
            guardian_id=sample_guardian.id
        )
        
        learner = await service.create_learner(learner_data)
        
        # Try to remove non-existent assignment
        success = await service.remove_teacher(learner.id, sample_teacher.id)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_assign_invalid_teacher(
        self, 
        db_session: AsyncSession, 
        sample_guardian: Guardian
    ):
        """Test assigning a non-existent teacher."""
        service = LearnerService(db_session)
        
        # Create learner
        learner_data = LearnerCreate(
            first_name="Invalid",
            last_name="Teacher",
            dob=date(2015, 6, 15),
            provision_source=ProvisionSource.PARENT,
            guardian_id=sample_guardian.id
        )
        
        learner = await service.create_learner(learner_data)
        
        # Try to assign non-existent teacher
        with pytest.raises(ValueError, match="Teacher with ID 999 not found"):
            await service.assign_teacher(learner.id, 999)
    
    @pytest.mark.asyncio
    async def test_assign_teacher_to_invalid_learner(
        self, 
        db_session: AsyncSession,
        sample_teacher: Teacher
    ):
        """Test assigning a teacher to a non-existent learner."""
        service = LearnerService(db_session)
        
        # Try to assign teacher to non-existent learner
        with pytest.raises(ValueError, match="Learner with ID 999 not found"):
            await service.assign_teacher(999, sample_teacher.id)
    
    @pytest.mark.asyncio
    async def test_learner_teachers_relationship(
        self, 
        db_session: AsyncSession, 
        sample_guardian: Guardian,
        sample_teacher: Teacher,
        second_teacher: Teacher
    ):
        """Test that learner-teacher relationships are properly loaded."""
        service = LearnerService(db_session)
        
        # Create learner
        learner_data = LearnerCreate(
            first_name="Relation",
            last_name="Test",
            dob=date(2015, 6, 15),
            provision_source=ProvisionSource.PARENT,
            guardian_id=sample_guardian.id
        )
        
        learner = await service.create_learner(learner_data)
        
        # Assign teachers
        await service.assign_teacher(learner.id, sample_teacher.id)
        await service.assign_teacher(learner.id, second_teacher.id)
        
        # Get learner with relationships
        learner_with_relations = await service.get_learner(learner.id, include_relations=True)
        
        assert learner_with_relations is not None
        assert learner_with_relations.teachers is not None
        assert len(learner_with_relations.teachers) == 2
        
        teacher_ids = [t.id for t in learner_with_relations.teachers]
        assert sample_teacher.id in teacher_ids
        assert second_teacher.id in teacher_ids
    
    @pytest.mark.asyncio
    async def test_bulk_assignment_partial_failure(
        self, 
        db_session: AsyncSession, 
        sample_guardian: Guardian,
        sample_teacher: Teacher
    ):
        """Test bulk assignment with some valid and some invalid teacher IDs."""
        service = LearnerService(db_session)
        
        # Create learner
        learner_data = LearnerCreate(
            first_name="Bulk",
            last_name="Partial",
            dob=date(2015, 6, 15),
            provision_source=ProvisionSource.PARENT,
            guardian_id=sample_guardian.id
        )
        
        learner = await service.create_learner(learner_data)
        
        # Assign teachers (one valid, one invalid)
        teacher_ids = [sample_teacher.id, 999]  # 999 doesn't exist
        results = await service.assign_multiple_teachers(learner.id, teacher_ids)
        
        # Verify results
        assert len(results) == 2
        assert results[sample_teacher.id] is True
        assert results[999] is False
