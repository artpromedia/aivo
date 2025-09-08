"""Tests for Science Solver Service main application."""

import base64

from fastapi.testclient import TestClient
from starlette import status

from app.main import app

client = TestClient(app)

# HTTP status code constants
HTTP_200_OK = status.HTTP_200_OK
HTTP_400_BAD_REQUEST = status.HTTP_400_BAD_REQUEST


def test_health_check() -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "science-solver-svc"
    assert "timestamp" in data


def test_units_validate() -> None:
    """Test unit validation endpoint."""
    request_data = {
        "expression": "10 m/s + 5 ft/s",
        "target_system": "SI",
    }
    response = client.post("/units/validate", json=request_data)
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert "is_valid" in data
    assert "unit_analysis" in data


def test_chem_balance() -> None:
    """Test chemical equation balancing endpoint."""
    request_data = {
        "equation": "H2 + O2 -> H2O",
        "balance_type": "standard",
    }
    response = client.post("/chem/balance", json=request_data)
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert "is_balanced" in data
    if data["is_balanced"]:
        assert data["balanced_equation"] == "2H2 + O2 -> 2H2O"


def test_diagram_parse() -> None:
    """Test diagram parsing endpoint."""
    # Create a simple base64 encoded image (1x1 pixel PNG)
    # Minimal PNG data for a 1x1 transparent pixel
    png_data = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
        b"\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    base64_image = base64.b64encode(png_data).decode("utf-8")

    request_data = {
        "image_data": base64_image,
        "parse_type": "general",
        "confidence_threshold": 0.7,
    }
    response = client.post("/diagram/parse", json=request_data)
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert "detected_objects" in data
    assert "extracted_text" in data
    assert "processing_info" in data


def test_invalid_equation_format() -> None:
    """Test invalid chemical equation format."""
    request_data = {
        "equation": "invalid equation format",
        "balance_type": "standard",
    }
    response = client.post("/chem/balance", json=request_data)
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["is_balanced"] is False
    assert len(data["errors"]) > 0


def test_equation_too_long() -> None:
    """Test chemical equation that is too long."""
    long_equation = "A" * 2000 + " -> " + "B" * 2000
    request_data = {
        "equation": long_equation,
        "balance_type": "standard",
    }
    response = client.post("/chem/balance", json=request_data)
    assert response.status_code == HTTP_400_BAD_REQUEST


def test_image_too_large() -> None:
    """Test image that is too large."""
    # Create a large base64 string to simulate oversized image
    large_data = "x" * (15 * 1024 * 1024)  # 15MB of data
    request_data = {
        "image_data": large_data,
        "parse_type": "general",
        "confidence_threshold": 0.7,
    }
    response = client.post("/diagram/parse", json=request_data)
    assert response.status_code == HTTP_400_BAD_REQUEST
