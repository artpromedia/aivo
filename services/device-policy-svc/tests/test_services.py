"""Unit tests for policy management."""
# flake8: noqa: E501


from app.models import PolicyStatus, PolicyType
from app.schemas import (
    KioskPolicyConfig,
    PolicyCreate,
    PolicyUpdate,
)


class TestPolicyService:
    """Test policy service operations."""

    async def test_create_policy(self, db_session, policy_service):
        """Test policy creation."""
        config = KioskPolicyConfig(
            mode="single_app",
            apps=[
                {
                    "package_name": "com.aivo.study",
                    "app_name": "Aivo Study",
                    "auto_launch": True,
                    "allow_exit": False,
                    "fullscreen": True,
                }
            ],
        )

        request = PolicyCreate(
            name="Test Kiosk Policy",
            description="Test policy for kiosk mode",
            policy_type=PolicyType.KIOSK,
            config=config.dict(),
            priority=100,
        )

        policy = await policy_service.create_policy(db_session, request)

        assert policy.name == "Test Kiosk Policy"
        assert policy.policy_type == PolicyType.KIOSK
        assert policy.status == PolicyStatus.DRAFT
        assert policy.version == 1

    async def test_get_policy(self, db_session, policy_service, sample_policy):
        """Test policy retrieval."""
        db_session.add(sample_policy)
        await db_session.commit()

        policy = await policy_service.get_policy(db_session, sample_policy.policy_id)

        assert policy is not None
        assert policy.policy_id == sample_policy.policy_id
        assert policy.name == sample_policy.name

    async def test_update_policy(self, db_session, policy_service, sample_policy):
        """Test policy update."""
        db_session.add(sample_policy)
        await db_session.commit()

        update_request = PolicyUpdate(
            name="Updated Policy",
            description="Updated description",
        )

        updated_policy = await policy_service.update_policy(
            db_session, sample_policy.policy_id, update_request
        )

        assert updated_policy.name == "Updated Policy"
        assert updated_policy.description == "Updated description"
        assert updated_policy.version == 2

    async def test_delete_policy(self, db_session, policy_service, sample_policy):
        """Test policy deletion."""
        db_session.add(sample_policy)
        await db_session.commit()

        success = await policy_service.delete_policy(db_session, sample_policy.policy_id)

        assert success is True

        deleted_policy = await policy_service.get_policy(db_session, sample_policy.policy_id)
        assert deleted_policy is None

    async def test_list_policies(self, db_session, policy_service, sample_policy):
        """Test policy listing."""
        db_session.add(sample_policy)
        await db_session.commit()

        policies = await policy_service.list_policies(db_session)

        assert len(policies) == 1
        assert policies[0].policy_id == sample_policy.policy_id


class TestAllowlistService:
    """Test allowlist service operations."""

    async def test_add_allowlist_entry(self, db_session, allowlist_service):
        """Test adding allowlist entry."""
        entry = await allowlist_service.add_entry(
            db_session,
            entry_type="domain",
            value="education.com",
            category="educational",
            description="Educational content site",
        )

        assert entry.entry_type == "domain"
        assert entry.value == "education.com"
        assert entry.category == "educational"
        assert entry.is_active is True

    async def test_get_active_allowlist(self, db_session, allowlist_service):
        """Test retrieving active allowlist entries."""
        # Add test entries
        await allowlist_service.add_entry(
            db_session,
            entry_type="domain",
            value="education.com",
            category="educational",
        )

        await allowlist_service.add_entry(
            db_session,
            entry_type="url",
            value="https://khan-academy.org/learn",
            category="educational",
        )

        entries = await allowlist_service.get_active_entries(db_session)

        assert len(entries) == 2
        assert all(entry.is_active for entry in entries)

    async def test_remove_allowlist_entry(self, db_session, allowlist_service):
        """Test removing allowlist entry."""
        entry = await allowlist_service.add_entry(
            db_session,
            entry_type="domain",
            value="test.com",
            category="test",
        )

        removed = await allowlist_service.remove_entry(db_session, entry.entry_id)

        assert removed is True

        # Verify entry is deactivated
        entries = await allowlist_service.get_active_entries(db_session)
        active_values = [e.value for e in entries]
        assert "test.com" not in active_values
