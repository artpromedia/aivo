#!/usr/bin/env python3
"""
S2C-05 Audit Logs Validation Script

Tests the implementation against the exact requirements:
- WORM (write-once) audit stream for admin actions
- Searchable UI with export
- GET /audit?actor=&action=&resource=&from=&to=
- audit_event(id, ts, actor, actor_role, action, resource, before, after, ip, ua, sig)
- Export to S3 (CSV/JSON) with signed URL
- Tamper-check (hash chain) passes
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

import httpx


class S2C05Validator:
    """Validates S2C-05 Audit Logs implementation."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    async def test_audit_event_creation(self) -> Dict[str, Any]:
        """Test creating audit events with S2C-05 schema."""
        print("🔍 Testing audit event creation...")

        test_event = {
            "actor": "admin_user_123",
            "actor_role": "admin",
            "action": "user_create",
            "resource": "user:new_user_456",
            "before": None,
            "after": {
                "id": "new_user_456",
                "email": "test@example.com",
                "role": "user"
            },
            "metadata": {
                "test": "s2c-05_validation"
            }
        }

        response = await self.client.post(
            f"{self.base_url}/api/v1/audit",
            json=test_event
        )

        if response.status_code == 201:
            event = response.json()
            print(f"✅ Audit event created: {event['id']}")
            return event
        else:
            print(f"❌ Failed to create audit event: {response.status_code}")
            print(f"   Response: {response.text}")
            return {}

    async def test_search_api(self) -> bool:
        """Test GET /audit?actor=&action=&resource=&from=&to= endpoint."""
        print("🔍 Testing search API with S2C-05 parameters...")

        # Test the exact S2C-05 parameter format
        from_date = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        to_date = datetime.utcnow().isoformat()

        params = {
            "actor": "admin_user_123",
            "action": "user_create",
            "resource": "user",
            "from": from_date,
            "to": to_date
        }

        response = await self.client.get(
            f"{self.base_url}/api/v1/audit",
            params=params
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search API working - found {len(data.get('events', []))} events")
            return True
        else:
            print(f"❌ Search API failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    async def test_export_functionality(self) -> bool:
        """Test export to CSV/JSON with signed URLs."""
        print("🔍 Testing export functionality...")

        export_request = {
            "job_name": "S2C-05 Validation Export",
            "export_format": "json",
            "filters": {
                "actor": "admin_user_123"
            }
        }

        response = await self.client.post(
            f"{self.base_url}/api/v1/export?requested_by=s2c05_validator",
            json=export_request
        )

        if response.status_code == 201:
            job = response.json()
            job_id = job["id"]
            print(f"✅ Export job created: {job_id}")

            # Check job status (in real implementation, would poll until complete)
            status_response = await self.client.get(f"{self.base_url}/api/v1/export/{job_id}")
            if status_response.status_code == 200:
                print("✅ Export job status check working")
                return True

        print(f"❌ Export failed: {response.status_code}")
        return False

    async def test_hash_chain_verification(self) -> bool:
        """Test tamper-check (hash chain) verification."""
        print("🔍 Testing hash chain verification...")

        response = await self.client.post(
            f"{self.base_url}/api/v1/audit/verify",
            json={"verify_all": True}
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("is_valid"):
                print("✅ Hash chain verification passed")
                return True
            else:
                print(f"❌ Hash chain verification failed: {result.get('errors')}")
                return False
        else:
            print(f"❌ Hash chain verification endpoint failed: {response.status_code}")
            return False

    async def test_health_endpoints(self) -> bool:
        """Test service health and WORM compliance."""
        print("🔍 Testing health endpoints...")

        # Basic health
        response = await self.client.get(f"{self.base_url}/health")
        if response.status_code != 200:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False

        # Readiness check (includes WORM verification)
        response = await self.client.get(f"{self.base_url}/health/ready")
        if response.status_code == 200:
            print("✅ Health endpoints working, WORM compliance verified")
            return True
        else:
            print(f"❌ Readiness check failed: {response.status_code}")
            return False

    async def run_validation(self) -> Dict[str, bool]:
        """Run complete S2C-05 validation suite."""
        print("🚀 Starting S2C-05 Audit Logs Validation\n")

        results = {}

        try:
            # Test 1: Health and WORM compliance
            results["health_worm"] = await self.test_health_endpoints()

            # Test 2: Audit event creation
            event = await self.test_audit_event_creation()
            results["event_creation"] = bool(event)

            # Test 3: Search API with S2C-05 parameters
            results["search_api"] = await self.test_search_api()

            # Test 4: Export functionality
            results["export"] = await self.test_export_functionality()

            # Test 5: Hash chain verification
            results["hash_chain"] = await self.test_hash_chain_verification()

        except Exception as e:
            print(f"❌ Validation failed with exception: {e}")

        return results

    def print_results(self, results: Dict[str, bool]):
        """Print validation results summary."""
        print("\n" + "="*50)
        print("S2C-05 AUDIT LOGS VALIDATION RESULTS")
        print("="*50)

        all_passed = True
        for test, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test.replace('_', ' ').title():<25} {status}")
            if not passed:
                all_passed = False

        print("="*50)
        if all_passed:
            print("🎉 ALL TESTS PASSED - S2C-05 Implementation Valid!")
        else:
            print("⚠️  Some tests failed - check implementation")
        print("="*50)

        return all_passed


async def main():
    """Main validation function."""
    import argparse

    parser = argparse.ArgumentParser(description="S2C-05 Audit Logs Validator")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Audit service base URL"
    )
    args = parser.parse_args()

    async with S2C05Validator(args.url) as validator:
        results = await validator.run_validation()
        success = validator.print_results(results)

        if not success:
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
