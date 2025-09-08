"""
Tests for learner creation and PRIVATE_BRAIN_REQUEST event emission.
"""

from datetime import date

import pytest
from app.models import Guardian, PrivateBrainRequest, ProvisionSource, Tenant
from app.schemas import LearnerCreate
from app.services import LearnerService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TestLearnerCreation:
    """Test learner creation with guardian-first approach."""

    @pytest.mark.asyncio
    async def test_create_learner_with_guardian_only(
        self, db_session: AsyncSession, sample_guardian: Guardian
    ):
        """Test creating a learner with guardian only (parent provision)."""
        service = LearnerService(db_session)

        learner_data = LearnerCreate(
            first_name="Alice",
            last_name="Johnson",
            email="alice.johnson@example.com",
            dob=date(2015, 6, 15),  # Should be grade 2-3
            provision_source=ProvisionSource.PARENT,
            guardian_id=sample_guardian.id,
        )

        learner = await service.create_learner(learner_data)

        # Verify learner was created correctly
        assert learner.id is not None
        assert learner.first_name == "Alice"
        assert learner.last_name == "Johnson"
        assert learner.email == "alice.johnson@example.com"
        assert learner.dob == date(2015, 6, 15)
        assert learner.provision_source == ProvisionSource.PARENT
        assert learner.guardian_id == sample_guardian.id
        assert learner.tenant_id is None
        assert learner.grade_default in [5, 6]  # Should be 5th or 6th grade based on age in 2025
        assert learner.grade_current == learner.grade_default
        assert learner.is_active is True

    @pytest.mark.asyncio
    async def test_create_learner_with_district_provision(
        self, db_session: AsyncSession, sample_guardian: Guardian, sample_tenant: Tenant
    ):
        """Test creating a learner with district provision."""
        service = LearnerService(db_session)

        learner_data = LearnerCreate(
            first_name="Bob",
            last_name="Smith",
            dob=date(2016, 3, 10),  # Should be grade 1-2
            provision_source=ProvisionSource.DISTRICT,
            guardian_id=sample_guardian.id,
            tenant_id=sample_tenant.id,
        )

        learner = await service.create_learner(learner_data)

        # Verify learner was created correctly
        assert learner.provision_source == ProvisionSource.DISTRICT
        assert learner.guardian_id == sample_guardian.id
        assert learner.tenant_id == sample_tenant.id
        assert learner.grade_default in [3, 4]  # Should be 3rd or 4th grade based on age in 2025

    @pytest.mark.asyncio
    async def test_create_learner_emits_private_brain_request(
        self, db_session: AsyncSession, sample_guardian: Guardian
    ):
        """Test that creating a learner emits a PRIVATE_BRAIN_REQUEST event."""
        service = LearnerService(db_session)

        learner_data = LearnerCreate(
            first_name="Charlie",
            last_name="Brown",
            dob=date(2014, 8, 20),
            provision_source=ProvisionSource.PARENT,
            guardian_id=sample_guardian.id,
        )

        learner = await service.create_learner(learner_data)

        # Verify PRIVATE_BRAIN_REQUEST event was created
        result = await db_session.execute(
            select(PrivateBrainRequest).where(PrivateBrainRequest.learner_id == learner.id)
        )
        brain_request = result.scalar_one_or_none()

        assert brain_request is not None
        assert brain_request.learner_id == learner.id
        assert brain_request.event_type == "PRIVATE_BRAIN_REQUEST"
        assert brain_request.status == "sent"
        assert brain_request.processed_at is not None

    @pytest.mark.asyncio
    async def test_create_learner_invalid_guardian(self, db_session: AsyncSession):
        """Test creating a learner with invalid guardian ID."""
        service = LearnerService(db_session)

        learner_data = LearnerCreate(
            first_name="Invalid",
            last_name="Guardian",
            dob=date(2015, 6, 15),
            provision_source=ProvisionSource.PARENT,
            guardian_id=999,  # Non-existent guardian
        )

        with pytest.raises(ValueError, match="Guardian with ID 999 not found"):
            await service.create_learner(learner_data)

    @pytest.mark.asyncio
    async def test_create_learner_invalid_tenant(
        self, db_session: AsyncSession, sample_guardian: Guardian
    ):
        """Test creating a learner with invalid tenant ID."""
        service = LearnerService(db_session)

        learner_data = LearnerCreate(
            first_name="Invalid",
            last_name="Tenant",
            dob=date(2015, 6, 15),
            provision_source=ProvisionSource.DISTRICT,
            guardian_id=sample_guardian.id,
            tenant_id=999,  # Non-existent tenant
        )

        with pytest.raises(ValueError, match="Tenant with ID 999 not found"):
            await service.create_learner(learner_data)

    @pytest.mark.asyncio
    async def test_create_learner_with_custom_grade(
        self, db_session: AsyncSession, sample_guardian: Guardian
    ):
        """Test creating a learner with custom grade override."""
        service = LearnerService(db_session)

        learner_data = LearnerCreate(
            first_name="Custom",
            last_name="Grade",
            dob=date(2015, 6, 15),
            provision_source=ProvisionSource.PARENT,
            guardian_id=sample_guardian.id,
            grade_current=5,  # Override default grade
        )

        learner = await service.create_learner(learner_data)

        # Verify grade override
        assert learner.grade_default in [5, 6]  # Default based on age in 2025
        assert learner.grade_current == 5  # Custom override

    @pytest.mark.asyncio
    async def test_get_learners_by_guardian(
        self, db_session: AsyncSession, sample_guardian: Guardian
    ):
        """Test getting all learners for a guardian."""
        service = LearnerService(db_session)

        # Create multiple learners for the same guardian
        learner_data_1 = LearnerCreate(
            first_name="First",
            last_name="Child",
            dob=date(2015, 6, 15),
            provision_source=ProvisionSource.PARENT,
            guardian_id=sample_guardian.id,
        )

        learner_data_2 = LearnerCreate(
            first_name="Second",
            last_name="Child",
            dob=date(2017, 3, 10),
            provision_source=ProvisionSource.PARENT,
            guardian_id=sample_guardian.id,
        )

        learner1 = await service.create_learner(learner_data_1)
        learner2 = await service.create_learner(learner_data_2)

        # Get all learners for the guardian
        learners = await service.get_learners_by_guardian(sample_guardian.id)

        assert len(learners) == 2
        learner_ids = [l.id for l in learners]
        assert learner1.id in learner_ids
        assert learner2.id in learner_ids

    @pytest.mark.asyncio
    async def test_update_learner(self, db_session: AsyncSession, sample_guardian: Guardian):
        """Test updating learner information."""
        service = LearnerService(db_session)

        # Create learner
        learner_data = LearnerCreate(
            first_name="Original",
            last_name="Name",
            dob=date(2015, 6, 15),
            provision_source=ProvisionSource.PARENT,
            guardian_id=sample_guardian.id,
        )

        learner = await service.create_learner(learner_data)

        # Update learner
        from app.schemas import LearnerUpdate

        update_data = LearnerUpdate(first_name="Updated", grade_current=4)

        updated_learner = await service.update_learner(learner.id, update_data)

        assert updated_learner is not None
        assert updated_learner.first_name == "Updated"
        assert updated_learner.last_name == "Name"  # Unchanged
        assert updated_learner.grade_current == 4

    @pytest.mark.asyncio
    async def test_get_learner_with_relations(
        self, db_session: AsyncSession, sample_guardian: Guardian, sample_tenant: Tenant
    ):
        """Test getting a learner with related data."""
        service = LearnerService(db_session)

        learner_data = LearnerCreate(
            first_name="Relation",
            last_name="Test",
            dob=date(2015, 6, 15),
            provision_source=ProvisionSource.DISTRICT,
            guardian_id=sample_guardian.id,
            tenant_id=sample_tenant.id,
        )

        learner = await service.create_learner(learner_data)

        # Get learner with relations
        learner_with_relations = await service.get_learner(learner.id, include_relations=True)

        assert learner_with_relations is not None
        assert learner_with_relations.guardian is not None
        assert learner_with_relations.guardian.id == sample_guardian.id
        assert learner_with_relations.tenant is not None
        assert learner_with_relations.tenant.id == sample_tenant.id
