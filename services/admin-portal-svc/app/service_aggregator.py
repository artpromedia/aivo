"""
Service aggregator for collecting data from downstream services.
"""

import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Any

import httpx

from .cache_service import cache_service
from .config import get_settings
from .http_client import CircuitBreakerError, http_client
from .schemas import (
    BillingHistoryResponse,
    NamespacesResponse,
    SubscriptionDetails,
    SummaryResponse,
    TeamResponse,
    UsageResponse,
)

logger = logging.getLogger(__name__)


class ServiceAggregator:
    """Aggregates data from downstream services for admin dashboard."""

    def __init__(self) -> None:
        """Initialize service aggregator."""
        self.settings = get_settings()

    async def _get_cached_or_fetch(
        self,
        tenant_id: str,
        endpoint: str,
        fetch_func: Callable[[], Awaitable[Any]],
        ttl: int | None = None,
    ) -> Any:
        """Get data from cache or fetch from service."""
        # Try cache first
        cached_data = await cache_service.get(tenant_id, endpoint)
        if cached_data is not None:
            return cached_data

        # Fetch from service
        try:
            data = await fetch_func()
            # Cache the result
            await cache_service.set(tenant_id, endpoint, data, ttl)
            return data
        except (
            httpx.HTTPError,
            CircuitBreakerError,
            ValueError,
            TypeError,
        ) as e:
            logger.error("Failed to fetch data for %s: %s", endpoint, e)
            # Return empty/default data structure
            return self._get_fallback_data(endpoint, tenant_id)

    def _get_fallback_data(self, endpoint: str, tenant_id: str = "unknown") -> dict[str, Any]:
        """Get fallback data when services are unavailable."""
        fallbacks = {
            "summary": {
                "tenant_id": tenant_id,
                "tenant_name": "Unknown",
                "status": "suspended",
                "subscription_tier": "free",
                "total_users": 0,
                "active_users_30d": 0,
                "total_documents": 0,
                "pending_approvals": 0,
                "monthly_spend": "0.00",
                "usage_alerts": 0,
                "health_score": 0.0,
            },
            "subscription": {
                "tenant_id": tenant_id,
                "current_tier": "free",
                "billing_cycle": "monthly",
                "next_billing_date": datetime.utcnow().isoformat(),
                "monthly_cost": "0.00",
                "features": [],
                "usage_limits": {},
                "auto_renewal": False,
            },
            "billing-history": {
                "tenant_id": tenant_id,
                "current_balance": "0.00",
                "invoices": [],
                "total_spent_ytd": "0.00",
            },
            "team": {
                "tenant_id": tenant_id,
                "total_members": 0,
                "active_members": 0,
                "pending_invites": 0,
                "members": [],
                "role_distribution": {},
                "recent_activity": [],
            },
            "usage": {
                "tenant_id": tenant_id,
                "billing_period_start": datetime.utcnow().isoformat(),
                "billing_period_end": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "metrics": [],
                "total_api_calls": 0,
                "total_storage_gb": 0.0,
                "bandwidth_gb": 0.0,
                "cost_breakdown": {},
                "projected_monthly_cost": "0.00",
                "usage_trends": {},
            },
            "namespaces": {
                "tenant_id": tenant_id,
                "total_namespaces": 0,
                "active_namespaces": 0,
                "total_documents": 0,
                "total_storage_gb": 0.0,
                "namespaces": [],
                "storage_distribution": {},
            },
        }
        return fallbacks.get(endpoint, {})

    async def get_summary(self, tenant_id: str) -> SummaryResponse:
        """Get dashboard summary data."""

        async def fetch_summary() -> dict[str, Any]:
            # Fetch data from multiple services concurrently
            tasks = {
                "tenant": self._get_tenant_info(tenant_id),
                "users": self._get_user_stats(tenant_id),
                "documents": self._get_document_stats(tenant_id),
                "approvals": self._get_approval_stats(tenant_id),
                "billing": self._get_billing_summary(tenant_id),
                "usage": self._get_usage_alerts(tenant_id),
            }

            results = {}
            for key, task in tasks.items():
                try:
                    results[key] = await task
                except (httpx.HTTPError, CircuitBreakerError) as e:
                    logger.warning("Failed to fetch %s for summary: %s", key, e)
                    results[key] = {}

            # Aggregate into summary response
            tenant_info = results.get("tenant", {})
            user_stats = results.get("users", {})
            doc_stats = results.get("documents", {})
            approval_stats = results.get("approvals", {})
            billing_info = results.get("billing", {})
            usage_alerts = results.get("usage", {})

            return {
                "tenant_id": tenant_id,
                "tenant_name": tenant_info.get("name", "Unknown"),
                "status": tenant_info.get("status", "suspended"),
                "subscription_tier": tenant_info.get("subscription_tier", "free"),
                "total_users": user_stats.get("total", 0),
                "active_users_30d": user_stats.get("active_30d", 0),
                "total_documents": doc_stats.get("total", 0),
                "pending_approvals": approval_stats.get("pending", 0),
                "monthly_spend": billing_info.get("current_month_spend", "0.00"),
                "usage_alerts": usage_alerts.get("count", 0),
                "last_activity": user_stats.get("last_activity"),
                "health_score": self._calculate_health_score(results),
            }

        data = await self._get_cached_or_fetch(tenant_id, "summary", fetch_summary)
        return SummaryResponse(**data)

    async def get_subscription(self, tenant_id: str) -> SubscriptionDetails:
        """Get subscription details."""

        async def fetch_subscription() -> dict[str, Any]:
            subscription_data = await http_client.get(
                "tenant_service",
                f"{self.settings.tenant_service_url}/tenants/" f"{tenant_id}/subscription",
            )

            # Enrich with payment service data
            try:
                payment_data = await http_client.get(
                    "payment_service",
                    f"{self.settings.payment_service_url}/subscriptions/" f"{tenant_id}",
                )
                subscription_data.update(payment_data)
            except (httpx.HTTPError, CircuitBreakerError) as e:
                logger.warning("Failed to get payment data: %s", e)

            return subscription_data

        data = await self._get_cached_or_fetch(tenant_id, "subscription", fetch_subscription)
        return SubscriptionDetails(**data)

    async def get_billing_history(self, tenant_id: str) -> BillingHistoryResponse:
        """Get billing history."""

        async def fetch_billing() -> dict[str, Any]:
            billing_data = await http_client.get(
                "payment_service",
                f"{self.settings.payment_service_url}/billing/" f"{tenant_id}/history",
            )

            # Transform invoice data
            invoices = []
            for invoice in billing_data.get("invoices", []):
                invoices.append(
                    {
                        "invoice_id": invoice.get("id"),
                        "date": invoice.get("created_at"),
                        "amount": invoice.get("amount"),
                        "status": invoice.get("status"),
                        "description": invoice.get("description"),
                        "download_url": invoice.get("pdf_url"),
                    }
                )

            return {
                "tenant_id": tenant_id,
                "current_balance": billing_data.get("balance", "0.00"),
                "next_payment_due": billing_data.get("next_payment_due"),
                "payment_method": billing_data.get("default_payment_method"),
                "invoices": invoices,
                "total_spent_ytd": billing_data.get("ytd_total", "0.00"),
            }

        data = await self._get_cached_or_fetch(tenant_id, "billing-history", fetch_billing)
        return BillingHistoryResponse(**data)

    async def get_team(self, tenant_id: str) -> TeamResponse:
        """Get team information."""

        async def fetch_team() -> dict[str, Any]:
            team_data = await http_client.get(
                "tenant_service",
                f"{self.settings.tenant_service_url}/tenants/" f"{tenant_id}/team",
            )

            # Transform member data
            members = []
            for member in team_data.get("members", []):
                members.append(
                    {
                        "user_id": member.get("id"),
                        "email": member.get("email"),
                        "name": member.get("name"),
                        "role": member.get("role"),
                        "status": member.get("status"),
                        "last_login": member.get("last_login"),
                        "permissions": member.get("permissions", []),
                        "invite_status": member.get("invite_status"),
                    }
                )

            return {
                "tenant_id": tenant_id,
                "total_members": len(members),
                "active_members": len([m for m in members if m["status"] == "active"]),
                "pending_invites": len([m for m in members if m.get("invite_status") == "pending"]),
                "members": members,
                "role_distribution": team_data.get("role_distribution", {}),
                "recent_activity": team_data.get("recent_activity", []),
            }

        data = await self._get_cached_or_fetch(tenant_id, "team", fetch_team)
        return TeamResponse(**data)

    async def get_usage(self, tenant_id: str) -> UsageResponse:
        """Get usage metrics."""

        async def fetch_usage() -> dict[str, Any]:
            # Get usage from analytics service (when available) or
            # tenant service
            try:
                usage_data = await http_client.get(
                    "analytics_service",
                    f"{self.settings.analytics_service_url}/usage/" f"{tenant_id}",
                )
            except CircuitBreakerError:
                # Fallback to tenant service
                usage_data = await http_client.get(
                    "tenant_service",
                    f"{self.settings.tenant_service_url}/tenants/" f"{tenant_id}/usage",
                )

            # Transform metrics
            metrics = []
            for metric in usage_data.get("metrics", []):
                metrics.append(
                    {
                        "metric_name": metric.get("name"),
                        "current_value": metric.get("current"),
                        "limit_value": metric.get("limit"),
                        "percentage_used": metric.get("percentage", 0.0),
                        "unit": metric.get("unit", "count"),
                    }
                )

            return {
                "tenant_id": tenant_id,
                "billing_period_start": usage_data.get("period_start"),
                "billing_period_end": usage_data.get("period_end"),
                "metrics": metrics,
                "total_api_calls": usage_data.get("api_calls", 0),
                "total_storage_gb": usage_data.get("storage_gb", 0.0),
                "bandwidth_gb": usage_data.get("bandwidth_gb", 0.0),
                "cost_breakdown": usage_data.get("cost_breakdown", {}),
                "projected_monthly_cost": usage_data.get("projected_cost", "0.00"),
                "usage_trends": usage_data.get("trends", {}),
            }

        data = await self._get_cached_or_fetch(tenant_id, "usage", fetch_usage)
        return UsageResponse(**data)

    async def get_namespaces(self, tenant_id: str) -> NamespacesResponse:
        """Get namespace information."""

        async def fetch_namespaces() -> dict[str, Any]:
            namespaces_data = await http_client.get(
                "fm_orchestrator",
                f"{self.settings.fm_orchestrator_url}/tenants/" f"{tenant_id}/namespaces",
            )

            # Transform namespace data
            namespaces = []
            for ns in namespaces_data.get("namespaces", []):
                namespaces.append(
                    {
                        "namespace_id": ns.get("id"),
                        "name": ns.get("name"),
                        "status": ns.get("status"),
                        "document_count": ns.get("document_count", 0),
                        "storage_used_mb": ns.get("storage_mb", 0.0),
                        "last_updated": ns.get("updated_at"),
                        "model_deployments": ns.get("model_count", 0),
                        "active_workflows": ns.get("workflow_count", 0),
                    }
                )

            total_storage_gb = sum(ns["storage_used_mb"] for ns in namespaces) / 1024

            return {
                "tenant_id": tenant_id,
                "total_namespaces": len(namespaces),
                "active_namespaces": len([ns for ns in namespaces if ns["status"] == "active"]),
                "total_documents": sum(ns["document_count"] for ns in namespaces),
                "total_storage_gb": total_storage_gb,
                "namespaces": namespaces,
                "storage_distribution": {
                    ns["name"]: ns["storage_used_mb"] / 1024
                    for ns in namespaces
                    if ns["storage_used_mb"] > 0
                },
            }

        data = await self._get_cached_or_fetch(tenant_id, "namespaces", fetch_namespaces)
        return NamespacesResponse(**data)

    # Helper methods for fetching specific data
    async def _get_tenant_info(self, tenant_id: str) -> dict[str, Any]:
        """Get basic tenant information."""
        return await http_client.get(
            "tenant_service",
            f"{self.settings.tenant_service_url}/tenants/{tenant_id}",
        )

    async def _get_user_stats(self, tenant_id: str) -> dict[str, Any]:
        """Get user statistics."""
        return await http_client.get(
            "tenant_service",
            f"{self.settings.tenant_service_url}/tenants/" f"{tenant_id}/users/stats",
        )

    async def _get_document_stats(self, tenant_id: str) -> dict[str, Any]:
        """Get document statistics."""
        try:
            return await http_client.get(
                "fm_orchestrator",
                f"{self.settings.fm_orchestrator_url}/tenants/" f"{tenant_id}/documents/stats",
            )
        except (httpx.HTTPError, CircuitBreakerError):
            return {"total": 0}

    async def _get_approval_stats(self, tenant_id: str) -> dict[str, Any]:
        """Get approval statistics."""
        try:
            return await http_client.get(
                "approval_service",
                f"{self.settings.approval_service_url}/approvals/" f"stats?tenant_id={tenant_id}",
            )
        except (httpx.HTTPError, CircuitBreakerError):
            return {"pending": 0}

    async def _get_billing_summary(self, tenant_id: str) -> dict[str, Any]:
        """Get billing summary."""
        try:
            return await http_client.get(
                "payment_service",
                f"{self.settings.payment_service_url}/billing/" f"{tenant_id}/summary",
            )
        except (httpx.HTTPError, CircuitBreakerError):
            return {"current_month_spend": "0.00"}

    async def _get_usage_alerts(self, tenant_id: str) -> dict[str, Any]:
        """Get usage alerts."""
        try:
            return await http_client.get(
                "tenant_service",
                f"{self.settings.tenant_service_url}/tenants/" f"{tenant_id}/alerts",
            )
        except (httpx.HTTPError, CircuitBreakerError):
            return {"count": 0}

    def _calculate_health_score(self, data: dict[str, Any]) -> float:
        """Calculate overall tenant health score."""
        score = 100.0

        # Deduct for service availability issues
        failed_services = sum(1 for service_data in data.values() if not service_data)
        score -= failed_services * 10

        # Deduct for usage alerts
        usage_alerts = data.get("usage", {}).get("count", 0)
        score -= usage_alerts * 5

        # Deduct for pending approvals
        pending_approvals = data.get("approvals", {}).get("pending", 0)
        if pending_approvals > 10:
            score -= 10
        elif pending_approvals > 5:
            score -= 5

        return max(0.0, min(100.0, score))


# Global service aggregator instance
service_aggregator = ServiceAggregator()
