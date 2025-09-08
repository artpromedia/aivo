"""Tests for ink service business logic."""
import pytest
from uuid import uuid4

from app.schemas import Point, Stroke, StrokeRequest
from app.services import ConsentGateService, S3StorageService


@pytest.mark.asyncio
async def test_consent_validation():
    """Test consent validation logic."""
    service = ConsentGateService()
    
    learner_id = uuid4()
    subject = "mathematics"
    metadata = {"device": "tablet"}
    
    is_valid, error = await service.validate_consent(
        learner_id, subject, metadata
    )
    
    assert is_valid is True
    assert error is None


@pytest.mark.asyncio
async def test_media_policy_validation():
    """Test media policy validation."""
    service = ConsentGateService()
    
    # Create valid stroke request
    stroke_request = StrokeRequest(
        session_id=uuid4(),
        learner_id=uuid4(),
        subject="mathematics",
        canvas_width=800,
        canvas_height=600,
        strokes=[
            Stroke(
                stroke_id=uuid4(),
                points=[
                    Point(x=100, y=150, timestamp=0),
                    Point(x=105, y=152, timestamp=16),
                ]
            )
        ]
    )
    
    is_valid, error = await service.validate_media_policy(stroke_request)
    
    assert is_valid is True
    assert error is None


@pytest.mark.asyncio
async def test_media_policy_too_many_strokes():
    """Test media policy with too many strokes."""
    service = ConsentGateService()
    
    # Create stroke request with too many strokes
    strokes = [
        Stroke(
            stroke_id=uuid4(),
            points=[Point(x=100, y=150, timestamp=0)]
        )
        for _ in range(1001)  # Exceeds limit
    ]
    
    stroke_request = StrokeRequest(
        session_id=uuid4(),
        learner_id=uuid4(),
        subject="mathematics",
        canvas_width=800,
        canvas_height=600,
        strokes=strokes
    )
    
    is_valid, error = await service.validate_media_policy(stroke_request)
    
    assert is_valid is False
    assert "Too many strokes" in error


def test_s3_key_generation():
    """Test S3 key generation."""
    service = S3StorageService()
    
    session_id = uuid4()
    page_id = uuid4()
    learner_id = uuid4()
    
    s3_key = service.generate_s3_key(session_id, page_id, learner_id)
    
    assert s3_key.startswith("ink-pages/")
    assert str(session_id) in s3_key
    assert str(page_id) in s3_key
    assert str(learner_id) in s3_key
    assert s3_key.endswith(".ndjson")
