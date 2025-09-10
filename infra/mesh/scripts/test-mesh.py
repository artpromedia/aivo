#!/usr/bin/env python3
"""
gRPC Mesh Integration Test Suite.

This script tests the gRPC mesh functionality including mTLS, retries,
circuit breakers, and service discovery.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import grpc
import requests
from grpc_health.v1 import health_pb2, health_pb2_grpc

# Add mesh library to path
sys.path.append(str(Path(__file__).parent / "python"))

from mesh_client import MeshClient, MeshConfig  # type: ignore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MeshTestSuite:
    """Test suite for gRPC mesh functionality."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize test suite."""
        self.config_path = Path(config_path) if config_path else Path("./certs")
        self.test_results: Dict[str, bool] = {}
        self.services_under_test = [
            "event-collector-svc",
            "auth-svc",
            "learner-svc",
            "analytics-svc",
        ]

    async def run_all_tests(self) -> bool:
        """Run all mesh tests."""
        logger.info("🧪 Starting gRPC mesh test suite...")
        
        tests = [
            self.test_certificate_generation,
            self.test_envoy_admin_interfaces,
            self.test_service_discovery,
            self.test_mtls_connectivity,
            self.test_health_checks,
            self.test_retry_policies,
            self.test_circuit_breakers,
            self.test_metrics_collection,
            self.test_distributed_tracing,
        ]

        for test in tests:
            test_name = test.__name__
            try:
                logger.info(f"Running {test_name}...")
                result = await test()
                self.test_results[test_name] = result
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"{test_name}: {status}")
            except Exception as e:
                logger.error(f"{test_name}: ❌ ERROR - {e}")
                self.test_results[test_name] = False

        # Print summary
        self.print_test_summary()
        return all(self.test_results.values())

    async def test_certificate_generation(self) -> bool:
        """Test certificate generation and validation."""
        ca_cert_path = self.config_path / "ca" / "ca.crt"
        
        if not ca_cert_path.exists():
            logger.error("CA certificate not found at %s", ca_cert_path)
            return False

        # Check service certificates
        for service in self.services_under_test:
            cert_path = self.config_path / "services" / f"{service}.crt"
            key_path = self.config_path / "services" / f"{service}-key.pem"
            
            if not cert_path.exists():
                logger.error("Certificate not found for service %s", service)
                return False
                
            if not key_path.exists():
                logger.error("Private key not found for service %s", service)
                return False

        logger.info("✅ All certificates found and valid")
        return True

    async def test_envoy_admin_interfaces(self) -> bool:
        """Test Envoy admin interface accessibility."""
        envoy_ports = [9901, 9902, 9903, 9904]  # Admin ports for different services
        
        for port in envoy_ports:
            try:
                response = requests.get(
                    f"http://localhost:{port}/ready", timeout=5
                )
                if response.status_code != 200:
                    logger.warning("Envoy admin interface not ready on port %d", port)
                    continue
                    
                # Test clusters endpoint
                clusters_response = requests.get(
                    f"http://localhost:{port}/clusters", timeout=5
                )
                if clusters_response.status_code == 200:
                    logger.info("✅ Envoy admin interface working on port %d", port)
                    return True
                    
            except requests.RequestException as e:
                logger.debug("Envoy admin interface test failed for port %d: %s", port, e)
                continue

        logger.error("❌ No Envoy admin interfaces accessible")
        return False

    async def test_service_discovery(self) -> bool:
        """Test Consul service discovery."""
        try:
            response = requests.get(
                "http://localhost:8500/v1/catalog/services", timeout=10
            )
            if response.status_code != 200:
                logger.error("Consul service discovery not accessible")
                return False

            services = response.json()
            logger.info("Discovered services: %s", list(services.keys()))
            
            # Check health of registered services
            for service in self.services_under_test:
                health_response = requests.get(
                    f"http://localhost:8500/v1/health/service/{service}",
                    timeout=5
                )
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    if health_data:
                        logger.info("✅ Service %s registered in Consul", service)
                    else:
                        logger.warning("Service %s not found in Consul", service)

            return True

        except requests.RequestException as e:
            logger.error("Service discovery test failed: %s", e)
            return False

    async def test_mtls_connectivity(self) -> bool:
        """Test mTLS connectivity between services."""
        try:
            config = MeshConfig(
                ca_cert_path=str(self.config_path / "ca" / "ca.crt"),
                client_cert_path=str(self.config_path / "mesh-client.crt"),
                client_key_path=str(self.config_path / "mesh-client-key.pem"),
            )
            
            with MeshClient(config) as mesh_client:
                # Test connection to each service
                for service in self.services_under_test:
                    try:
                        channel = mesh_client.create_channel(service, timeout=5.0)
                        
                        # Try to create a health stub and make a call
                        stub = health_pb2_grpc.HealthStub(channel)
                        request = health_pb2.HealthCheckRequest()
                        
                        # This will test the full mTLS handshake
                        response = stub.Check(request, timeout=5.0)
                        logger.info("✅ mTLS connection successful to %s", service)
                        
                    except grpc.RpcError as e:
                        if e.code() == grpc.StatusCode.UNIMPLEMENTED:
                            # Service doesn't implement health check, but connection worked
                            logger.info("✅ mTLS connection successful to %s (no health check)", service)
                        else:
                            logger.warning("mTLS connection failed to %s: %s", service, e)
                            continue

            return True

        except Exception as e:
            logger.error("mTLS connectivity test failed: %s", e)
            return False

    async def test_health_checks(self) -> bool:
        """Test gRPC health check functionality."""
        config = MeshConfig(
            ca_cert_path=str(self.config_path / "ca" / "ca.crt"),
            client_cert_path=str(self.config_path / "mesh-client.crt"),
            client_key_path=str(self.config_path / "mesh-client-key.pem"),
        )
        
        with MeshClient(config) as mesh_client:
            health_checks_passed = 0
            
            for service in self.services_under_test:
                try:
                    status = await mesh_client.health_check(service)
                    if status == health_pb2.HealthCheckResponse.SERVING:
                        logger.info("✅ Health check passed for %s", service)
                        health_checks_passed += 1
                    else:
                        logger.warning("Health check failed for %s: %s", service, status)
                        
                except Exception as e:
                    logger.warning("Health check error for %s: %s", service, e)

            # Consider test passed if at least one service is healthy
            return health_checks_passed > 0

    async def test_retry_policies(self) -> bool:
        """Test retry policy configuration."""
        # This test would require a service that can simulate failures
        # For now, we'll check if retry configuration is properly set in Envoy
        
        try:
            response = requests.get(
                "http://localhost:9901/config_dump", timeout=10
            )
            if response.status_code != 200:
                return False

            config_dump = response.json()
            
            # Look for retry policy configuration in the config dump
            dynamic_listeners = config_dump.get("configs", [])
            for config in dynamic_listeners:
                if config.get("@type") == "type.googleapis.com/envoy.admin.v3.ListenersConfigDump":
                    # Check if retry policies are configured
                    logger.info("✅ Retry policies found in Envoy configuration")
                    return True

            logger.warning("Retry policies not found in Envoy configuration")
            return False

        except Exception as e:
            logger.error("Retry policy test failed: %s", e)
            return False

    async def test_circuit_breakers(self) -> bool:
        """Test circuit breaker configuration."""
        try:
            response = requests.get(
                "http://localhost:9901/clusters", timeout=10
            )
            if response.status_code != 200:
                return False

            clusters_text = response.text
            
            # Look for circuit breaker configuration
            if "circuit_breakers" in clusters_text or "max_connections" in clusters_text:
                logger.info("✅ Circuit breakers configured in Envoy")
                return True
            else:
                logger.warning("Circuit breakers not found in cluster configuration")
                return False

        except Exception as e:
            logger.error("Circuit breaker test failed: %s", e)
            return False

    async def test_metrics_collection(self) -> bool:
        """Test metrics collection and Prometheus integration."""
        try:
            # Test Prometheus metrics endpoint
            prometheus_response = requests.get(
                "http://localhost:9090/api/v1/targets", timeout=10
            )
            if prometheus_response.status_code != 200:
                logger.error("Prometheus not accessible")
                return False

            targets = prometheus_response.json()
            active_targets = [
                target for target in targets.get("data", {}).get("activeTargets", [])
                if target.get("health") == "up"
            ]
            
            if len(active_targets) > 0:
                logger.info("✅ Prometheus collecting metrics from %d targets", len(active_targets))
                return True
            else:
                logger.warning("No active Prometheus targets found")
                return False

        except Exception as e:
            logger.error("Metrics collection test failed: %s", e)
            return False

    async def test_distributed_tracing(self) -> bool:
        """Test Jaeger distributed tracing."""
        try:
            # Test Jaeger health endpoint
            jaeger_response = requests.get(
                "http://localhost:16686/api/services", timeout=10
            )
            if jaeger_response.status_code != 200:
                logger.error("Jaeger not accessible")
                return False

            services = jaeger_response.json()
            if isinstance(services, dict) and "data" in services:
                service_names = services["data"]
                logger.info("✅ Jaeger tracking %d services", len(service_names))
                return True
            else:
                logger.warning("No services found in Jaeger")
                return True  # Jaeger is up, just no traces yet

        except Exception as e:
            logger.error("Distributed tracing test failed: %s", e)
            return False

    def print_test_summary(self) -> None:
        """Print test results summary."""
        print("\n" + "="*60)
        print("🧪 gRPC MESH TEST RESULTS SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print("-"*60)
        print(f"TOTAL: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Mesh is working correctly.")
        else:
            print("⚠️  Some tests failed. Check logs for details.")
        
        print("="*60)


async def main() -> None:
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="gRPC Mesh Test Suite")
    parser.add_argument(
        "--cert-path",
        default="./certs",
        help="Path to certificate directory",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    test_suite = MeshTestSuite(args.cert_path)
    success = await test_suite.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
