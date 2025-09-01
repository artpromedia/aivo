"""
Comprehensive tests for tenant service - districts, schools, and seat lifecycle.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_database
from app.models import Base, TenantKind, SeatState


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_tenant.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
async def test_client(test_db):
    """Create test client with database dependency override."""
    async def override_get_database():
        yield test_db
    
    app.dependency_overrides[get_database] = override_get_database
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_id():
    """Test user ID."""
    return "test_user_123"


class TestTenantLifecycle:
    """Test tenant creation and management."""

    async def test_create_district(self, test_client: AsyncClient, test_user_id: str):
        """Test creating a district."""
        district_data = {
            "name": "Springfield District"
        }
        
        response = await test_client.post(
            "/api/v1/district",
            json=district_data,
            headers={"X-User-ID": test_user_id}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Springfield District"
        assert data["kind"] == TenantKind.DISTRICT
        assert data["parent_id"] is None
        assert "id" in data
        assert data["is_active"] is True
        
        return data["id"]

    async def test_create_school(self, test_client: AsyncClient, test_user_id: str):
        """Test creating a school under a district."""
        # First create a district
        district_id = await self.test_create_district(test_client, test_user_id)
        
        school_data = {
            "name": "Springfield Elementary"
        }
        
        response = await test_client.post(
            f"/api/v1/district/{district_id}/schools",
            json=school_data,
            headers={"X-User-ID": test_user_id}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Springfield Elementary"
        assert data["kind"] == TenantKind.SCHOOL
        assert data["parent_id"] == district_id
        
        return data["id"]

    async def test_get_district_with_schools(self, test_client: AsyncClient, test_user_id: str):
        """Test getting district with its schools."""
        # Create district
        district_data = {"name": "Springfield District"}
        response = await test_client.post(
            "/api/v1/district",
            json=district_data,
            headers={"X-User-ID": test_user_id}
        )
        assert response.status_code == 201
        district_id = response.json()["id"]
        
        # Create school
        school_data = {"name": "Springfield Elementary"}
        response = await test_client.post(
            f"/api/v1/district/{district_id}/schools",
            json=school_data,
            headers={"X-User-ID": test_user_id}
        )
        assert response.status_code == 201
        school_id = response.json()["id"]
        
        # Get district with schools
        response = await test_client.get(
            f"/api/v1/district/{district_id}",
            headers={"X-User-ID": test_user_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == district_id
        assert len(data["children"]) >= 1
        assert any(child["id"] == school_id for child in data["children"])

    async def test_create_school_invalid_district(self, test_client: AsyncClient, test_user_id: str):
        """Test creating school with invalid district ID."""
        school_data = {
            "name": "Invalid School"
        }
        
        response = await test_client.post(
            "/api/v1/district/99999/schools",
            json=school_data,
            headers={"X-User-ID": test_user_id}
        )
        
        assert response.status_code == 404


class TestSeatLifecycle:
    """Test seat purchase, allocation, and reclaim lifecycle."""

    async def setup_tenant(self, test_client: AsyncClient, test_user_id: str) -> int:
        """Setup a tenant for seat testing."""
        district_data = {"name": "Test District"}
        response = await test_client.post(
            "/api/v1/district",
            json=district_data,
            headers={"X-User-ID": test_user_id}
        )
        assert response.status_code == 201
        return response.json()["id"]

    async def test_purchase_seats(self, test_client: AsyncClient, test_user_id: str):
        """Test purchasing seats for a tenant."""
        tenant_id = await self.setup_tenant(test_client, test_user_id)
        
        seat_data = {
            "tenant_id": tenant_id,
            "count": 5
        }
        
        response = await test_client.post(
            "/api/v1/seats/purchase",
            json=seat_data,
            headers={"X-User-ID": test_user_id}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 5
        
        for seat in data:
            assert seat["tenant_id"] == tenant_id
            assert seat["state"] == SeatState.FREE
            assert seat["learner_id"] is None
        
        return [seat["id"] for seat in data]

    async def test_allocate_seat(self, test_client: AsyncClient, test_user_id: str):
        """Test allocating a seat to a learner."""
        tenant_id = await self.setup_tenant(test_client, test_user_id)
        seat_ids = await self.test_purchase_seats(test_client, test_user_id)
        
        allocation_data = {
            "seat_id": seat_ids[0],
            "learner_id": "learner_123"
        }
        
        response = await test_client.post(
            "/api/v1/seats/allocate",
            json=allocation_data,
            headers={"X-User-ID": test_user_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == seat_ids[0]
        assert data["state"] == SeatState.ASSIGNED
        assert data["learner_id"] == "learner_123"
        assert data["assigned_at"] is not None
        
        return data

    async def test_reclaim_seat(self, test_client: AsyncClient, test_user_id: str):
        """Test reclaiming a seat from a learner."""
        allocated_seat = await self.test_allocate_seat(test_client, test_user_id)
        
        reclaim_data = {
            "seat_id": allocated_seat["id"],
            "reason": "Student graduated"
        }
        
        response = await test_client.post(
            "/api/v1/seats/reclaim",
            json=reclaim_data,
            headers={"X-User-ID": test_user_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == allocated_seat["id"]
        assert data["state"] == SeatState.FREE
        assert data["learner_id"] is None
        assert data["assigned_at"] is None

    async def test_seat_summary(self, test_client: AsyncClient, test_user_id: str):
        """Test getting seat summary for a tenant."""
        tenant_id = await self.setup_tenant(test_client, test_user_id)
        
        # Purchase seats
        seat_data = {"tenant_id": tenant_id, "count": 5}
        response = await test_client.post(
            "/api/v1/seats/purchase",
            json=seat_data,
            headers={"X-User-ID": test_user_id}
        )
        assert response.status_code == 201
        seats = response.json()
        seat_ids = [seat["id"] for seat in seats]
        
        # Allocate some seats
        allocation_data = {
            "seat_id": seat_ids[0],
            "learner_id": "learner_1"
        }
        await test_client.post(
            "/api/v1/seats/allocate",
            json=allocation_data,
            headers={"X-User-ID": test_user_id}
        )
        
        allocation_data = {
            "seat_id": seat_ids[1],
            "learner_id": "learner_2"
        }
        await test_client.post(
            "/api/v1/seats/allocate",
            json=allocation_data,
            headers={"X-User-ID": test_user_id}
        )
        
        # Get summary
        response = await test_client.get(
            f"/api/v1/seats/summary?tenantId={tenant_id}",
            headers={"X-User-ID": test_user_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == tenant_id
        assert data["total_seats"] == 5
        assert data["assigned_seats"] == 2
        assert data["free_seats"] == 3
        assert data["reserved_seats"] == 0
        assert data["utilization_percentage"] == 40.0

    async def test_idempotent_allocation(self, test_client: AsyncClient, test_user_id: str):
        """Test that learner cannot have multiple seats in same tenant."""
        tenant_id = await self.setup_tenant(test_client, test_user_id)
        seat_ids = await self.test_purchase_seats(test_client, test_user_id)
        
        # Allocate first seat
        allocation_data = {
            "seat_id": seat_ids[0],
            "learner_id": "learner_duplicate"
        }
        
        response = await test_client.post(
            "/api/v1/seats/allocate",
            json=allocation_data,
            headers={"X-User-ID": test_user_id}
        )
        assert response.status_code == 200
        
        # Try to allocate second seat to same learner
        allocation_data = {
            "seat_id": seat_ids[1],
            "learner_id": "learner_duplicate"
        }
        
        response = await test_client.post(
            "/api/v1/seats/allocate",
            json=allocation_data,
            headers={"X-User-ID": test_user_id}
        )
        assert response.status_code == 400
        assert "already has a seat" in response.json()["detail"]

    async def test_allocate_unavailable_seat(self, test_client: AsyncClient, test_user_id: str):
        """Test allocation of already allocated seat fails."""
        allocated_seat = await self.test_allocate_seat(test_client, test_user_id)
        
        # Try to allocate the same seat to another learner
        allocation_data = {
            "seat_id": allocated_seat["id"],
            "learner_id": "another_learner"
        }
        
        response = await test_client.post(
            "/api/v1/seats/allocate",
            json=allocation_data,
            headers={"X-User-ID": test_user_id}
        )
        
        assert response.status_code == 400
        assert "not available" in response.json()["detail"]

    async def test_reclaim_free_seat_fails(self, test_client: AsyncClient, test_user_id: str):
        """Test that reclaiming a free seat fails."""
        tenant_id = await self.setup_tenant(test_client, test_user_id)
        seat_ids = await self.test_purchase_seats(test_client, test_user_id)
        
        reclaim_data = {
            "seat_id": seat_ids[0],  # This seat is free
            "reason": "Test reclaim"
        }
        
        response = await test_client.post(
            "/api/v1/seats/reclaim",
            json=reclaim_data,
            headers={"X-User-ID": test_user_id}
        )
        
        assert response.status_code == 400
        assert "already free" in response.json()["detail"]


class TestErrorHandling:
    """Test error handling and edge cases."""

    async def test_purchase_seats_invalid_tenant(self, test_client: AsyncClient, test_user_id: str):
        """Test purchasing seats for non-existent tenant."""
        seat_data = {
            "tenant_id": 99999,
            "count": 5
        }
        
        response = await test_client.post(
            "/api/v1/seats/purchase",
            json=seat_data,
            headers={"X-User-ID": test_user_id}
        )
        
        assert response.status_code == 404

    async def test_allocate_nonexistent_seat(self, test_client: AsyncClient, test_user_id: str):
        """Test allocating non-existent seat."""
        allocation_data = {
            "seat_id": 99999,
            "learner_id": "learner_123"
        }
        
        response = await test_client.post(
            "/api/v1/seats/allocate",
            json=allocation_data,
            headers={"X-User-ID": test_user_id}
        )
        
        assert response.status_code == 404

    async def test_get_nonexistent_tenant(self, test_client: AsyncClient, test_user_id: str):
        """Test getting non-existent tenant."""
        response = await test_client.get(
            "/api/v1/tenant/99999",
            headers={"X-User-ID": test_user_id}
        )
        
        assert response.status_code == 404

    async def test_seat_summary_nonexistent_tenant(self, test_client: AsyncClient, test_user_id: str):
        """Test seat summary for non-existent tenant."""
        response = await test_client.get(
            "/api/v1/seats/summary?tenantId=99999",
            headers={"X-User-ID": test_user_id}
        )
        
        assert response.status_code == 404


class TestUserRoles:
    """Test user role management within tenants."""

    async def test_assign_user_role(self, test_client: AsyncClient, test_user_id: str):
        """Test assigning role to user within tenant."""
        # Create tenant first
        district_data = {"name": "Test District"}
        response = await test_client.post(
            "/api/v1/district",
            json=district_data,
            headers={"X-User-ID": test_user_id}
        )
        tenant_id = response.json()["id"]
        
        # Assign role
        role_data = {
            "user_id": "teacher_123",
            "tenant_id": tenant_id,
            "role": "teacher"
        }
        
        response = await test_client.post(
            "/api/v1/roles",
            json=role_data,
            headers={"X-User-ID": test_user_id}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == "teacher_123"
        assert data["tenant_id"] == tenant_id
        assert data["role"] == "teacher"
        assert data["is_active"] is True

    async def test_get_user_tenants(self, test_client: AsyncClient, test_user_id: str):
        """Test getting user's tenants."""
        # First assign a role
        await self.test_assign_user_role(test_client, test_user_id)
        
        response = await test_client.get(
            "/api/v1/users/teacher_123/tenants",
            headers={"X-User-ID": test_user_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["user_id"] == "teacher_123"


class TestHealthAndStatus:
    """Test health and status endpoints."""

    async def test_health_check(self, test_client: AsyncClient):
        """Test health check endpoint."""
        response = await test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    async def test_service_health_check(self, test_client: AsyncClient):
        """Test service-specific health check."""
        response = await test_client.get("/api/v1/health")
        assert response.status_code == 200
        assert "healthy" in response.json()["message"]

    async def test_root_endpoint(self, test_client: AsyncClient):
        """Test root endpoint."""
        response = await test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "tenant-svc"
        assert data["status"] == "running"


# Integration test scenarios
class TestIntegrationScenarios:
    """Test complete workflow scenarios."""

    async def test_complete_district_school_seat_workflow(
        self, test_client: AsyncClient, test_user_id: str
    ):
        """Test complete workflow: create district, add schools, purchase seats, allocate/reclaim."""
        
        # 1. Create district
        district_data = {"name": "Metro District"}
        response = await test_client.post(
            "/api/v1/district",
            json=district_data,
            headers={"X-User-ID": test_user_id}
        )
        assert response.status_code == 201
        district_id = response.json()["id"]
        
        # 2. Create schools
        school1_data = {"name": "North Elementary"}
        response = await test_client.post(
            f"/api/v1/district/{district_id}/schools",
            json=school1_data,
            headers={"X-User-ID": test_user_id}
        )
        assert response.status_code == 201
        school1_id = response.json()["id"]
        
        school2_data = {"name": "South Elementary"}
        response = await test_client.post(
            f"/api/v1/district/{district_id}/schools",
            json=school2_data,
            headers={"X-User-ID": test_user_id}
        )
        assert response.status_code == 201
        school2_id = response.json()["id"]
        
        # 3. Purchase seats for each school
        for school_id in [school1_id, school2_id]:
            seat_data = {"tenant_id": school_id, "count": 10}
            response = await test_client.post(
                "/api/v1/seats/purchase",
                json=seat_data,
                headers={"X-User-ID": test_user_id}
            )
            assert response.status_code == 201
            assert len(response.json()) == 10
        
        # 4. Check seat summaries
        for school_id in [school1_id, school2_id]:
            response = await test_client.get(
                f"/api/v1/seats/summary?tenantId={school_id}",
                headers={"X-User-ID": test_user_id}
            )
            assert response.status_code == 200
            summary = response.json()
            assert summary["total_seats"] == 10
            assert summary["free_seats"] == 10
            assert summary["utilization_percentage"] == 0.0
        
        # 5. Verify district structure
        response = await test_client.get(
            f"/api/v1/district/{district_id}",
            headers={"X-User-ID": test_user_id}
        )
        assert response.status_code == 200
        district = response.json()
        assert len(district["children"]) == 2
        school_ids = [child["id"] for child in district["children"]]
        assert school1_id in school_ids
        assert school2_id in school_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
