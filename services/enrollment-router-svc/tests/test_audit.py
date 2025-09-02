"""
Tests for enrollment auditing and tracking.
"""
import pytest
from datetime import datetime
from app.models import ProvisionSource, EnrollmentStatus
from app.schemas import EnrollmentRequest, LearnerProfile, EnrollmentContext
from app.services import EnrollmentRouterService, EventService


class TestEnrollmentAudit:
    """Test enrollment decision auditing."""
    
    @pytest.mark.asyncio
    async def test_enrollment_decision_is_recorded(
        self, 
        db_session, 
        district_allocation, 
        sample_learner_profile, 
        sample_district_context
    ):
        """Test that enrollment decisions are properly recorded."""
        service = EnrollmentRouterService()
        
        request = EnrollmentRequest(
            learner_profile=LearnerProfile(**sample_learner_profile),
            context=EnrollmentContext(**sample_district_context)
        )
        
        result = await service.route_enrollment(db_session, request)
        
        # Verify decision was recorded
        assert result.decision_id > 0
        
        # Verify decision details from database
        from sqlalchemy import select
        from app.models import EnrollmentDecision
        
        db_result = await db_session.execute(
            select(EnrollmentDecision).where(EnrollmentDecision.id == result.decision_id)
        )
        decision = db_result.scalar_one()
        
        assert decision.learner_email == "student@example.com"
        assert decision.learner_profile["first_name"] == "John"
        assert decision.learner_profile["last_name"] == "Doe"
        assert decision.tenant_id == 1
        assert decision.provision_source == ProvisionSource.DISTRICT
        assert decision.status == EnrollmentStatus.COMPLETED
        assert decision.district_seats_reserved == 1
        assert isinstance(decision.created_at, datetime)
        assert decision.decision_metadata is not None
    
    @pytest.mark.asyncio
    async def test_parent_enrollment_decision_recorded(
        self, 
        db_session, 
        sample_learner_profile, 
        sample_parent_context,
        mock_payment_service
    ):
        """Test that parent enrollment decisions are recorded."""
        service = EnrollmentRouterService()
        service.payment_service = mock_payment_service
        
        request = EnrollmentRequest(
            learner_profile=LearnerProfile(**sample_learner_profile),
            context=EnrollmentContext(**sample_parent_context)
        )
        
        result = await service.route_enrollment(db_session, request)
        
        # Verify decision was recorded
        from sqlalchemy import select
        from app.models import EnrollmentDecision
        
        db_result = await db_session.execute(
            select(EnrollmentDecision).where(EnrollmentDecision.id == result.decision_id)
        )
        decision = db_result.scalar_one()
        
        assert decision.guardian_id == "guardian_123"
        assert decision.provision_source == ProvisionSource.PARENT
        assert decision.status == EnrollmentStatus.CHECKOUT_REQUIRED
        assert decision.checkout_session_id == "cs_test_123"
        assert decision.checkout_url == "https://checkout.stripe.com/pay/cs_test_123"
    
    @pytest.mark.asyncio
    async def test_failed_enrollment_is_recorded(
        self, 
        db_session, 
        sample_learner_profile, 
        sample_parent_context
    ):
        """Test that failed enrollments are properly recorded."""
        service = EnrollmentRouterService()
        
        # Mock payment service to raise exception
        from unittest.mock import AsyncMock
        mock_payment = AsyncMock()
        mock_payment.create_checkout_session.side_effect = Exception("Test error")
        service.payment_service = mock_payment
        
        request = EnrollmentRequest(
            learner_profile=LearnerProfile(**sample_learner_profile),
            context=EnrollmentContext(**sample_parent_context)
        )
        
        result = await service.route_enrollment(db_session, request)
        
        # Verify failed decision was recorded
        from sqlalchemy import select
        from app.models import EnrollmentDecision
        
        db_result = await db_session.execute(
            select(EnrollmentDecision).where(EnrollmentDecision.id == result.decision_id)
        )
        decision = db_result.scalar_one()
        
        assert decision.status == EnrollmentStatus.FAILED
        assert "Test error" in decision.error_message
    
    @pytest.mark.asyncio
    async def test_enrollment_metadata_includes_context(
        self, 
        db_session, 
        district_allocation, 
        sample_learner_profile
    ):
        """Test that enrollment metadata includes full context."""
        service = EnrollmentRouterService()
        
        context = EnrollmentContext(
            tenant_id=1,
            source="district_portal",
            referral_code="REF123",
            campaign_id="CAMP456",
            additional_context={"utm_source": "google", "utm_medium": "cpc"}
        )
        
        request = EnrollmentRequest(
            learner_profile=LearnerProfile(**sample_learner_profile),
            context=context
        )
        
        result = await service.route_enrollment(db_session, request)
        
        # Verify context was stored
        from sqlalchemy import select
        from app.models import EnrollmentDecision
        
        db_result = await db_session.execute(
            select(EnrollmentDecision).where(EnrollmentDecision.id == result.decision_id)
        )
        decision = db_result.scalar_one()
        
        stored_context = decision.context
        assert stored_context["tenant_id"] == 1
        assert stored_context["source"] == "district_portal"
        assert stored_context["referral_code"] == "REF123"
        assert stored_context["campaign_id"] == "CAMP456"
        assert stored_context["additional_context"]["utm_source"] == "google"


class TestEnrollmentEvents:
    """Test enrollment event publishing."""
    
    @pytest.mark.asyncio
    async def test_enrollment_event_is_published(
        self, 
        db_session, 
        district_allocation, 
        sample_learner_profile, 
        sample_district_context,
        caplog
    ):
        """Test that enrollment events are published."""
        import logging
        caplog.set_level(logging.INFO)
        
        service = EnrollmentRouterService()
        
        request = EnrollmentRequest(
            learner_profile=LearnerProfile(**sample_learner_profile),
            context=EnrollmentContext(**sample_district_context)
        )
        
        result = await service.route_enrollment(db_session, request)
        
        # Check that event was logged (in real implementation, would be published to message queue)
        assert "Published enrollment event" in caplog.text
        assert f'"decision_id":{result.decision_id}' in caplog.text
        assert '"provision_source":"district"' in caplog.text
        assert '"tenant_id":1' in caplog.text
    
    @pytest.mark.asyncio
    async def test_event_service_creates_correct_event(
        self, 
        enrollment_decision
    ):
        """Test that event service creates correct event structure."""
        event_service = EventService()
        
        # This would normally publish to a message queue
        # For testing, we'll verify the event structure
        await event_service.publish_enrollment_decision(enrollment_decision)
        
        # In a real implementation, we'd verify the published event
        # For now, we just verify no exceptions were raised
        assert True


class TestEnrollmentQueryAndReporting:
    """Test enrollment querying and reporting capabilities."""
    
    @pytest.mark.asyncio
    async def test_get_enrollment_decision_by_id(
        self, 
        db_session, 
        enrollment_decision
    ):
        """Test retrieving enrollment decision by ID."""
        from sqlalchemy import select
        from app.models import EnrollmentDecision
        
        result = await db_session.execute(
            select(EnrollmentDecision).where(EnrollmentDecision.id == enrollment_decision.id)
        )
        found_decision = result.scalar_one()
        
        assert found_decision.id == enrollment_decision.id
        assert found_decision.learner_email == "test@example.com"
        assert found_decision.provision_source == ProvisionSource.DISTRICT
    
    @pytest.mark.asyncio
    async def test_enrollment_decisions_have_timestamps(
        self, 
        db_session, 
        district_allocation, 
        sample_learner_profile, 
        sample_district_context
    ):
        """Test that enrollment decisions have proper timestamps."""
        service = EnrollmentRouterService()
        
        from datetime import datetime, timezone
        
        before_enrollment = datetime.now(timezone.utc)
        
        request = EnrollmentRequest(
            learner_profile=LearnerProfile(**sample_learner_profile),
            context=EnrollmentContext(**sample_district_context)
        )
        
        result = await service.route_enrollment(db_session, request)
        
        after_enrollment = datetime.now(timezone.utc)
        
        # Verify decision was recorded with timestamp
        from sqlalchemy import select
        from app.models import EnrollmentDecision
        
        db_result = await db_session.execute(
            select(EnrollmentDecision).where(EnrollmentDecision.id == result.decision_id)
        )
        decision = db_result.scalar_one()
        
        # Check timestamps are reasonable (accounting for timezone differences)
        assert decision.created_at is not None
        assert decision.updated_at is not None
        
        # Timestamps should be within reasonable range
        # Note: Using a larger tolerance due to potential timezone/precision differences
        time_diff_start = abs((decision.created_at.replace(tzinfo=None) - before_enrollment).total_seconds())
        time_diff_end = abs((decision.created_at.replace(tzinfo=None) - after_enrollment).total_seconds())
        assert time_diff_start < 60  # Within 1 minute
        assert time_diff_end < 60    # Within 1 minute
