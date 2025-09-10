#!/usr/bin/env python3
# pylint: disable=invalid-name
"""
gRPC Mesh Deployment and Management Script.

This script handles deployment, configuration, and management of the gRPC mesh
infrastructure including certificate management, service registration, and
health monitoring.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import subprocess
import sys
import time
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MeshDeployment:
    """Manages gRPC mesh deployment and operations."""

    def __init__(self: MeshDeployment, config_dir: str = "./") -> None:
        """Initialize mesh deployment manager."""
        self.config_dir = Path(config_dir)
        self.cert_dir = self.config_dir / "certs"
        self.compose_file = self.config_dir / "docker-compose.yml"

    async def deploy(
        self: MeshDeployment, components: list[str] | None = None
    ) -> bool:
        """Deploy mesh infrastructure components."""
        logger.info("🚀 Starting gRPC mesh deployment...")

        # Step 1: Generate certificates
        if not await self.generate_certificates():
            logger.error("❌ Certificate generation failed")
            return False

        # Step 2: Start infrastructure components
        if not await self.start_infrastructure(components):
            logger.error("❌ Infrastructure startup failed")
            return False

        # Step 3: Wait for services to be ready
        if not await self.wait_for_readiness():
            logger.error("❌ Service health checks failed")
            return False

        # Step 4: Register services
        if not await self.register_services():
            logger.error("❌ Service registration failed")
            return False

        logger.info("✅ gRPC mesh deployment completed successfully")
        return True

    async def generate_certificates(self: MeshDeployment) -> bool:
        """Generate TLS certificates for the mesh."""
        logger.info("🔐 Generating mTLS certificates...")

        # Check if certificates already exist
        ca_cert = self.cert_dir / "ca" / "ca.crt"
        if ca_cert.exists():
            logger.info("Certificates already exist, skipping generation")
            return True

        # Run certificate generation script
        script_path = self.config_dir / "scripts" / "generate-certs.ps1"
        if not script_path.exists():
            script_path = self.config_dir / "scripts" / "generate-certs.sh"

        if not script_path.exists():
            logger.error("Certificate generation script not found")
            return False

        try:
            if script_path.suffix == ".ps1":
                cmd = [
                    "powershell", "-ExecutionPolicy", "Bypass", "-File",
                    str(script_path)
                ]
            else:
                cmd = ["bash", str(script_path)]

            result = subprocess.run(
                cmd,
                cwd=self.config_dir,
                capture_output=True,
                text=True,
                timeout=120,
                check=False
            )

            if result.returncode != 0:
                logger.error(
                    "Certificate generation failed: %s", result.stderr
                )
                return False

            logger.info("✅ Certificates generated successfully")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Certificate generation timed out")
            return False
        except (subprocess.SubprocessError, OSError, FileNotFoundError) as e:
            logger.error("Certificate generation error: %s", e)
            return False

    async def start_infrastructure(
        self: MeshDeployment, components: list[str] | None = None
    ) -> bool:
        """Start infrastructure components using Docker Compose."""
        logger.info("🐳 Starting infrastructure components...")

        if not self.compose_file.exists():
            logger.error(
                "Docker Compose file not found: %s", self.compose_file
            )
            return False

        # Default components in dependency order
        default_components = [
            "consul",
            "jaeger",
            "prometheus",
            "grafana",
            "postgres",
            "kafka",
            "zookeeper"
        ]

        components_to_start = components or default_components

        try:
            # Start components in order
            for component in components_to_start:
                logger.info("Starting %s...", component)
                result = subprocess.run([
                    "docker-compose", "-f", str(self.compose_file),
                    "up", "-d", component
                ], capture_output=True, text=True, timeout=60, check=False)

                if result.returncode != 0:
                    logger.error(
                        "Failed to start %s: %s", component, result.stderr
                    )
                    return False

                # Wait a bit between components
                await asyncio.sleep(2)

            logger.info("✅ Infrastructure components started")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Infrastructure startup timed out")
            return False
        except (subprocess.SubprocessError, OSError) as e:
            logger.error("Infrastructure startup error: %s", e)
            return False

    async def wait_for_readiness(
        self: MeshDeployment, timeout: int = 120
    ) -> bool:
        """Wait for all services to be ready."""
        logger.info("⏳ Waiting for services to be ready...")

        services_to_check = {
            "consul": "http://localhost:8500/v1/status/leader",
            "jaeger": "http://localhost:16686/api/services",
            "prometheus": "http://localhost:9090/-/ready",
            "grafana": "http://localhost:3000/api/health",
        }

        start_time = time.time()

        while time.time() - start_time < timeout:
            ready_services = []

            for service, health_url in services_to_check.items():
                try:
                    response = requests.get(health_url, timeout=5)
                    if response.status_code == 200:
                        ready_services.append(service)
                        logger.debug("✅ %s is ready", service)
                    else:
                        logger.debug(
                            "⏳ %s not ready yet (status: %d)",
                            service, response.status_code
                        )
                except requests.RequestException:
                    logger.debug(
                        "⏳ %s not ready yet (connection failed)", service
                    )

            if len(ready_services) == len(services_to_check):
                logger.info("✅ All services are ready")
                return True
            logger.info(
                "Waiting for %d/%d services...",
                len(ready_services), len(services_to_check)
            )
            await asyncio.sleep(5)

        logger.error("❌ Timeout waiting for services to be ready")
        return False

    async def register_services(self: MeshDeployment) -> bool:
        """Register services with Consul."""
        logger.info("📝 Registering services with Consul...")

        # Define services to register
        services = [
            {
                "ID": "event-collector-svc",
                "Name": "event-collector-svc",
                "Tags": ["grpc", "events", "v1.0.0"],
                "Address": "event-collector-svc",
                "Port": 50051,
                "Check": {
                    "GRPC": "event-collector-svc:50051",
                    "Interval": "30s",
                    "Timeout": "5s"
                }
            },
            {
                "ID": "auth-svc",
                "Name": "auth-svc",
                "Tags": ["grpc", "auth", "v1.0.0"],
                "Address": "auth-svc",
                "Port": 50051,
                "Check": {
                    "GRPC": "auth-svc:50051",
                    "Interval": "30s",
                    "Timeout": "5s"
                }
            },
            # Add more services as needed
        ]

        registered_count = 0

        for service in services:
            try:
                response = requests.put(
                    "http://localhost:8500/v1/agent/service/register",
                    json=service,
                    timeout=10
                )

                if response.status_code == 200:
                    logger.info("✅ Registered service: %s", service["Name"])
                    registered_count += 1
                else:
                    logger.warning(
                        "Failed to register service %s: %s",
                        service["Name"], response.text
                    )

            except requests.RequestException as e:
                logger.warning(
                    "Error registering service %s: %s", service["Name"], e
                )

        logger.info("📝 Registered %d services with Consul", registered_count)
        return registered_count > 0

    async def status(self: MeshDeployment) -> dict[str, bool]:
        """Check status of mesh components."""
        logger.info("📊 Checking mesh component status...")

        status_checks = {
            "consul": self._check_consul,
            "jaeger": self._check_jaeger,
            "prometheus": self._check_prometheus,
            "grafana": self._check_grafana,
            "certificates": self._check_certificates,
        }

        results = {}

        for component, check_func in status_checks.items():
            try:
                results[component] = await check_func()
            except (requests.RequestException, OSError, TimeoutError) as e:
                logger.error("Status check failed for %s: %s", component, e)
                results[component] = False

        # Print status summary
        print("\n" + "="*50)
        print("📊 MESH COMPONENT STATUS")
        print("="*50)

        for component, status in results.items():
            status_icon = "✅" if status else "❌"
            print(f"{component:15}: {status_icon}")

        print("="*50)

        return results

    async def _check_consul(self: MeshDeployment) -> bool:
        """Check Consul status."""
        try:
            response = requests.get(
                "http://localhost:8500/v1/status/leader", timeout=5
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    async def _check_jaeger(self: MeshDeployment) -> bool:
        """Check Jaeger status."""
        try:
            response = requests.get(
                "http://localhost:16686/api/services", timeout=5
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    async def _check_prometheus(self: MeshDeployment) -> bool:
        """Check Prometheus status."""
        try:
            response = requests.get(
                "http://localhost:9090/-/ready", timeout=5
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    async def _check_grafana(self: MeshDeployment) -> bool:
        """Check Grafana status."""
        try:
            response = requests.get(
                "http://localhost:3000/api/health", timeout=5
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    async def _check_certificates(self: MeshDeployment) -> bool:
        """Check certificate availability."""
        ca_cert = self.cert_dir / "ca" / "ca.crt"
        return ca_cert.exists()

    async def cleanup(self: MeshDeployment) -> bool:
        """Clean up mesh infrastructure."""
        logger.info("🧹 Cleaning up mesh infrastructure...")

        try:
            # Stop all containers
            result = subprocess.run([
                "docker-compose", "-f", str(self.compose_file), "down", "-v"
            ], capture_output=True, text=True, timeout=60, check=False)

            if result.returncode != 0:
                logger.error("Docker cleanup failed: %s", result.stderr)
                return False

            # Remove generated certificates (optional)
            # cert_cleanup = input("Remove generated certificates? (y/N): ")
            # if cert_cleanup.lower() == 'y':
            #     shutil.rmtree(self.cert_dir, ignore_errors=True)
            #     logger.info("Certificates removed")

            logger.info("✅ Cleanup completed")
            return True

        except (subprocess.SubprocessError, OSError) as e:
            logger.error("Cleanup error: %s", e)
            return False


async def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="gRPC Mesh Deployment Manager"
    )
    parser.add_argument(
        "--config-dir",
        default="./",
        help="Configuration directory path"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands"
    )

    # Deploy command
    deploy_parser = subparsers.add_parser(
        "deploy", help="Deploy mesh infrastructure"
    )
    deploy_parser.add_argument(
        "--components",
        nargs="+",
        help="Specific components to deploy"
    )

    # Status command
    subparsers.add_parser("status", help="Check mesh status")

    # Cleanup command
    subparsers.add_parser("cleanup", help="Clean up mesh infrastructure")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    deployment = MeshDeployment(args.config_dir)

    if args.command == "deploy":
        success = await deployment.deploy(args.components)
        sys.exit(0 if success else 1)

    elif args.command == "status":
        await deployment.status()

    elif args.command == "cleanup":
        success = await deployment.cleanup()
        sys.exit(0 if success else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
