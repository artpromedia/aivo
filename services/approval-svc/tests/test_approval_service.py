"""
Comprehensive tests for the Approval Service.
"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import UUID
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.approval_service import approval_service
from app.schemas import ApprovalCreateInput, DecisionInput
from app.enums import ApprovalStatus, DecisionType, ParticipantRole, ApprovalType, Priority
from app.models import Approval, ApprovalParticipant, ApprovalDecision


class TestApprovalCreation:
    """Test approval creation functionality."""
    
    def test_create_approval_success(self, client: TestClient, sample_approval_data):
        """Test successful approval creation."""
        response = client.post("/approvals", json=sample_approval_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "approval_id" in data
        assert UUID(data["approval_id"])  # Valid UUID
    
    def test_create_approval_invalid_participants(self, client: TestClient, sample_approval_data):
        """Test approval creation with invalid participants."""
        # Remove guardian participant
        sample_approval_data["participants"] = [
            p for p in sample_approval_data["participants"] 
            if p["role"] != ParticipantRole.GUARDIAN
        ]
        
        response = client.post("/approvals", json=sample_approval_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "Must have at least one guardian and one staff member" in str(data["detail"])
    
    def test_create_approval_duplicate_participants(self, client: TestClient, sample_approval_data):
        """Test approval creation with duplicate participants."""
        # Duplicate first participant
        sample_approval_data["participants"].append(sample_approval_data["participants"][0])
        
        response = client.post("/approvals", json=sample_approval_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "Duplicate user_ids" in str(data["detail"])
    
    def test_create_approval_invalid_ttl(self, client: TestClient, sample_approval_data):
        """Test approval creation with invalid TTL."""
        sample_approval_data["ttl_hours"] = 1000  # Exceeds maximum
        
        response = client.post("/approvals", json=sample_approval_data)
        
        assert response.status_code == 422  # Validation error


class TestApprovalRetrieval:
    """Test approval retrieval functionality."""
    
    @pytest.fixture
    async def created_approval(self, db_session: AsyncSession, sample_approval_data):
        """Create an approval for testing."""
        approval_input = ApprovalCreateInput(**sample_approval_data)
        approval = await approval_service.create_approval(db_session, approval_input)
        return approval
    
    def test_get_approval_success(self, client: TestClient, created_approval):
        """Test successful approval retrieval."""
        response = client.get(f"/approvals/{created_approval.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(created_approval.id)
        assert data["title"] == created_approval.title
        assert len(data["participants"]) == 2
    
    def test_get_approval_not_found(self, client: TestClient):
        """Test retrieval of non-existent approval."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/approvals/{fake_id}")
        
        assert response.status_code == 404
    
    def test_get_approval_with_tenant_filter(self, client: TestClient, created_approval):
        """Test approval retrieval with tenant filtering."""
        # Correct tenant
        response = client.get(
            f"/approvals/{created_approval.id}?tenant_id={created_approval.tenant_id}"
        )
        assert response.status_code == 200
        
        # Wrong tenant
        response = client.get(
            f"/approvals/{created_approval.id}?tenant_id=wrong_tenant"
        )
        assert response.status_code == 404


class TestApprovalListing:
    """Test approval listing functionality."""
    
    @pytest.fixture
    async def multiple_approvals(self, db_session: AsyncSession, sample_approval_data):
        """Create multiple approvals for testing."""
        approvals = []
        
        for i in range(3):
            data = sample_approval_data.copy()
            data["title"] = f"Approval {i + 1}"
            data["resource_id"] = f"resource_{i + 1}"
            
            approval_input = ApprovalCreateInput(**data)
            approval = await approval_service.create_approval(db_session, approval_input)
            approvals.append(approval)
        
        return approvals
    
    def test_list_approvals_success(self, client: TestClient, multiple_approvals):
        """Test successful approval listing."""
        response = client.get("/approvals")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3
        assert data["has_more"] is False
    
    def test_list_approvals_with_filters(self, client: TestClient, multiple_approvals):
        """Test approval listing with filters."""
        tenant_id = multiple_approvals[0].tenant_id
        
        response = client.get(f"/approvals?tenant_id={tenant_id}&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["has_more"] is True
    
    def test_list_approvals_pagination(self, client: TestClient, multiple_approvals):
        """Test approval listing pagination."""
        # First page
        response = client.get("/approvals?limit=2&offset=0")
        assert response.status_code == 200
        page1 = response.json()
        assert len(page1["items"]) == 2
        
        # Second page
        response = client.get("/approvals?limit=2&offset=2")
        assert response.status_code == 200
        page2 = response.json()
        assert len(page2["items"]) == 1


class TestDecisionMaking:
    """Test decision making functionality."""
    
    @pytest.fixture
    async def pending_approval(self, db_session: AsyncSession, sample_approval_data):
        """Create a pending approval for testing."""
        approval_input = ApprovalCreateInput(**sample_approval_data)
        approval = await approval_service.create_approval(db_session, approval_input)
        return approval
    
    def test_make_decision_approve(self, client: TestClient, pending_approval):
        """Test making an approve decision."""
        participant = pending_approval.participants[0]
        decision_data = {
            "decision_type": DecisionType.APPROVE,
            "comments": "Looks good to me"
        }
        
        response = client.post(
            f"/approvals/{pending_approval.id}/decision",
            json=decision_data,
            params={"user_id": participant.user_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["approval_completed"] is False  # Need both approvals
    
    def test_make_decision_reject(self, client: TestClient, pending_approval):
        """Test making a reject decision."""
        participant = pending_approval.participants[0]
        decision_data = {
            "decision_type": DecisionType.REJECT,
            "comments": "Needs revision"
        }
        
        response = client.post(
            f"/approvals/{pending_approval.id}/decision",
            json=decision_data,
            params={"user_id": participant.user_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["approval_completed"] is True  # Rejection completes immediately
        assert data["approval_status"] == ApprovalStatus.REJECTED
    
    def test_make_decision_completion_flow(self, client: TestClient, pending_approval):
        """Test complete approval flow with both participants."""
        # First participant approves
        participant1 = pending_approval.participants[0]
        decision_data = {"decision_type": DecisionType.APPROVE}
        
        response = client.post(
            f"/approvals/{pending_approval.id}/decision",
            json=decision_data,
            params={"user_id": participant1.user_id}
        )
        
        assert response.status_code == 200
        first_result = response.json()
        assert first_result["approval_completed"] is False
        
        # Second participant approves
        participant2 = pending_approval.participants[1]
        response = client.post(
            f"/approvals/{pending_approval.id}/decision",
            json=decision_data,
            params={"user_id": participant2.user_id}
        )
        
        assert response.status_code == 200
        second_result = response.json()
        assert second_result["approval_completed"] is True
        assert second_result["approval_status"] == ApprovalStatus.APPROVED
    
    def test_make_decision_invalid_participant(self, client: TestClient, pending_approval):
        """Test making decision with invalid participant."""
        decision_data = {"decision_type": DecisionType.APPROVE}
        
        response = client.post(
            f"/approvals/{pending_approval.id}/decision",
            json=decision_data,
            params={"user_id": "invalid_user"}
        )
        
        assert response.status_code == 400
    
    def test_make_decision_already_responded(self, client: TestClient, pending_approval):
        """Test making decision when participant already responded."""
        participant = pending_approval.participants[0]
        decision_data = {"decision_type": DecisionType.APPROVE}
        
        # First decision
        response = client.post(
            f"/approvals/{pending_approval.id}/decision",
            json=decision_data,
            params={"user_id": participant.user_id}
        )
        assert response.status_code == 200
        
        # Second decision (should fail)
        response = client.post(
            f"/approvals/{pending_approval.id}/decision",
            json=decision_data,
            params={"user_id": participant.user_id}
        )
        assert response.status_code == 409


class TestExpirationFlow:
    """Test approval expiration functionality."""
    
    @pytest.fixture
    async def expired_approval(self, db_session: AsyncSession, sample_approval_data):
        """Create an expired approval for testing."""
        # Create approval that expires in the past
        approval_input = ApprovalCreateInput(**sample_approval_data)
        approval = await approval_service.create_approval(db_session, approval_input)
        
        # Manually set expiry to past
        from app.models import Approval
        db_approval = await db_session.get(Approval, approval.id)
        db_approval.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        await db_session.commit()
        
        return approval
    
    def test_make_decision_on_expired_approval(self, client: TestClient, expired_approval):
        """Test making decision on expired approval."""
        participant = expired_approval.participants[0]
        decision_data = {"decision_type": DecisionType.APPROVE}
        
        response = client.post(
            f"/approvals/{expired_approval.id}/decision",
            json=decision_data,
            params={"user_id": participant.user_id}
        )
        
        assert response.status_code == 410  # Gone
    
    async def test_expire_approvals_task(self, db_session: AsyncSession, expired_approval):
        """Test the expire approvals background task."""
        # Run expiration task
        count = await approval_service.expire_approvals(db_session)
        
        assert count == 1
        
        # Verify approval is marked as expired
        updated_approval = await approval_service.get_approval(db_session, expired_approval.id)
        assert updated_approval.status == ApprovalStatus.EXPIRED


class TestPermissions:
    """Test permission and access control."""
    
    @pytest.fixture
    async def tenant_approval(self, db_session: AsyncSession, sample_approval_data):
        """Create approval for specific tenant."""
        data = sample_approval_data.copy()
        data["tenant_id"] = "specific_tenant"
        
        approval_input = ApprovalCreateInput(**data)
        approval = await approval_service.create_approval(db_session, approval_input)
        return approval
    
    def test_tenant_isolation(self, client: TestClient, tenant_approval):
        """Test that tenant isolation works properly."""
        # Access with correct tenant
        response = client.get(
            f"/approvals/{tenant_approval.id}?tenant_id=specific_tenant"
        )
        assert response.status_code == 200
        
        # Access with wrong tenant
        response = client.get(
            f"/approvals/{tenant_approval.id}?tenant_id=wrong_tenant"
        )
        assert response.status_code == 404
    
    def test_participant_restriction(self, client: TestClient, tenant_approval):
        """Test that only participants can make decisions."""
        decision_data = {"decision_type": DecisionType.APPROVE}
        
        # Non-participant tries to make decision
        response = client.post(
            f"/approvals/{tenant_approval.id}/decision",
            json=decision_data,
            params={"user_id": "non_participant"}
        )
        
        assert response.status_code == 400


class TestHealthAndStatus:
    """Test health and status endpoints."""
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
    
    def test_approval_status_endpoint(self, client: TestClient, sample_approval_data):
        """Test approval status endpoint."""
        # Create approval first
        create_response = client.post("/approvals", json=sample_approval_data)
        approval_id = create_response.json()["approval_id"]
        
        # Get status
        response = client.get(f"/approvals/{approval_id}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["approval_id"] == approval_id
        assert "status" in data
        assert "approval_progress" in data
        assert "participants_summary" in data


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_invalid_approval_id_format(self, client: TestClient):
        """Test handling of invalid UUID format."""
        response = client.get("/approvals/invalid-uuid")
        
        assert response.status_code == 422  # Validation error
    
    def test_missing_required_fields(self, client: TestClient):
        """Test handling of missing required fields."""
        incomplete_data = {
            "tenant_id": "test",
            "approval_type": ApprovalType.IEP_DOCUMENT
            # Missing required fields
        }
        
        response = client.post("/approvals", json=incomplete_data)
        
        assert response.status_code == 422
    
    def test_invalid_enum_values(self, client: TestClient, sample_approval_data):
        """Test handling of invalid enum values."""
        sample_approval_data["approval_type"] = "invalid_type"
        
        response = client.post("/approvals", json=sample_approval_data)
        
        assert response.status_code == 422
