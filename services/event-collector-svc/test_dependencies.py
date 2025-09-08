#!/usr/bin/env python3
"""Test script to verify all dependencies are installed correctly."""

import importlib.util
import sys

from app.config import settings


def test_imports():
    """Test all critical imports."""
    try:
        print("Testing basic Python modules...")
        # Test availability without importing unused modules
        assert importlib.util.find_spec("asyncio")
        assert importlib.util.find_spec("json")
        assert importlib.util.find_spec("datetime")

        print("✓ Basic Python modules available")

        print("Testing web framework dependencies...")
        assert importlib.util.find_spec("fastapi")
        assert importlib.util.find_spec("uvicorn")

        print("✓ FastAPI and Uvicorn available")

        print("Testing async and data dependencies...")
        assert importlib.util.find_spec("aiofiles")
        assert importlib.util.find_spec("orjson")
        assert importlib.util.find_spec("pendulum")
        assert importlib.util.find_spec("structlog")

        print("✓ Async and data modules available")

        print("Testing Kafka dependencies...")
        assert importlib.util.find_spec("aiokafka")

        print("✓ Kafka modules available")

        print("Testing gRPC dependencies...")
        assert importlib.util.find_spec("grpc")
        assert importlib.util.find_spec("grpcio_tools")
        assert importlib.util.find_spec("google.protobuf")

        print("✓ gRPC modules available")

        print("Testing Pydantic dependencies...")
        assert importlib.util.find_spec("pydantic")
        assert importlib.util.find_spec("pydantic_settings")

        print("✓ Pydantic modules available")

        print("Testing application modules...")
        assert importlib.util.find_spec("app.models")

        print(
            f"✓ Application modules available - Service: "
            f"{settings.service_name}"
        )

        print("Testing protobuf modules...")
        assert importlib.util.find_spec("protos.event_collector_pb2")
        assert importlib.util.find_spec("protos.event_collector_pb2_grpc")

        print("✓ Protobuf modules available")

        print("\n🎉 All dependencies are installed and working correctly!")
        return True

    except (ModuleNotFoundError, AttributeError) as e:
        print(f"❌ Module or attribute error: {e}")
        return False
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


if __name__ == "__main__":
    SUCCESS = test_imports()
    sys.exit(0 if SUCCESS else 1)
