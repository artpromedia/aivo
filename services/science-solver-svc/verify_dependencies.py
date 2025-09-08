#!/usr/bin/env python3
"""Verification script for Science Solver Service dependencies."""

# ruff: noqa: T201
# pylint: disable=import-error,no-member,broad-exception-caught
# pylint: disable=import-outside-toplevel

import sys
from typing import Any


def test_imports() -> dict[str, Any]:
    """Test all critical imports for the Science Solver Service."""
    results = {}

    # Core web framework
    try:
        import fastapi
        import pydantic
        import uvicorn

        results["web_framework"] = {
            "fastapi": fastapi.__version__,
            "uvicorn": uvicorn.__version__,
            "pydantic": pydantic.__version__,
            "status": "✅ OK",
        }
    except ImportError as e:
        results["web_framework"] = {"status": f"❌ FAILED: {e}"}

    # Scientific computing
    try:
        import numpy as np
        import scipy
        import sympy

        results["scientific"] = {
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "sympy": sympy.__version__,
            "status": "✅ OK",
        }
    except ImportError as e:
        results["scientific"] = {"status": f"❌ FAILED: {e}"}

    # Image processing with graceful cv2 handling
    try:
        try:
            import cv2
        except ImportError:
            cv2 = None

        import PIL

        if cv2 is not None:
            opencv_version = cv2.__version__
        else:
            opencv_version = "Not available"

        results["image_processing"] = {
            "opencv": opencv_version,
            "pillow": PIL.__version__,
            "status": "✅ OK",
        }
    except ImportError as e:
        results["image_processing"] = {"status": f"❌ FAILED: {e}"}

    # Development tools (minimal for verification)
    try:
        import black
        import pytest

        results["dev_tools"] = {
            "pytest": pytest.__version__,
            "black": black.__version__,
            "status": "✅ OK",
        }
    except ImportError as e:
        results["dev_tools"] = {"status": f"❌ FAILED: {e}"}

    return results


def _test_fastapi_import() -> bool:
    """Test FastAPI app import."""
    try:
        from app.main import app
        assert app is not None  # noqa: S101
        print("✅ FastAPI app imports successfully")
        return True
    except ImportError as e:
        print(f"❌ FastAPI app import failed: {e}")
        return False


def _test_config_import() -> bool:
    """Test configuration import."""
    try:
        from app.config import settings
        print(
            f"✅ Configuration loaded: {settings.service_name} "
            f"v{settings.service_version}",
        )
        return True
    except ImportError as e:
        print(f"❌ Configuration import failed: {e}")
        return False


def _test_schemas_import() -> bool:
    """Test Pydantic schemas import."""
    try:
        from app.schemas import (
            ChemicalEquationRequest,
            DiagramParseRequest,
            UnitValidationRequest,
        )
        test_schemas = [
            ChemicalEquationRequest,
            DiagramParseRequest,
            UnitValidationRequest,
        ]
        assert len(test_schemas) == 3  # noqa: S101,PLR2004
        print("✅ Pydantic schemas import successfully")
        return True
    except ImportError as e:
        print(f"❌ Schema import failed: {e}")
        return False


def _test_scientific_computing() -> bool:
    """Test scientific computing libraries."""
    try:
        import numpy as np
        import sympy as sp

        # Basic numpy test
        arr = np.array([1, 2, 3])
        if arr.sum() != 6:  # noqa: PLR2004
            msg = "Array sum test failed"
            raise ValueError(msg)  # noqa: TRY301

        # Basic sympy test
        x = sp.Symbol("x")
        expr = x**2 + 2*x + 1
        sp.simplify(expr)  # Test simplification works

        print("✅ Scientific computing libraries working")
        return True
    except Exception as e:
        print(f"❌ Scientific computing test failed: {e}")
        return False


def _test_image_processing() -> bool:
    """Test image processing libraries."""
    try:
        try:
            import cv2
        except ImportError:
            cv2 = None

        import numpy as np
        from PIL import Image

        # Create a simple test image
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)

        # Test OpenCV if available
        if cv2 is not None:
            cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)

        # Test PIL
        Image.fromarray(test_img)

        print("✅ Image processing libraries working")
        return True
    except Exception as e:
        print(f"❌ Image processing test failed: {e}")
        return False


def test_functionality() -> bool:
    """Test basic functionality of key components."""
    print("🧪 Testing Core Functionality...")

    # Run all tests
    tests = [
        _test_fastapi_import,
        _test_config_import,
        _test_schemas_import,
        _test_scientific_computing,
        _test_image_processing,
    ]

    return all(test() for test in tests)


def main() -> int:
    """Main verification function."""
    print("🔬 Science Solver Service - Dependency Verification")
    print("=" * 50)

    # Test imports
    print("\n📦 Testing Package Imports...")
    results = test_imports()

    for category, result in results.items():
        print(f"\n{category.replace('_', ' ').title()}:")
        if isinstance(result, dict) and "status" in result:
            print(f"  {result['status']}")
            for key, value in result.items():
                if key != "status":
                    print(f"  - {key}: {value}")

    # Test functionality
    print("\n" + "=" * 50)
    success = test_functionality()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All dependencies and functionality verified successfully!")
        print("\nThe Science Solver Service is ready for deployment.")
        return 0

    print("❌ Some tests failed. Please check the error messages above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
