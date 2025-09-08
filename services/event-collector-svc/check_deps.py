#!/usr/bin/env python3
"""Quick dependency check for Event Collector service."""


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

        print(f"✅ aiofiles {aiofiles.__version__}")

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
        from app.models import LearnerEvent

        print("✅ Models loaded")

        # Test services
        from app.services.buffer_service import EventBuffer

        print("✅ Buffer service loaded")

        from app.services.kafka_service import KafkaProducerService

        print("✅ Kafka service loaded")

        from app.services.event_processor import EventProcessor

        print("✅ Event processor loaded")

        # Test APIs
        from app.http_api import app

        print("✅ HTTP API loaded")

        # Test protobuf (might fail if not generated)
        try:
            from protos import event_collector_pb2

            print("✅ Protobuf modules loaded")
        except ImportError:
            print("⚠️  Protobuf modules not found (need to generate)")

        print("\n🎉 All app modules loaded successfully!")
        return True

    except ImportError as e:
        print(f"❌ App module error: {e}")
        return False


if __name__ == "__main__":
    deps_ok = test_imports()
    app_ok = test_app_modules()

    if deps_ok and app_ok:
        print("\n✅ Event Collector service is ready to run!")
    else:
        print("\n❌ Some issues found - check output above")
        exit(1)
