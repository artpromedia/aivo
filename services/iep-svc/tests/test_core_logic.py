"""
Core business logic tests for IEP Service.
Tests CRDT operations, approval workflow, and event publishing.
"""
import pytest
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import json
from uuid import uuid4

from app.enums import IepStatus, GoalType, AccommodationType, ApprovalStatus, EventType
from app.crdt_manager import crdt_manager
from app.approval_service import approval_service
from app.event_service import event_service


# Sample test data
sample_iep_data = {
    "student_id": "student123",
    "title": "IEP for John Doe",
    "start_date": date.today(),
    "end_date": date.today() + timedelta(days=365),
    "status": IepStatus.DRAFT.value,
    "goals": [],
    "accommodations": []
}

sample_goal_data = {
    "title": "Improve reading comprehension",
    "description": "Student will improve reading comprehension skills",
    "type": GoalType.ACADEMIC.value,
    "target_date": date.today() + timedelta(days=180),
    "criteria": "80% accuracy on grade-level texts",
    "current_level": "Below grade level",
    "is_active": True
}

sample_accommodation_data = {
    "title": "Extended time",
    "description": "Provide extended time for assignments and tests",
    "type": AccommodationType.INSTRUCTIONAL.value,
    "implementation": "Provide 50% additional time",
    "frequency": "As needed",
    "is_active": True
}


class TestCrdtManager:
    """Test CRDT document management functionality."""
    
    @pytest.fixture
    def sample_document(self):
        """Create a sample IEP document for testing."""
        doc_id = str(uuid4())
        document = {
            "id": doc_id,
            "content": sample_iep_data.copy()
        }
        crdt_manager.documents[doc_id] = document
        crdt_manager.vector_clocks[doc_id] = {}
        crdt_manager.operation_logs[doc_id] = []
        return document

    def test_create_document(self):
        """Test creating a new CRDT document."""
        doc_id = str(uuid4())
        content = sample_iep_data.copy()
        
        document = crdt_manager.create_document(doc_id, content)
        
        assert document["id"] == doc_id
        assert document["content"] == content
        assert doc_id in crdt_manager.documents
        assert doc_id in crdt_manager.vector_clocks
        assert doc_id in crdt_manager.operation_logs

    def test_apply_update_operation(self, sample_document):
        """Test applying update operations to CRDT document."""
        doc_id = sample_document["id"]
        
        # Create update operation
        operation = {
            "type": "update",
            "path": "title",
            "value": "Updated IEP Title",
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": "client1"
        }
        
        result = crdt_manager.apply_operation(doc_id, operation)
        
        assert result is True
        assert crdt_manager.documents[doc_id]["content"]["title"] == "Updated IEP Title"
        assert len(crdt_manager.operation_logs[doc_id]) == 1

    def test_apply_insert_operation(self, sample_document):
        """Test applying insert operations to CRDT document."""
        doc_id = sample_document["id"]
        
        # Insert goal operation
        operation = {
            "type": "insert",
            "path": "goals",
            "value": sample_goal_data.copy(),
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": "client1"
        }
        
        result = crdt_manager.apply_operation(doc_id, operation)
        
        assert result is True
        assert len(crdt_manager.documents[doc_id]["content"]["goals"]) == 1
        assert crdt_manager.documents[doc_id]["content"]["goals"][0]["title"] == sample_goal_data["title"]

    def test_apply_delete_operation(self, sample_document):
        """Test applying delete operations to CRDT document."""
        doc_id = sample_document["id"]
        
        # First insert a goal to delete
        crdt_manager.documents[doc_id]["content"]["goals"] = [sample_goal_data.copy()]
        
        # Delete operation
        operation = {
            "type": "delete",
            "path": "goals.0",
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": "client1"
        }
        
        result = crdt_manager.apply_operation(doc_id, operation)
        
        assert result is True
        assert len(crdt_manager.documents[doc_id]["content"]["goals"]) == 0

    def test_vector_clock_advancement(self, sample_document):
        """Test vector clock advancement with operations."""
        doc_id = sample_document["id"]
        client_id = "client1"
        
        # Apply multiple operations
        for i in range(3):
            operation = {
                "type": "update",
                "path": f"field_{i}",
                "value": f"value_{i}",
                "timestamp": datetime.utcnow().isoformat(),
                "client_id": client_id
            }
            crdt_manager.apply_operation(doc_id, operation)
        
        # Check vector clock advancement
        assert crdt_manager.vector_clocks[doc_id][client_id] == 3

    def test_concurrent_operations_resolution(self, sample_document):
        """Test conflict resolution for concurrent operations."""
        doc_id = sample_document["id"]
        
        # Simulate concurrent operations from different clients
        op1 = {
            "type": "update",
            "path": "title",
            "value": "Title from Client 1",
            "timestamp": "2024-01-01T10:00:00",
            "client_id": "client1"
        }
        
        op2 = {
            "type": "update",
            "path": "title",
            "value": "Title from Client 2",
            "timestamp": "2024-01-01T10:00:01",  # Later timestamp
            "client_id": "client2"
        }
        
        # Apply operations
        crdt_manager.apply_operation(doc_id, op1)
        crdt_manager.apply_operation(doc_id, op2)
        
        # Later timestamp should win
        assert crdt_manager.documents[doc_id]["content"]["title"] == "Title from Client 2"


class TestApprovalService:
    """Test approval workflow functionality."""
    
    @pytest.mark.asyncio
    async def test_submit_for_approval_success(self):
        """Test successful approval submission."""
        iep_id = str(uuid4())
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"approval_id": "approval123"}
            
            result = await approval_service.submit_for_approval(iep_id, sample_iep_data)
            
            assert result["approval_id"] == "approval123"
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_for_approval_failure(self):
        """Test approval submission failure."""
        iep_id = str(uuid4())
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value.status_code = 500
            
            result = await approval_service.submit_for_approval(iep_id, sample_iep_data)
            
            assert result is None

    @pytest.mark.asyncio
    async def test_process_approval_webhook_approved(self):
        """Test processing approval webhook for approved status."""
        with patch('app.approval_service.event_service.publish_event') as mock_publish:
            webhook_data = {
                "approval_id": "approval123",
                "status": ApprovalStatus.APPROVED.value,
                "document_id": str(uuid4()),
                "approved_by": "admin@example.com",
                "approved_at": datetime.utcnow().isoformat()
            }
            
            await approval_service.process_approval_webhook(webhook_data)
            
            # Should publish IEP_APPROVED event
            mock_publish.assert_called()
            call_args = mock_publish.call_args[1]
            assert call_args["event_type"] == EventType.IEP_APPROVED

    @pytest.mark.asyncio
    async def test_process_approval_webhook_rejected(self):
        """Test processing approval webhook for rejected status."""
        with patch('app.approval_service.event_service.publish_event') as mock_publish:
            webhook_data = {
                "approval_id": "approval123",
                "status": ApprovalStatus.REJECTED.value,
                "document_id": str(uuid4()),
                "rejected_by": "admin@example.com",
                "rejected_at": datetime.utcnow().isoformat(),
                "rejection_reason": "Incomplete information"
            }
            
            await approval_service.process_approval_webhook(webhook_data)
            
            # Should publish IEP_REJECTED event
            mock_publish.assert_called()
            call_args = mock_publish.call_args[1]
            assert call_args["event_type"] == EventType.IEP_REJECTED


class TestEventService:
    """Test event publishing functionality."""
    
    @pytest.mark.asyncio
    async def test_publish_iep_created_event(self):
        """Test publishing IEP created event."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value.status_code = 200
            
            await event_service.publish_event(
                event_type=EventType.IEP_CREATED,
                iep_id=str(uuid4()),
                data=sample_iep_data
            )
            
            mock_post.assert_called_once()
            call_args = mock_post.call_args[1]
            assert call_args["json"]["event_type"] == EventType.IEP_CREATED.value

    @pytest.mark.asyncio
    async def test_publish_iep_updated_event(self):
        """Test publishing IEP updated event."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value.status_code = 200
            
            await event_service.publish_event(
                event_type=EventType.IEP_UPDATED,
                iep_id=str(uuid4()),
                data=sample_iep_data,
                changes={"title": "Updated Title"}
            )
            
            mock_post.assert_called_once()
            call_args = mock_post.call_args[1]
            assert call_args["json"]["event_type"] == EventType.IEP_UPDATED.value
            assert "changes" in call_args["json"]["data"]

    @pytest.mark.asyncio
    async def test_publish_goal_added_event(self):
        """Test publishing goal added event."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value.status_code = 200
            
            await event_service.publish_event(
                event_type=EventType.GOAL_ADDED,
                iep_id=str(uuid4()),
                data={"goal": sample_goal_data}
            )
            
            mock_post.assert_called_once()
            call_args = mock_post.call_args[1]
            assert call_args["json"]["event_type"] == EventType.GOAL_ADDED.value

    @pytest.mark.asyncio
    async def test_publish_accommodation_added_event(self):
        """Test publishing accommodation added event."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value.status_code = 200
            
            await event_service.publish_event(
                event_type=EventType.ACCOMMODATION_ADDED,
                iep_id=str(uuid4()),
                data={"accommodation": sample_accommodation_data}
            )
            
            mock_post.assert_called_once()
            call_args = mock_post.call_args[1]
            assert call_args["json"]["event_type"] == EventType.ACCOMMODATION_ADDED.value

    @pytest.mark.asyncio
    async def test_publish_event_failure_handling(self):
        """Test event publishing failure handling."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = Exception("Network error")
            
            # Should not raise exception
            await event_service.publish_event(
                event_type=EventType.IEP_CREATED,
                iep_id=str(uuid4()),
                data=sample_iep_data
            )
            
            mock_post.assert_called_once()


class TestIntegrationWorkflow:
    """Test integrated workflow scenarios."""
    
    @pytest.mark.asyncio
    async def test_complete_iep_workflow(self):
        """Test complete IEP creation to approval workflow."""
        doc_id = str(uuid4())
        
        # 1. Create IEP document
        document = crdt_manager.create_document(doc_id, sample_iep_data.copy())
        assert document["content"]["status"] == IepStatus.DRAFT.value
        
        # 2. Add goal via CRDT operation
        goal_operation = {
            "type": "insert",
            "path": "goals",
            "value": sample_goal_data.copy(),
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": "client1"
        }
        crdt_manager.apply_operation(doc_id, goal_operation)
        assert len(document["content"]["goals"]) == 1
        
        # 3. Add accommodation via CRDT operation
        acc_operation = {
            "type": "insert",
            "path": "accommodations",
            "value": sample_accommodation_data.copy(),
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": "client1"
        }
        crdt_manager.apply_operation(doc_id, acc_operation)
        assert len(document["content"]["accommodations"]) == 1
        
        # 4. Submit for approval
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"approval_id": "approval123"}
            
            result = await approval_service.submit_for_approval(doc_id, document["content"])
            assert result["approval_id"] == "approval123"
        
        # 5. Process approval webhook
        with patch('app.approval_service.event_service.publish_event') as mock_publish:
            webhook_data = {
                "approval_id": "approval123",
                "status": ApprovalStatus.APPROVED.value,
                "document_id": doc_id,
                "approved_by": "admin@example.com",
                "approved_at": datetime.utcnow().isoformat()
            }
            
            await approval_service.process_approval_webhook(webhook_data)
            
            # Should publish approval event
            mock_publish.assert_called()

    @pytest.mark.asyncio
    async def test_concurrent_editing_scenario(self):
        """Test concurrent editing scenario with multiple clients."""
        doc_id = str(uuid4())
        
        # Create document
        document = crdt_manager.create_document(doc_id, sample_iep_data.copy())
        
        # Simulate concurrent edits from multiple clients
        operations = [
            {
                "type": "update",
                "path": "title",
                "value": "Title from Client 1",
                "timestamp": "2024-01-01T10:00:00",
                "client_id": "client1"
            },
            {
                "type": "insert",
                "path": "goals",
                "value": sample_goal_data.copy(),
                "timestamp": "2024-01-01T10:00:01",
                "client_id": "client2"
            },
            {
                "type": "update",
                "path": "title",
                "value": "Title from Client 3",
                "timestamp": "2024-01-01T10:00:02",
                "client_id": "client3"
            }
        ]
        
        # Apply all operations
        for op in operations:
            crdt_manager.apply_operation(doc_id, op)
        
        # Check final state
        final_doc = crdt_manager.documents[doc_id]["content"]
        assert final_doc["title"] == "Title from Client 3"  # Latest timestamp wins
        assert len(final_doc["goals"]) == 1
        assert len(crdt_manager.operation_logs[doc_id]) == 3
        
        # Check vector clocks
        assert crdt_manager.vector_clocks[doc_id]["client1"] == 1
        assert crdt_manager.vector_clocks[doc_id]["client2"] == 1
        assert crdt_manager.vector_clocks[doc_id]["client3"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
