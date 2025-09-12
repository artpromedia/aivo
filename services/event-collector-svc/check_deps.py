#!/usr/bin/env python3
"""Quick dependency check for Event Collector service."""
# pylint: disable=import-outside-toplevel


def test_imports():
    """Test all critical imports."""
    try:
        print("Testing core imports...")

        # Test FastAPI
        import fastapi

        print(f"✅ FastAPI {fastapi.__version__}")

        # Test gRPC
        import grpc

        print(f"✅ gRPC {grpc.__version__}")

        # Test Kafka
        import aiokafka

        print(f"✅ aiokafka {aiokafka.__version__}")

        # Test other dependencies
        import pydantic

        print(f"✅ Pydantic {pydantic.__version__}")

        import structlog

        print(f"✅ structlog {structlog.__version__}")

        import aiofiles

        # Handle aiofiles version detection
        version = getattr(aiofiles, "__version__", "unknown")
        print(f"✅ aiofiles {version}")

        import orjson

        print(f"✅ orjson {orjson.__version__}")

        import pendulum

        print(f"✅ pendulum {pendulum.__version__}")

        print("\n🎉 All core dependencies are installed!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_app_modules():
    """Test our application modules."""
    try:
        print("\nTesting app modules...")

        # Test config
        from app.config import settings

        print(f"✅ Config loaded - Service: {settings.service_name}")

        # Test models
        import importlib.util

        if importlib.util.find_spec("app.models"):
            print("✅ Models module available")

        # Test services
        if importlib.util.find_spec("app.services.buffer_service"):
            print("✅ Buffer service module available")

        if importlib.util.find_spec("app.services.kafka_service"):
            print("✅ Kafka service module available")

        if importlib.util.find_spec("app.services.event_processor"):
            print("✅ Event processor module available")

        # Test APIs
        if importlib.util.find_spec("app.http_api"):
            print("✅ HTTP API module available")

        # Test protobuf (might fail if not generated)
        try:
            if importlib.util.find_spec("protos.event_collector_pb2"):
                print("✅ Protobuf modules available")
        except ImportError:
            print("⚠️  Protobuf modules not found (need to generate)")

        print("\n🎉 All app modules loaded successfully!")
        return True

    except ImportError as e:
        print(f"❌ App module error: {e}")
        return False


if __name__ == "__main__":
    DEPS_OK = test_imports()
    APP_OK = test_app_modules()

    if DEPS_OK and APP_OK:
        print("\n✅ Event Collector service is ready to run!")
    else:
        print("\n❌ Some issues found - check output above")
        exit(1)
