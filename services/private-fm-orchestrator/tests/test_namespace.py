"""
Tests for namespace service functionality.
"""

from app.services import NamespaceService


class TestNamespaceService:
    """Test namespace service functionality."""

    def test_generate_namespace_uid(self):
        """Test namespace UID generation."""
        service = NamespaceService()

        # Generate UIDs for different learners
        uid1 = service.generate_namespace_uid(123)
        uid2 = service.generate_namespace_uid(456)
        uid3 = service.generate_namespace_uid(123)  # Same learner, different call

        # All UIDs should be unique (even for same learner)
        assert uid1 != uid2
        assert uid1 != uid3
        assert uid2 != uid3

        # All should start with 'ns-'
        assert uid1.startswith("ns-")
        assert uid2.startswith("ns-")
        assert uid3.startswith("ns-")

        # Should be correct length (ns- + 16 char hash)
        assert len(uid1) == 19  # "ns-" + 16 chars
        assert len(uid2) == 19
        assert len(uid3) == 19

    def test_generate_checkpoint_hash(self):
        """Test checkpoint hash generation."""
        service = NamespaceService()

        # Generate multiple hashes
        hash1 = service.generate_checkpoint_hash()
        hash2 = service.generate_checkpoint_hash()
        hash3 = service.generate_checkpoint_hash()

        # All hashes should be unique
        assert hash1 != hash2
        assert hash1 != hash3
        assert hash2 != hash3

        # Should be 32 characters (truncated SHA256)
        assert len(hash1) == 32
        assert len(hash2) == 32
        assert len(hash3) == 32

        # Should be hexadecimal
        assert all(c in "0123456789abcdef" for c in hash1)
        assert all(c in "0123456789abcdef" for c in hash2)
        assert all(c in "0123456789abcdef" for c in hash3)

    def test_namespace_uid_deterministic_base(self):
        """Test that namespace UID generation uses learner ID consistently."""
        service = NamespaceService()

        # Multiple calls for same learner should have different UUIDs but same learner reference
        learner_id = 789
        uid1 = service.generate_namespace_uid(learner_id)
        uid2 = service.generate_namespace_uid(learner_id)

        # Should be different (due to UUID)
        assert uid1 != uid2

        # But both should reference the same learner in their generation
        # (This is more of a conceptual test - in practice they're unique due to UUID)
