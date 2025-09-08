"""
Core business logic tests for IEP Service.
Note: Full GraphQL integration tests require strawberry-graphql installation.
"""

import json
from datetime import date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from app.approval_service import approval_service
from app.crdt_manager import CrdtOperation, crdt_manager
from app.enums import AccommodationType, ApprovalStatus, EventType, GoalType, IepStatus
from app.event_service import event_service
from app.main import app
from app.schema import AccommodationInput, GoalInput
from fastapi.testclient import TestClient

# Create test client
client = TestClient(app)


@pytest.fixture
def sample_iep_data():
    """Sample IEP data for testing."""
    return {
        "student_id": "student_123",
        "student_name": "John Doe",
        "school_year": "2024-2025",
        "effective_date": date(2024, 9, 1),
        "expiry_date": date(2025, 8, 31),
        "meeting_date": date(2024, 8, 15),
        "present_levels": "Student demonstrates grade-level reading skills...",
        "transition_services": "Career exploration activities...",
        "special_factors": ["behavioral_supports"],
        "placement_details": "General education classroom with support",
    }


@pytest.fixture
def sample_goal_data():
    """Sample goal data for testing."""
    return {
        "goal_type": GoalType.ACADEMIC,
        "title": "Reading Comprehension Goal",
        "description": "Improve reading comprehension skills",
        "measurable_criteria": "80% accuracy on grade-level passages",
        "target_date": date(2025, 6, 1),
        "baseline_data": "Currently at 60% accuracy",
        "responsible_staff": ["teacher_1", "aide_1"],
    }


@pytest.fixture
def sample_accommodation_data():
    """Sample accommodation data for testing."""
    return {
        "accommodation_type": AccommodationType.INSTRUCTIONAL,
        "title": "Extended Time",
        "description": "Provide 50% additional time for assignments",
        "implementation_notes": "Apply to all written work",
        "applicable_settings": ["classroom", "testing"],
        "frequency": "daily",
        "duration": "ongoing",
        "responsible_staff": ["teacher_1"],
    }


@pytest.fixture(autouse=True)
def reset_state():
    """Reset application state before each test."""
    crdt_manager.documents.clear()
    crdt_manager.operation_logs.clear()
    yield
    crdt_manager.documents.clear()
    crdt_manager.operation_logs.clear()


@pytest.fixture
def mock_services():
    """Mock external services."""
    with (
        patch.object(event_service, "publish_event", new_callable=AsyncMock) as mock_event,
        patch.object(
            approval_service, "submit_for_approval", new_callable=AsyncMock
        ) as mock_approval,
    ):
        mock_event.return_value = True
        mock_approval.return_value = {
            "success": True,
            "approval_request_id": "approval_123",
            "message": "Submitted for approval",
        }

        yield {"event_service": mock_event, "approval_service": mock_approval}


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self):
        """Test health check returns 200 and correct information."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "iep-svc"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
        assert "graphql_endpoint" in data


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_endpoint(self):
        """Test root endpoint returns service information."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "IEP Service"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        assert "features" in data
        assert "GraphQL API with Strawberry" in data["features"]


class TestCrdtDocumentManager:
    """Test CRDT document manager functionality."""

    def test_create_document(self, sample_iep_data):
        """Test creating a new IEP document."""
        author_id = "teacher_123"

        iep_doc = crdt_manager.create_document(sample_iep_data, author_id)

        assert iep_doc.id is not None
        assert iep_doc.student_id == sample_iep_data["student_id"]
        assert iep_doc.student_name == sample_iep_data["student_name"]
        assert iep_doc.status == IepStatus.DRAFT
        assert iep_doc.created_by == author_id
        assert iep_doc.version == 1
        assert author_id in iep_doc.vector_clock
        assert iep_doc.vector_clock[author_id] == 1

    def test_apply_update_operation(self, sample_iep_data):
        """Test applying update operations."""
        author_id = "teacher_123"
        iep_doc = crdt_manager.create_document(sample_iep_data, author_id)

        # Create update operation
        operation = CrdtOperation(
            operation_type="update",
            path="present_levels",
            value="Updated present levels content",
            author=author_id,
            timestamp=datetime.utcnow(),
        )

        success, error = crdt_manager.apply_operation(iep_doc.id, operation)

        assert success is True
        assert error is None
        assert iep_doc.present_levels == "Updated present levels content"
        assert iep_doc.version == 2
        assert iep_doc.vector_clock[author_id] == 2

    def test_apply_insert_goal_operation(self, sample_iep_data, sample_goal_data):
        """Test inserting a goal via CRDT operation."""
        author_id = "teacher_123"
        iep_doc = crdt_manager.create_document(sample_iep_data, author_id)

        # Prepare goal data for insertion
        goal_json = json.dumps(
            {
                "goal_type": sample_goal_data["goal_type"].value,
                "title": sample_goal_data["title"],
                "description": sample_goal_data["description"],
                "measurable_criteria": sample_goal_data["measurable_criteria"],
                "target_date": sample_goal_data["target_date"].isoformat(),
                "baseline_data": sample_goal_data["baseline_data"],
                "responsible_staff": sample_goal_data["responsible_staff"],
            }
        )

        operation = CrdtOperation(
            operation_type="insert",
            path="goals",
            value=goal_json,
            position=0,
            author=author_id,
            timestamp=datetime.utcnow(),
        )

        success, error = crdt_manager.apply_operation(iep_doc.id, operation)

        assert success is True
        assert error is None
        assert len(iep_doc.goals) == 1
        assert iep_doc.goals[0].title == sample_goal_data["title"]

    def test_apply_delete_operation(self, sample_iep_data):
        """Test deleting items via CRDT operation."""
        author_id = "teacher_123"
        iep_doc = crdt_manager.create_document(sample_iep_data, author_id)

        # Add a special factor first
        iep_doc.special_factors.append("test_factor")

        # Delete the special factor
        operation = CrdtOperation(
            operation_type="delete",
            path="special_factors",
            position=1,  # Index of the added factor
            author=author_id,
            timestamp=datetime.utcnow(),
        )

        success, error = crdt_manager.apply_operation(iep_doc.id, operation)

        assert success is True
        assert error is None
        assert "test_factor" not in iep_doc.special_factors


class TestGraphQLQueries:
    """Test GraphQL query operations."""

    def test_query_iep_by_id(self, sample_iep_data):
        """Test querying IEP by ID."""
        # Create an IEP first
        iep_doc = crdt_manager.create_document(sample_iep_data, "teacher_123")

        query = f"""
        query {{
            iep(id: "{iep_doc.id}") {{
                id
                studentId
                studentName
                status
                schoolYear
                goals {{
                    id
                    title
                }}
                accommodations {{
                    id
                    title
                }}
            }}
        }}
        """

        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 200

        data = response.json()
        assert "errors" not in data
        assert data["data"]["iep"]["id"] == iep_doc.id
        assert data["data"]["iep"]["studentName"] == sample_iep_data["student_name"]

    def test_query_student_ieps(self, sample_iep_data):
        """Test querying IEPs for a specific student."""
        student_id = sample_iep_data["student_id"]

        # Create multiple IEPs for the student
        iep1 = crdt_manager.create_document(sample_iep_data, "teacher_123")
        iep2_data = sample_iep_data.copy()
        iep2_data["school_year"] = "2023-2024"
        iep2 = crdt_manager.create_document(iep2_data, "teacher_123")

        query = f"""
        query {{
            studentIeps(studentId: "{student_id}") {{
                id
                studentId
                schoolYear
                status
            }}
        }}
        """

        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 200

        data = response.json()
        assert "errors" not in data
        assert len(data["data"]["studentIeps"]) == 2

        # Verify both IEPs are returned
        iep_ids = [iep["id"] for iep in data["data"]["studentIeps"]]
        assert iep1.id in iep_ids
        assert iep2.id in iep_ids


class TestGraphQLMutations:
    """Test GraphQL mutation operations."""

    def test_create_iep_mutation(
        self, sample_iep_data, sample_goal_data, sample_accommodation_data, mock_services
    ):
        """Test creating an IEP via GraphQL mutation."""
        mutation = """
        mutation CreateIep($input: IepDocInput!, $createdBy: String!) {
            createIep(input: $input, createdBy: $createdBy) {
                success
                message
                iep {
                    id
                    studentName
                    status
                    goals {
                        title
                        goalType
                    }
                    accommodations {
                        title
                        accommodationType
                    }
                }
                errors
            }
        }
        """

        variables = {
            "input": {
                "studentId": sample_iep_data["student_id"],
                "studentName": sample_iep_data["student_name"],
                "schoolYear": sample_iep_data["school_year"],
                "effectiveDate": sample_iep_data["effective_date"].isoformat(),
                "expiryDate": sample_iep_data["expiry_date"].isoformat(),
                "meetingDate": sample_iep_data["meeting_date"].isoformat(),
                "presentLevels": sample_iep_data["present_levels"],
                "transitionServices": sample_iep_data["transition_services"],
                "specialFactors": sample_iep_data["special_factors"],
                "placementDetails": sample_iep_data["placement_details"],
                "goals": [
                    {
                        "goalType": sample_goal_data["goal_type"].value.upper(),
                        "title": sample_goal_data["title"],
                        "description": sample_goal_data["description"],
                        "measurableCriteria": sample_goal_data["measurable_criteria"],
                        "targetDate": sample_goal_data["target_date"].isoformat(),
                        "baselineData": sample_goal_data["baseline_data"],
                        "responsibleStaff": sample_goal_data["responsible_staff"],
                    }
                ],
                "accommodations": [
                    {
                        "accommodationType": sample_accommodation_data[
                            "accommodation_type"
                        ].value.upper(),
                        "title": sample_accommodation_data["title"],
                        "description": sample_accommodation_data["description"],
                        "implementationNotes": sample_accommodation_data["implementation_notes"],
                        "applicableSettings": sample_accommodation_data["applicable_settings"],
                        "frequency": sample_accommodation_data["frequency"],
                        "duration": sample_accommodation_data["duration"],
                        "responsibleStaff": sample_accommodation_data["responsible_staff"],
                    }
                ],
            },
            "createdBy": "teacher_123",
        }

        response = client.post("/graphql", json={"query": mutation, "variables": variables})
        assert response.status_code == 200

        data = response.json()
        assert "errors" not in data
        assert data["data"]["createIep"]["success"] is True
        assert data["data"]["createIep"]["iep"]["studentName"] == sample_iep_data["student_name"]
        assert len(data["data"]["createIep"]["iep"]["goals"]) == 1
        assert len(data["data"]["createIep"]["iep"]["accommodations"]) == 1

        # Verify event was published
        mock_services["event_service"].assert_called()

    def test_save_draft_mutation(self, sample_iep_data, mock_services):
        """Test saving draft changes via CRDT operations."""
        # Create an IEP first
        iep_doc = crdt_manager.create_document(sample_iep_data, "teacher_123")

        mutation = """
        mutation SaveDraft($iepId: String!, $operations: [CrdtOperation!]!, $updatedBy: String!) {
            saveDraft(iepId: $iepId, operations: $operations, updatedBy: $updatedBy) {
                success
                message
                iep {
                    id
                    presentLevels
                    version
                }
                errors
            }
        }
        """

        variables = {
            "iepId": iep_doc.id,
            "operations": [
                {
                    "operationType": "update",
                    "path": "present_levels",
                    "value": "Updated present levels via CRDT",
                    "author": "teacher_123",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ],
            "updatedBy": "teacher_123",
        }

        response = client.post("/graphql", json={"query": mutation, "variables": variables})
        assert response.status_code == 200

        data = response.json()
        assert "errors" not in data
        assert data["data"]["saveDraft"]["success"] is True
        assert (
            data["data"]["saveDraft"]["iep"]["presentLevels"] == "Updated present levels via CRDT"
        )
        assert data["data"]["saveDraft"]["iep"]["version"] == 2

    def test_submit_for_approval_mutation(
        self, sample_iep_data, sample_goal_data, sample_accommodation_data, mock_services
    ):
        """Test submitting IEP for approval."""
        # Create a complete IEP
        iep_doc = crdt_manager.create_document(sample_iep_data, "teacher_123")

        # Add goal and accommodation to make it complete
        from app.resolvers import Mutation

        Mutation()

        # Add via helper methods to ensure completeness
        GoalInput(**sample_goal_data)
        AccommodationInput(**sample_accommodation_data)

        # Use CRDT manager to add directly for test
        goal_json = json.dumps(
            {
                "goal_type": sample_goal_data["goal_type"].value,
                "title": sample_goal_data["title"],
                "description": sample_goal_data["description"],
                "measurable_criteria": sample_goal_data["measurable_criteria"],
                "target_date": sample_goal_data["target_date"].isoformat(),
                "baseline_data": sample_goal_data["baseline_data"],
                "responsible_staff": sample_goal_data["responsible_staff"],
            }
        )

        acc_json = json.dumps(
            {
                "accommodation_type": sample_accommodation_data["accommodation_type"].value,
                "title": sample_accommodation_data["title"],
                "description": sample_accommodation_data["description"],
                "implementation_notes": sample_accommodation_data["implementation_notes"],
                "applicable_settings": sample_accommodation_data["applicable_settings"],
                "frequency": sample_accommodation_data["frequency"],
                "duration": sample_accommodation_data["duration"],
                "responsible_staff": sample_accommodation_data["responsible_staff"],
            }
        )

        # Insert goal and accommodation
        crdt_manager.apply_operation(
            iep_doc.id,
            CrdtOperation(
                operation_type="insert",
                path="goals",
                value=goal_json,
                author="teacher_123",
                timestamp=datetime.utcnow(),
            ),
        )

        crdt_manager.apply_operation(
            iep_doc.id,
            CrdtOperation(
                operation_type="insert",
                path="accommodations",
                value=acc_json,
                author="teacher_123",
                timestamp=datetime.utcnow(),
            ),
        )

        mutation = """
        mutation SubmitForApproval($iepId: String!, $submittedBy: String!) {
            submitForApproval(iepId: $iepId, submittedBy: $submittedBy) {
                success
                message
                approvalId
                status
                errors
            }
        }
        """

        variables = {"iepId": iep_doc.id, "submittedBy": "teacher_123"}

        response = client.post("/graphql", json={"query": mutation, "variables": variables})
        assert response.status_code == 200

        data = response.json()
        assert "errors" not in data
        assert data["data"]["submitForApproval"]["success"] is True
        assert data["data"]["submitForApproval"]["approvalId"] == "approval_123"

        # Verify approval service was called
        mock_services["approval_service"].assert_called_once()

        # Verify IEP status changed
        updated_iep = crdt_manager.get_document(iep_doc.id)
        assert updated_iep.status == IepStatus.PENDING_APPROVAL


class TestApprovalWorkflow:
    """Test approval workflow functionality."""

    def test_approval_webhook_processing(self, sample_iep_data):
        """Test processing approval webhooks."""
        # Create an IEP in pending approval status
        iep_doc = crdt_manager.create_document(sample_iep_data, "teacher_123")
        iep_doc.status = IepStatus.PENDING_APPROVAL

        # Mock approval webhook data
        webhook_data = {
            "event_type": "APPROVAL_COMPLETED",
            "data": {
                "resource_id": iep_doc.id,
                "approvals": [
                    {
                        "approver_id": "coordinator_1",
                        "role": "special_education_coordinator",
                        "approved_at": datetime.utcnow().isoformat(),
                        "comments": "Approved - good goals",
                    },
                    {
                        "approver_id": "admin_1",
                        "role": "administrator",
                        "approved_at": datetime.utcnow().isoformat(),
                        "comments": "Administrative approval",
                    },
                ],
                "completed_by": "system",
            },
        }

        response = client.post("/webhooks/approval", json=webhook_data)
        assert response.status_code == 200

        # Verify IEP status updated
        updated_iep = crdt_manager.get_document(iep_doc.id)
        assert updated_iep.status == "approved"
        assert len(updated_iep.approval_records) == 2
        assert updated_iep.pending_approval_count == 0

    def test_approval_rejection_webhook(self, sample_iep_data):
        """Test processing approval rejection webhook."""
        # Create an IEP in pending approval status
        iep_doc = crdt_manager.create_document(sample_iep_data, "teacher_123")
        iep_doc.status = IepStatus.PENDING_APPROVAL

        # Mock rejection webhook data
        webhook_data = {
            "event_type": "APPROVAL_REJECTED",
            "data": {
                "resource_id": iep_doc.id,
                "rejection": {
                    "rejected_by": "coordinator_1",
                    "role": "special_education_coordinator",
                    "rejected_at": datetime.utcnow().isoformat(),
                    "reason": "Goals need more specificity",
                    "comments": "Please revise goal measurements",
                },
            },
        }

        response = client.post("/webhooks/approval", json=webhook_data)
        assert response.status_code == 200

        # Verify IEP status updated
        updated_iep = crdt_manager.get_document(iep_doc.id)
        assert updated_iep.status == "rejected"
        assert len(updated_iep.approval_records) == 1
        assert updated_iep.approval_records[0].status == ApprovalStatus.REJECTED
        assert updated_iep.approval_records[0].rejection_reason == "Goals need more specificity"


class TestEventPublishing:
    """Test event publishing functionality."""

    @pytest.mark.asyncio
    async def test_publish_iep_updated_event(self):
        """Test publishing IEP_UPDATED event."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200

            success = await event_service.publish_iep_updated(
                iep_id="iep_123",
                student_id="student_123",
                status="approved",
                updated_by="system",
                changes=["status", "approval_records"],
            )

            assert success is True
            mock_post.assert_called_once()

            # Verify event payload structure
            call_args = mock_post.call_args
            event_data = call_args.kwargs["json"]

            assert event_data["event_type"] == EventType.IEP_UPDATED.value
            assert event_data["resource_id"] == "iep_123"
            assert event_data["data"]["student_id"] == "student_123"
            assert event_data["data"]["status"] == "approved"
            assert event_data["data"]["changes"] == ["status", "approval_records"]


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_nonexistent_iep_query(self):
        """Test querying nonexistent IEP."""
        query = """
        query {
            iep(id: "nonexistent") {
                id
                studentName
            }
        }
        """

        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 200

        data = response.json()
        assert "errors" not in data
        assert data["data"]["iep"] is None

    def test_invalid_crdt_operation(self, sample_iep_data):
        """Test applying invalid CRDT operation."""
        iep_doc = crdt_manager.create_document(sample_iep_data, "teacher_123")

        # Try to apply invalid operation
        operation = CrdtOperation(
            operation_type="invalid_op",
            path="unknown_field",
            value="some_value",
            author="teacher_123",
            timestamp=datetime.utcnow(),
        )

        success, error = crdt_manager.apply_operation(iep_doc.id, operation)

        assert success is False
        assert "Unknown operation type" in error

    def test_submit_incomplete_iep(self, sample_iep_data, mock_services):
        """Test submitting incomplete IEP for approval."""
        # Create IEP without goals/accommodations
        iep_doc = crdt_manager.create_document(sample_iep_data, "teacher_123")

        mutation = """
        mutation SubmitForApproval($iepId: String!, $submittedBy: String!) {
            submitForApproval(iepId: $iepId, submittedBy: $submittedBy) {
                success
                message
                errors
            }
        }
        """

        variables = {"iepId": iep_doc.id, "submittedBy": "teacher_123"}

        response = client.post("/graphql", json={"query": mutation, "variables": variables})
        assert response.status_code == 200

        data = response.json()
        assert "errors" not in data
        assert data["data"]["submitForApproval"]["success"] is False
        assert "incomplete" in data["data"]["submitForApproval"]["message"].lower()
        assert len(data["data"]["submitForApproval"]["errors"]) > 0


class TestConcurrencyAndSync:
    """Test concurrent editing and synchronization."""

    def test_concurrent_operations(self, sample_iep_data):
        """Test applying operations from multiple users concurrently."""
        iep_doc = crdt_manager.create_document(sample_iep_data, "teacher_1")

        # Simulate operations from different users
        op1 = CrdtOperation(
            operation_type="update",
            path="present_levels",
            value="Updated by teacher 1",
            author="teacher_1",
            timestamp=datetime.utcnow(),
        )

        op2 = CrdtOperation(
            operation_type="update",
            path="transition_services",
            value="Updated by teacher 2",
            author="teacher_2",
            timestamp=datetime.utcnow(),
        )

        # Apply operations
        success1, _ = crdt_manager.apply_operation(iep_doc.id, op1)
        success2, _ = crdt_manager.apply_operation(iep_doc.id, op2)

        assert success1 is True
        assert success2 is True

        # Verify vector clock reflects both authors
        assert "teacher_1" in iep_doc.vector_clock
        assert "teacher_2" in iep_doc.vector_clock
        assert iep_doc.vector_clock["teacher_1"] >= 1
        assert iep_doc.vector_clock["teacher_2"] >= 1

        # Verify both updates applied
        assert iep_doc.present_levels == "Updated by teacher 1"
        assert iep_doc.transition_services == "Updated by teacher 2"
