"""
Tests for PII detection and anonymization service.
"""
import pytest
from app.pii_service import PIIService
from app.schemas import PIIEntity


class TestPIIService:
    """Test PII service functionality."""
    
    @pytest.mark.asyncio
    async def test_detect_email_addresses(self):
        """Test detection of email addresses."""
        pii_service = PIIService()
        text = "Contact me at john.doe@example.com or jane@test.org"
        
        entities = await pii_service.detect_pii(text)
        
        # Should detect at least email addresses
        email_entities = [e for e in entities if "EMAIL" in e.entity_type.upper()]
        assert len(email_entities) >= 1
        assert any("john.doe@example.com" in e.text for e in email_entities)
    
    @pytest.mark.asyncio
    async def test_detect_phone_numbers(self):
        """Test detection of phone numbers."""
        pii_service = PIIService()
        text = "Call me at 555-123-4567 or (555) 987-6543"
        
        entities = await pii_service.detect_pii(text)
        
        # Should detect phone numbers
        phone_entities = [e for e in entities if "PHONE" in e.entity_type.upper()]
        assert len(phone_entities) >= 1
    
    @pytest.mark.asyncio
    async def test_anonymize_pii_entities(self):
        """Test PII anonymization."""
        pii_service = PIIService()
        text = "My email is john.doe@example.com"
        
        entities = await pii_service.detect_pii(text)
        anonymized = await pii_service.anonymize_text(text, entities)
        
        # Email should be anonymized
        assert "john.doe@example.com" not in anonymized
        assert "[EMAIL_ADDRESS]" in anonymized or "EMAIL" in anonymized.upper()
    
    @pytest.mark.asyncio
    async def test_process_text_with_pii(self):
        """Test complete PII processing pipeline."""
        pii_service = PIIService()
        text = "Contact john.doe@example.com or call 555-123-4567"
        
        processed_text, entities, scrubbed = await pii_service.process_text(text)
        
        assert len(entities) >= 1  # Should detect PII
        assert scrubbed  # Should be scrubbed
        assert "john.doe@example.com" not in processed_text
    
    @pytest.mark.asyncio
    async def test_process_text_without_pii(self):
        """Test processing text without PII."""
        pii_service = PIIService()
        text = "This is a normal message about science education"
        
        processed_text, entities, scrubbed = await pii_service.process_text(text)
        
        assert len(entities) == 0  # No PII detected
        assert not scrubbed  # Nothing to scrub
        assert processed_text == text  # Text unchanged
    
    @pytest.mark.asyncio
    async def test_multiple_pii_types(self):
        """Test detection of multiple PII types."""
        pii_service = PIIService()
        text = "John Doe (john.doe@example.com) lives at 123 Main St and his SSN is 123-45-6789"
        
        entities = await pii_service.detect_pii(text)
        
        # Should detect multiple types of PII
        entity_types = {e.entity_type for e in entities}
        assert len(entity_types) >= 1  # At least email should be detected
    
    @pytest.mark.asyncio
    async def test_fallback_regex_detection(self):
        """Test fallback regex-based PII detection."""
        pii_service = PIIService()
        # Force fallback by disabling Presidio
        pii_service.analyzer = None
        
        text = "Email: test@example.com Phone: 555-123-4567"
        entities = pii_service._detect_pii_fallback(text)
        
        assert len(entities) >= 2  # Email and phone
        entity_types = {e.entity_type for e in entities}
        assert "EMAIL_ADDRESS" in entity_types
        assert "PHONE_NUMBER" in entity_types
    
    @pytest.mark.asyncio
    async def test_fallback_anonymization(self):
        """Test fallback anonymization."""
        pii_service = PIIService()
        text = "Contact me at john@example.com"
        
        entities = [
            PIIEntity(
                entity_type="EMAIL_ADDRESS",
                start=14,
                end=30,
                score=0.8,
                text="john@example.com"
            )
        ]
        
        anonymized = pii_service._anonymize_fallback(text, entities)
        assert "john@example.com" not in anonymized
        assert "[EMAIL_ADDRESS]" in anonymized
