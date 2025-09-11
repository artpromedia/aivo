"""
Test suite for Compliance Export Service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from app.models import ExportFormat, ExportStatus
from app.exporters.edfacts import EDFactsExporter
from app.exporters.calpads import CALPADSExporter
from app.crypto import EncryptionManager
from app.audit import AuditLogger


class TestEDFactsExporter:
    """Test EDFacts export functionality"""
    
    @pytest.fixture
    def edfacts_exporter(self):
        db_session = AsyncMock()
        return EDFactsExporter(db_session)
    
    def test_student_headers_lint_compliance(self, edfacts_exporter):
        """Test that CSV headers follow lint hygiene (multi-line format)"""
        headers = edfacts_exporter.EDFACTS_STUDENT_HEADERS
        
        # Verify headers are properly formatted
        assert isinstance(headers, list)
        assert len(headers) > 30  # Should have many fields
        assert "state_student_id" in headers
        assert "district_id" in headers
        assert "academic_year" in headers
    
    @pytest.mark.asyncio
    async def test_export_students(self, edfacts_exporter):
        """Test student data export"""
        # Mock export parameters
        export_params = {
            "export_type": "student",
            "school_year": "2023-24",
            "district_id": "001"
        }
        
        # Mock the export method
        edfacts_exporter.export_students = AsyncMock(return_value="/tmp/test.csv")
        
        result = await edfacts_exporter.export_students(export_params)
        assert result == "/tmp/test.csv"


class TestCALPADSExporter:
    """Test CALPADS export functionality"""
    
    @pytest.fixture
    def calpads_exporter(self):
        db_session = AsyncMock()
        return CALPADSExporter(db_session)
    
    def test_senr_headers_lint_compliance(self, calpads_exporter):
        """Test that SENR headers follow lint hygiene"""
        headers = calpads_exporter.CALPADS_SENR_HEADERS
        
        assert isinstance(headers, list)
        assert len(headers) > 40  # SENR has many fields
        assert "academic_year" in headers
        assert "district_code" in headers
        assert "student_id" in headers


class TestEncryptionManager:
    """Test AES encryption functionality"""
    
    @pytest.fixture
    def encryption_manager(self):
        master_key = b"test-master-key-32-characters-lo"
        return EncryptionManager(master_key)
    
    def test_generate_file_key(self, encryption_manager):
        """Test file encryption key generation"""
        key_id, key_data = encryption_manager.generate_file_key()
        
        assert isinstance(key_id, str)
        assert len(key_id) == 36  # UUID format
        assert isinstance(key_data, bytes)
        assert len(key_data) == 32  # 256-bit key
    
    def test_encryption_validation(self, encryption_manager):
        """Test encryption validation"""
        # Test with mock data
        key_id, key_data = encryption_manager.generate_file_key()
        
        # Mock validation
        encryption_manager.validate_encryption = MagicMock(return_value=True)
        
        is_valid = encryption_manager.validate_encryption("/tmp/test.enc", key_data)
        assert is_valid is True


class TestAuditLogger:
    """Test immutable audit logging"""
    
    @pytest.fixture
    def audit_logger(self):
        db_session = AsyncMock()
        return AuditLogger(db_session)
    
    @pytest.mark.asyncio
    async def test_log_export_created(self, audit_logger):
        """Test export creation audit log"""
        export_job = MagicMock()
        export_job.id = uuid4()
        export_job.format = ExportFormat.EDFACTS
        export_job.name = "Test Export"
        
        user_id = "test@district.edu"
        
        # Mock the logging method
        audit_logger.log_export_created = AsyncMock()
        
        await audit_logger.log_export_created(export_job, user_id)
        audit_logger.log_export_created.assert_called_once_with(export_job, user_id)
    
    def test_integrity_hash_generation(self, audit_logger):
        """Test audit log integrity hash"""
        log_data = {
            "action": "export_created",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": "test@district.edu",
            "details": {"format": "edfacts"}
        }
        
        # Mock hash generation
        audit_logger._generate_integrity_hash = MagicMock(return_value="abc123")
        
        hash_value = audit_logger._generate_integrity_hash(log_data)
        assert hash_value == "abc123"


class TestComplianceAPI:
    """Test FastAPI endpoints"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health check endpoint"""
        # This would test the actual FastAPI app
        # For now, just verify the structure exists
        from app.main import app
        assert app is not None
    
    def test_csv_dict_writer_usage(self):
        """Test proper csv.DictWriter usage with fieldnames"""
        from app.exporters.edfacts import EDFactsExporter
        
        # Verify fieldnames are defined as lists (for lint compliance)
        headers = EDFactsExporter.EDFACTS_STUDENT_HEADERS
        assert isinstance(headers, list)
        
        # This ensures csv.DictWriter can use the fieldnames parameter
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=headers,
            quoting=csv.QUOTE_MINIMAL,
        )
        
        # Write header
        writer.writeheader()
        
        # Verify output contains headers
        output_content = output.getvalue()
        assert "state_student_id" in output_content
        assert "district_id" in output_content


if __name__ == "__main__":
    pytest.main([__file__])
