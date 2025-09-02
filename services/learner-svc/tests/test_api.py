"""
API integration tests for learner service.
"""
import pytest
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Guardian, Teacher, Tenant


class TestLearnerAPI:
    """Test learner API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_learner_api(
        self, 
        client: AsyncClient,
        sample_guardian: Guardian
    ):
        """Test creating a learner via API."""
        learner_data = {
            "first_name": "API",
            "last_name": "Test",
            "email": "api.test@example.com",
            "dob": "2015-06-15",
            "provision_source": "parent",
            "guardian_id": sample_guardian.id
        }
        
        response = await client.post("/learners", json=learner_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["first_name"] == "API"
        assert data["last_name"] == "Test"
        assert data["email"] == "api.test@example.com"
        assert data["dob"] == "2015-06-15"
        assert data["provision_source"] == "parent"
        assert data["guardian_id"] == sample_guardian.id
        assert data["grade_default"] in [5, 6]  # Based on 2025 school year
        assert data["id"] is not None
    
    @pytest.mark.asyncio
    async def test_get_learner_api(
        self, 
        client: AsyncClient,
        sample_guardian: Guardian
    ):
        """Test getting a learner via API."""
        # Create learner first
        learner_data = {
            "first_name": "Get",
            "last_name": "Test",
            "dob": "2015-06-15",
            "provision_source": "parent",
            "guardian_id": sample_guardian.id
        }
        
        create_response = await client.post("/learners", json=learner_data)
        assert create_response.status_code == 201
        learner_id = create_response.json()["id"]
        
        # Get learner
        response = await client.get(f"/learners/{learner_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == learner_id
        assert data["first_name"] == "Get"
        assert data["last_name"] == "Test"
        assert data["guardian"] is not None
        assert data["guardian"]["id"] == sample_guardian.id
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_learner(self, client: AsyncClient):
        """Test getting a non-existent learner."""
        response = await client.get("/learners/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_learners_by_guardian_api(
        self, 
        client: AsyncClient,
        sample_guardian: Guardian
    ):
        """Test getting learners by guardian via API."""
        # Create multiple learners for the same guardian
        learner_data_1 = {
            "first_name": "Child",
            "last_name": "One",
            "dob": "2015-06-15",
            "provision_source": "parent",
            "guardian_id": sample_guardian.id
        }
        
        learner_data_2 = {
            "first_name": "Child",
            "last_name": "Two",
            "dob": "2017-03-10",
            "provision_source": "parent",
            "guardian_id": sample_guardian.id
        }
        
        await client.post("/learners", json=learner_data_1)
        await client.post("/learners", json=learner_data_2)
        
        # Get learners by guardian
        response = await client.get(f"/guardians/{sample_guardian.id}/learners")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        names = [(l["first_name"], l["last_name"]) for l in data]
        assert ("Child", "One") in names
        assert ("Child", "Two") in names
    
    @pytest.mark.asyncio
    async def test_update_learner_api(
        self, 
        client: AsyncClient,
        sample_guardian: Guardian
    ):
        """Test updating a learner via API."""
        # Create learner first
        learner_data = {
            "first_name": "Original",
            "last_name": "Name",
            "dob": "2015-06-15",
            "provision_source": "parent",
            "guardian_id": sample_guardian.id
        }
        
        create_response = await client.post("/learners", json=learner_data)
        learner_id = create_response.json()["id"]
        
        # Update learner
        update_data = {
            "first_name": "Updated",
            "grade_current": 5
        }
        
        response = await client.put(f"/learners/{learner_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"  # Unchanged
        assert data["grade_current"] == 5
    
    @pytest.mark.asyncio
    async def test_assign_teacher_api(
        self, 
        client: AsyncClient,
        sample_guardian: Guardian,
        sample_teacher: Teacher
    ):
        """Test assigning a teacher via API."""
        # Create learner first
        learner_data = {
            "first_name": "Teacher",
            "last_name": "Assignment",
            "dob": "2015-06-15",
            "provision_source": "parent",
            "guardian_id": sample_guardian.id
        }
        
        create_response = await client.post("/learners", json=learner_data)
        learner_id = create_response.json()["id"]
        
        # Assign teacher
        assignment_data = {
            "teacher_id": sample_teacher.id,
            "assigned_by": "api_admin"
        }
        
        response = await client.post(
            f"/learners/{learner_id}/teachers", 
            json=assignment_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "assigned" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_assign_multiple_teachers_api(
        self, 
        client: AsyncClient,
        sample_guardian: Guardian,
        sample_teacher: Teacher,
        second_teacher: Teacher
    ):
        """Test assigning multiple teachers via API."""
        # Create learner first
        learner_data = {
            "first_name": "Multi",
            "last_name": "Teacher",
            "dob": "2015-06-15",
            "provision_source": "parent",
            "guardian_id": sample_guardian.id
        }
        
        create_response = await client.post("/learners", json=learner_data)
        learner_id = create_response.json()["id"]
        
        # Assign multiple teachers
        assignment_data = {
            "teacher_ids": [sample_teacher.id, second_teacher.id],
            "assigned_by": "bulk_admin"
        }
        
        response = await client.post(
            f"/learners/{learner_id}/teachers/bulk", 
            json=assignment_data
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["total_requested"] == 2
        assert data["total_successful"] == 2
        assert len(data["successful_assignments"]) == 2
        assert len(data["failed_assignments"]) == 0
    
    @pytest.mark.asyncio
    async def test_remove_teacher_api(
        self, 
        client: AsyncClient,
        sample_guardian: Guardian,
        sample_teacher: Teacher
    ):
        """Test removing a teacher assignment via API."""
        # Create learner and assign teacher
        learner_data = {
            "first_name": "Remove",
            "last_name": "Teacher",
            "dob": "2015-06-15",
            "provision_source": "parent",
            "guardian_id": sample_guardian.id
        }
        
        create_response = await client.post("/learners", json=learner_data)
        learner_id = create_response.json()["id"]
        
        # Assign teacher first
        assignment_data = {
            "teacher_id": sample_teacher.id
        }
        await client.post(f"/learners/{learner_id}/teachers", json=assignment_data)
        
        # Remove teacher
        response = await client.delete(
            f"/learners/{learner_id}/teachers/{sample_teacher.id}"
        )
        
        assert response.status_code == 204
    
    @pytest.mark.asyncio
    async def test_create_learner_invalid_data(self, client: AsyncClient):
        """Test creating a learner with invalid data."""
        learner_data = {
            "first_name": "",  # Invalid: empty string
            "last_name": "Test",
            "dob": "2015-06-15",
            "provision_source": "parent",
            "guardian_id": 999  # Invalid: non-existent guardian
        }
        
        response = await client.post("/learners", json=learner_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_assign_duplicate_teacher_api(
        self, 
        client: AsyncClient,
        sample_guardian: Guardian,
        sample_teacher: Teacher
    ):
        """Test assigning the same teacher twice via API."""
        # Create learner
        learner_data = {
            "first_name": "Duplicate",
            "last_name": "Test",
            "dob": "2015-06-15",
            "provision_source": "parent",
            "guardian_id": sample_guardian.id
        }
        
        create_response = await client.post("/learners", json=learner_data)
        learner_id = create_response.json()["id"]
        
        # Assign teacher first time
        assignment_data = {
            "teacher_id": sample_teacher.id
        }
        
        response1 = await client.post(
            f"/learners/{learner_id}/teachers", 
            json=assignment_data
        )
        assert response1.status_code == 201
        
        # Assign same teacher again (should fail)
        response2 = await client.post(
            f"/learners/{learner_id}/teachers", 
            json=assignment_data
        )
        assert response2.status_code == 409  # Conflict


class TestGuardianAPI:
    """Test guardian API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_guardian_api(self, client: AsyncClient):
        """Test creating a guardian via API."""
        guardian_data = {
            "first_name": "Test",
            "last_name": "Guardian",
            "email": "test.guardian@example.com",
            "phone": "555-0123"
        }
        
        response = await client.post("/guardians", json=guardian_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["first_name"] == "Test"
        assert data["last_name"] == "Guardian"
        assert data["email"] == "test.guardian@example.com"
        assert data["phone"] == "555-0123"
        assert data["id"] is not None
    
    @pytest.mark.asyncio
    async def test_get_guardian_api(self, client: AsyncClient):
        """Test getting a guardian via API."""
        # Create guardian first
        guardian_data = {
            "first_name": "Get",
            "last_name": "Guardian",
            "email": "get.guardian@example.com"
        }
        
        create_response = await client.post("/guardians", json=guardian_data)
        guardian_id = create_response.json()["id"]
        
        # Get guardian
        response = await client.get(f"/guardians/{guardian_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == guardian_id
        assert data["first_name"] == "Get"
        assert data["last_name"] == "Guardian"


class TestTeacherAPI:
    """Test teacher API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_teacher_api(
        self, 
        client: AsyncClient,
        sample_tenant: Tenant
    ):
        """Test creating a teacher via API."""
        teacher_data = {
            "first_name": "Test",
            "last_name": "Teacher",
            "email": "test.teacher@example.com",
            "subject": "Mathematics",
            "tenant_id": sample_tenant.id
        }
        
        response = await client.post("/teachers", json=teacher_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["first_name"] == "Test"
        assert data["last_name"] == "Teacher"
        assert data["email"] == "test.teacher@example.com"
        assert data["subject"] == "Mathematics"
        assert data["tenant_id"] == sample_tenant.id


class TestHealthAPI:
    """Test health check API."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "learner-svc"
        assert data["version"] == "1.0.0"
        assert data["timestamp"] is not None
