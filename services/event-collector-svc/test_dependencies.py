#!/usr/bin/env python3
"""Test script to verify all dependencies are installed correctly."""

import sys

def test_imports():
    """Test all critical imports."""
    try:
        print("Testing basic Python modules...")
        import asyncio
        import json
        from datetime import datetime
        print("✓ Basic Python modules imported")

        print("Testing web framework dependencies...")
        import fastapi
        import uvicorn
        print("✓ FastAPI and Uvicorn imported")

        print("Testing async and data dependencies...")
        import aiofiles
        import orjson
        import pendulum
        import structlog
        print("✓ Async and data modules imported")

        print("Testing Kafka dependencies...")
        import aiokafka
        print("✓ Kafka modules imported")

        print("Testing gRPC dependencies...")
        import grpc
        import grpcio_tools
        from google.protobuf import empty_pb2
        print("✓ gRPC modules imported")

        print("Testing Pydantic dependencies...")
        import pydantic
        from pydantic_settings import BaseSettings
        print("✓ Pydantic modules imported")

        print("Testing application modules...")
        from app.models import LearnerEvent
        from app.config import settings
        print(f"✓ Application modules imported - Service: {settings.service_name}")

        print("Testing protobuf modules...")
        from protos import event_collector_pb2, event_collector_pb2_grpc
        print("✓ Protobuf modules imported")

        print("\n🎉 All dependencies are installed and working correctly!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
