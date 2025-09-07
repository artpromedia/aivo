"""
Provider verification script for Python services.
This script starts the service and runs Pact verification against it.
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

import httpx


async def wait_for_service(url: str, timeout: int = 30) -> bool:
    """Wait for service to be ready."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/health")
                if response.status_code == 200:
                    return True
        except Exception:
            pass

        await asyncio.sleep(1)

    return False


async def run_provider_verification(service_name: str) -> bool:
    """Run Pact provider verification for a Python service."""
    service_dir = Path(f"services/{service_name}")

    if not service_dir.exists():
        print(f"Service directory {service_dir} does not exist")
        return False

    # Start the service
    print(f"Starting {service_name}...")
    process = subprocess.Popen(
        [sys.executable, "-m", "app.main"],
        cwd=service_dir,
        env={
            "DATABASE_URL": "sqlite:///test.db",
            "JWT_SECRET": "test-secret-key",
            "ENVIRONMENT": "test",
            "PORT": "8080",
        },
    )

    try:
        # Wait for service to be ready
        service_ready = await wait_for_service("http://localhost:8080")

        if not service_ready:
            print(f"Service {service_name} failed to start")
            return False

        print(f"Service {service_name} is ready")

        # Run Pact verification
        pact_result = subprocess.run(
            ["pnpm", "test:providers"],
            cwd="pact",
            env={"PROVIDER_NAME": service_name, "PROVIDER_URL": "http://localhost:8080"},
        )

        return pact_result.returncode == 0

    finally:
        # Clean up
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify_provider.py <service_name>")
        sys.exit(1)

    service_name = sys.argv[1]
    success = asyncio.run(run_provider_verification(service_name))

    if success:
        print(f"Provider verification for {service_name} passed")
        sys.exit(0)
    else:
        print(f"Provider verification for {service_name} failed")
        sys.exit(1)
