"""
RBAC aggregator routes for admin portal service.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from opentelemetry import trace  # type: ignore[import-untyped]

from .cache_service import cache_service
from .config import get_settings
from .http_client import CircuitBreakerError, http_client

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
settings = get_settings()

router = APIRouter(prefix="/rbac", tags=["rbac"])


# Helper functions for tenant validation
async def get_tenant_id(
    tenant_id: str = Query(..., description="Tenant identifier"),
) -> str:
    """Validate and return tenant ID."""
    if not tenant_id or len(tenant_id) < 3:
        raise HTTPException(status_code=400, detail="Invalid tenant ID")
    return tenant_id


# Permission Matrix Endpoints

@router.get("/roles/matrix")
async def get_permission_matrix(
    tenant_id: str = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get permission matrix with UI-friendly formatting."""
    with tracer.start_as_current_span("get_permission_matrix") as span:
        span.set_attribute("tenant.id", tenant_id)

        try:
            # Check cache first
            cache_key = f"permission_matrix_{tenant_id}"
            cached_data = await cache_service.get(tenant_id, cache_key)
            if cached_data:
                span.set_attribute("cache.hit", True)
                return cached_data

            # Fetch from auth service
            auth_response = await http_client.get(
                f"auth-svc/rbac/roles/matrix",
                params={"tenant_id": tenant_id}
            )

            if auth_response.status_code != 200:
                raise HTTPException(
                    status_code=auth_response.status_code,
                    detail=f"Failed to fetch permission matrix: {auth_response.text}"
                )

            raw_data = auth_response.json()

            # Shape data for frontend consumption
            matrix_data = _format_permission_matrix(raw_data.get("data", {}))

            # Cache for 15 minutes
            await cache_service.set(tenant_id, cache_key, matrix_data, ttl=900)

            span.set_attribute("cache.hit", False)
            span.set_attribute("matrix.roles_count", len(matrix_data.get("roles", [])))
            span.set_attribute("matrix.permissions_count", len(matrix_data.get("permissions", [])))

            return matrix_data

        except CircuitBreakerError:
            span.record_exception(CircuitBreakerError)
            raise HTTPException(
                status_code=503,
                detail="Auth service is temporarily unavailable"
            )
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to get permission matrix for tenant %s: %s", tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve permission matrix: {str(e)}"
            )


def _format_permission_matrix(raw_matrix: Dict[str, Any]) -> Dict[str, Any]:
    """Format permission matrix for frontend consumption."""
    roles = raw_matrix.get("roles", [])
    permissions = raw_matrix.get("permissions", [])
    matrix = raw_matrix.get("matrix", {})

    # Group permissions by resource for better UI organization
    permission_groups = {}
    for perm in permissions:
        resource = perm.get("resource", "general")
        if resource not in permission_groups:
            permission_groups[resource] = []
        permission_groups[resource].append({
            "id": perm["id"],
            "name": perm["name"],
            "display_name": perm["display_name"],
            "action": perm.get("action", ""),
            "scope": perm.get("scope", "")
        })

    # Format roles with additional metadata
    formatted_roles = []
    for role in roles:
        role_permissions = matrix.get(role["id"], [])
        formatted_roles.append({
            "id": role["id"],
            "name": role["name"],
            "display_name": role["display_name"],
            "description": role.get("description", ""),
            "is_system": role.get("is_system", False),
            "is_active": role.get("is_active", True),
            "permission_count": len(role_permissions),
            "permissions": role_permissions
        })

    return {
        "tenant_id": raw_matrix.get("tenant_id"),
        "roles": formatted_roles,
        "permission_groups": permission_groups,
        "matrix": matrix,
        "summary": {
            "total_roles": len(roles),
            "total_permissions": len(permissions),
            "system_roles": len([r for r in roles if r.get("is_system", False)]),
            "custom_roles": len([r for r in roles if not r.get("is_system", False)])
        },
        "last_updated": datetime.utcnow().isoformat()
    }


# Role Management Endpoints

@router.get("/roles")
async def get_roles(
    tenant_id: str = Depends(get_tenant_id),
    include_permissions: bool = Query(False, description="Include role permissions")
) -> Dict[str, Any]:
    """Get roles with enhanced metadata for UI."""
    with tracer.start_as_current_span("get_roles") as span:
        span.set_attribute("tenant.id", tenant_id)
        span.set_attribute("include_permissions", include_permissions)

        try:
            # Fetch from auth service
            auth_response = await http_client.get(
                f"auth-svc/rbac/roles",
                params={"tenant_id": tenant_id}
            )

            if auth_response.status_code != 200:
                raise HTTPException(
                    status_code=auth_response.status_code,
                    detail=f"Failed to fetch roles: {auth_response.text}"
                )

            raw_data = auth_response.json()
            roles = raw_data.get("data", [])

            # Enhance roles with additional metadata
            enhanced_roles = []
            for role in roles:
                enhanced_role = {
                    **role,
                    "can_edit": not role.get("is_system", False),
                    "can_delete": not role.get("is_system", False),
                    "user_count": await _get_role_user_count(role["id"], tenant_id),
                }

                # Optionally include permissions
                if include_permissions:
                    enhanced_role["permissions"] = await _get_role_permissions(role["id"])

                enhanced_roles.append(enhanced_role)

            return {
                "success": True,
                "data": {
                    "roles": enhanced_roles,
                    "summary": {
                        "total": len(roles),
                        "system_roles": len([r for r in roles if r.get("is_system", False)]),
                        "custom_roles": len([r for r in roles if not r.get("is_system", False)]),
                        "active_roles": len([r for r in roles if r.get("is_active", True)])
                    }
                }
            }

        except CircuitBreakerError:
            raise HTTPException(
                status_code=503,
                detail="Auth service is temporarily unavailable"
            )
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to get roles for tenant %s: %s", tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve roles: {str(e)}"
            )


async def _get_role_user_count(role_id: str, tenant_id: str) -> int:
    """Get the number of users assigned to a role."""
    try:
        # This could be cached or fetched from auth service
        # For now, return a placeholder
        return 0
    except Exception:
        return 0


async def _get_role_permissions(role_id: str) -> List[Dict[str, Any]]:
    """Get permissions for a specific role."""
    try:
        auth_response = await http_client.get(f"auth-svc/rbac/roles/{role_id}/permissions")
        if auth_response.status_code == 200:
            return auth_response.json().get("data", {}).get("permissions", [])
        return []
    except Exception:
        return []


@router.post("/roles/custom")
async def create_custom_role(
    request: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Create a custom role with enhanced response."""
    with tracer.start_as_current_span("create_custom_role") as span:
        span.set_attribute("tenant.id", tenant_id)
        span.set_attribute("role.name", request.get("name", ""))

        try:
            # Add tenant_id to request
            request["tenant_id"] = tenant_id

            # Forward to auth service
            auth_response = await http_client.post(
                "auth-svc/rbac/roles/custom",
                json=request
            )

            if auth_response.status_code == 200:
                # Clear permission matrix cache
                await cache_service.delete(tenant_id, f"permission_matrix_{tenant_id}")

                result = auth_response.json()
                span.set_attribute("operation.success", True)

                return {
                    "success": True,
                    "data": result.get("data"),
                    "message": result.get("message"),
                    "ui_actions": {
                        "refresh_matrix": True,
                        "refresh_roles": True,
                        "show_notification": {
                            "type": "success",
                            "title": "Role Created",
                            "message": result.get("message")
                        }
                    }
                }
            else:
                error_data = auth_response.json()
                raise HTTPException(
                    status_code=auth_response.status_code,
                    detail=error_data.get("detail", "Failed to create role")
                )

        except CircuitBreakerError:
            raise HTTPException(
                status_code=503,
                detail="Auth service is temporarily unavailable"
            )
        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to create custom role for tenant %s: %s", tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create custom role: {str(e)}"
            )


@router.put("/roles/{role_id}")
async def update_role(
    role_id: str,
    request: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Update a role with cache invalidation."""
    with tracer.start_as_current_span("update_role") as span:
        span.set_attribute("tenant.id", tenant_id)
        span.set_attribute("role.id", role_id)

        try:
            # Forward to auth service
            auth_response = await http_client.put(
                f"auth-svc/rbac/roles/{role_id}",
                json=request
            )

            if auth_response.status_code == 200:
                # Clear caches
                await cache_service.delete(tenant_id, f"permission_matrix_{tenant_id}")

                result = auth_response.json()
                span.set_attribute("operation.success", True)

                return {
                    "success": True,
                    "data": result.get("data"),
                    "message": result.get("message"),
                    "ui_actions": {
                        "refresh_matrix": True,
                        "refresh_roles": True,
                        "show_notification": {
                            "type": "success",
                            "title": "Role Updated",
                            "message": result.get("message")
                        }
                    }
                }
            else:
                error_data = auth_response.json()
                raise HTTPException(
                    status_code=auth_response.status_code,
                    detail=error_data.get("detail", "Failed to update role")
                )

        except CircuitBreakerError:
            raise HTTPException(
                status_code=503,
                detail="Auth service is temporarily unavailable"
            )
        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to update role %s for tenant %s: %s", role_id, tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update role: {str(e)}"
            )


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: str,
    tenant_id: str = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Delete a role with cache invalidation."""
    with tracer.start_as_current_span("delete_role") as span:
        span.set_attribute("tenant.id", tenant_id)
        span.set_attribute("role.id", role_id)

        try:
            # Forward to auth service
            auth_response = await http_client.delete(f"auth-svc/rbac/roles/{role_id}")

            if auth_response.status_code == 200:
                # Clear caches
                await cache_service.delete(tenant_id, f"permission_matrix_{tenant_id}")

                result = auth_response.json()
                span.set_attribute("operation.success", True)

                return {
                    "success": True,
                    "message": result.get("message"),
                    "ui_actions": {
                        "refresh_matrix": True,
                        "refresh_roles": True,
                        "show_notification": {
                            "type": "success",
                            "title": "Role Deleted",
                            "message": result.get("message")
                        }
                    }
                }
            else:
                error_data = auth_response.json()
                raise HTTPException(
                    status_code=auth_response.status_code,
                    detail=error_data.get("detail", "Failed to delete role")
                )

        except CircuitBreakerError:
            raise HTTPException(
                status_code=503,
                detail="Auth service is temporarily unavailable"
            )
        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to delete role %s for tenant %s: %s", role_id, tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete role: {str(e)}"
            )


# Permission Management Endpoints

@router.get("/permissions")
async def get_permissions(
    tenant_id: str = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get all permissions grouped by resource."""
    with tracer.start_as_current_span("get_permissions") as span:
        span.set_attribute("tenant.id", tenant_id)

        try:
            # Check cache first
            cache_key = f"permissions_{tenant_id}"
            cached_data = await cache_service.get(tenant_id, cache_key)
            if cached_data:
                span.set_attribute("cache.hit", True)
                return cached_data

            # Fetch from auth service
            auth_response = await http_client.get("auth-svc/rbac/permissions")

            if auth_response.status_code != 200:
                raise HTTPException(
                    status_code=auth_response.status_code,
                    detail=f"Failed to fetch permissions: {auth_response.text}"
                )

            raw_data = auth_response.json()
            permissions = raw_data.get("data", [])

            # Group permissions by resource for better UI organization
            grouped_permissions = {}
            for perm in permissions:
                resource = perm.get("resource", "general")
                if resource not in grouped_permissions:
                    grouped_permissions[resource] = {
                        "resource": resource,
                        "permissions": []
                    }
                grouped_permissions[resource]["permissions"].append(perm)

            result = {
                "success": True,
                "data": {
                    "grouped_permissions": list(grouped_permissions.values()),
                    "all_permissions": permissions,
                    "summary": {
                        "total_permissions": len(permissions),
                        "resources": len(grouped_permissions)
                    }
                }
            }

            # Cache for 30 minutes
            await cache_service.set(tenant_id, cache_key, result, ttl=1800)

            span.set_attribute("cache.hit", False)
            span.set_attribute("permissions.count", len(permissions))

            return result

        except CircuitBreakerError:
            raise HTTPException(
                status_code=503,
                detail="Auth service is temporarily unavailable"
            )
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to get permissions for tenant %s: %s", tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve permissions: {str(e)}"
            )


@router.put("/roles/{role_id}/permissions")
async def update_role_permissions(
    role_id: str,
    request: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Update role permissions with cache invalidation."""
    with tracer.start_as_current_span("update_role_permissions") as span:
        span.set_attribute("tenant.id", tenant_id)
        span.set_attribute("role.id", role_id)
        span.set_attribute("permissions.count", len(request.get("permission_ids", [])))

        try:
            # Forward to auth service
            auth_response = await http_client.put(
                f"auth-svc/rbac/roles/{role_id}/permissions",
                json=request
            )

            if auth_response.status_code == 200:
                # Clear permission matrix cache
                await cache_service.delete(tenant_id, f"permission_matrix_{tenant_id}")

                result = auth_response.json()
                span.set_attribute("operation.success", True)

                return {
                    "success": True,
                    "message": result.get("message"),
                    "ui_actions": {
                        "refresh_matrix": True,
                        "refresh_role_permissions": role_id,
                        "show_notification": {
                            "type": "success",
                            "title": "Permissions Updated",
                            "message": result.get("message")
                        }
                    }
                }
            else:
                error_data = auth_response.json()
                raise HTTPException(
                    status_code=auth_response.status_code,
                    detail=error_data.get("detail", "Failed to update permissions")
                )

        except CircuitBreakerError:
            raise HTTPException(
                status_code=503,
                detail="Auth service is temporarily unavailable"
            )
        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to update permissions for role %s, tenant %s: %s", role_id, tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update role permissions: {str(e)}"
            )


# Access Review Endpoints

@router.post("/access-reviews/start")
async def create_access_review(
    request: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Create and start an access review."""
    with tracer.start_as_current_span("create_access_review") as span:
        span.set_attribute("tenant.id", tenant_id)
        span.set_attribute("review.scope", request.get("scope", ""))

        try:
            # Add tenant_id to request
            request["tenant_id"] = tenant_id

            # Forward to auth service
            auth_response = await http_client.post(
                "auth-svc/rbac/access-reviews/start",
                json=request
            )

            if auth_response.status_code == 200:
                result = auth_response.json()
                span.set_attribute("operation.success", True)
                span.set_attribute("review.id", result.get("data", {}).get("id", ""))

                return {
                    "success": True,
                    "data": result.get("data"),
                    "message": result.get("message"),
                    "ui_actions": {
                        "refresh_reviews": True,
                        "navigate_to_review": result.get("data", {}).get("id"),
                        "show_notification": {
                            "type": "success",
                            "title": "Access Review Started",
                            "message": result.get("message")
                        }
                    }
                }
            else:
                error_data = auth_response.json()
                raise HTTPException(
                    status_code=auth_response.status_code,
                    detail=error_data.get("detail", "Failed to create access review")
                )

        except CircuitBreakerError:
            raise HTTPException(
                status_code=503,
                detail="Auth service is temporarily unavailable"
            )
        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to create access review for tenant %s: %s", tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create access review: {str(e)}"
            )


@router.get("/access-reviews")
async def get_access_reviews(
    tenant_id: str = Depends(get_tenant_id),
    status: Optional[str] = Query(None, description="Filter by status"),
) -> Dict[str, Any]:
    """Get access reviews with enhanced metadata."""
    with tracer.start_as_current_span("get_access_reviews") as span:
        span.set_attribute("tenant.id", tenant_id)

        params = {"tenant_id": tenant_id}
        if status:
            params["status"] = status
            span.set_attribute("filter.status", status)

        try:
            # Fetch from auth service
            auth_response = await http_client.get(
                "auth-svc/rbac/access-reviews",
                params=params
            )

            if auth_response.status_code != 200:
                raise HTTPException(
                    status_code=auth_response.status_code,
                    detail=f"Failed to fetch access reviews: {auth_response.text}"
                )

            raw_data = auth_response.json()
            reviews = raw_data.get("data", [])

            # Enhance reviews with UI metadata
            enhanced_reviews = []
            for review in reviews:
                progress = 0
                if review.get("total_items", 0) > 0:
                    progress = (review.get("reviewed_items", 0) / review.get("total_items", 1)) * 100

                enhanced_review = {
                    **review,
                    "progress_percentage": round(progress, 1),
                    "is_overdue": _is_review_overdue(review.get("due_date")),
                    "days_remaining": _calculate_days_remaining(review.get("due_date")),
                    "can_complete": review.get("reviewed_items", 0) == review.get("total_items", 0),
                    "urgency_level": _calculate_urgency_level(review.get("due_date"), progress)
                }
                enhanced_reviews.append(enhanced_review)

            return {
                "success": True,
                "data": {
                    "reviews": enhanced_reviews,
                    "summary": {
                        "total": len(reviews),
                        "active": len([r for r in reviews if r.get("status") == "active"]),
                        "completed": len([r for r in reviews if r.get("status") == "completed"]),
                        "overdue": len([r for r in enhanced_reviews if r.get("is_overdue")])
                    }
                }
            }

        except CircuitBreakerError:
            raise HTTPException(
                status_code=503,
                detail="Auth service is temporarily unavailable"
            )
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to get access reviews for tenant %s: %s", tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve access reviews: {str(e)}"
            )


def _is_review_overdue(due_date_str: Optional[str]) -> bool:
    """Check if a review is overdue."""
    if not due_date_str:
        return False
    try:
        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
        return datetime.utcnow().replace(tzinfo=due_date.tzinfo) > due_date
    except Exception:
        return False


def _calculate_days_remaining(due_date_str: Optional[str]) -> Optional[int]:
    """Calculate days remaining until due date."""
    if not due_date_str:
        return None
    try:
        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
        diff = due_date - datetime.utcnow().replace(tzinfo=due_date.tzinfo)
        return max(0, diff.days)
    except Exception:
        return None


def _calculate_urgency_level(due_date_str: Optional[str], progress: float) -> str:
    """Calculate urgency level based on due date and progress."""
    days_remaining = _calculate_days_remaining(due_date_str)

    if days_remaining is None:
        return "low"

    if days_remaining <= 0:
        return "critical"
    elif days_remaining <= 3 and progress < 50:
        return "high"
    elif days_remaining <= 7 and progress < 25:
        return "medium"
    else:
        return "low"


@router.get("/access-reviews/{review_id}/items")
async def get_review_items(
    review_id: str,
    tenant_id: str = Depends(get_tenant_id),
    status: Optional[str] = Query(None, description="Filter by item status"),
) -> Dict[str, Any]:
    """Get review items with enhanced formatting."""
    with tracer.start_as_current_span("get_review_items") as span:
        span.set_attribute("tenant.id", tenant_id)
        span.set_attribute("review.id", review_id)

        params = {}
        if status:
            params["status"] = status
            span.set_attribute("filter.status", status)

        try:
            # Fetch from auth service
            auth_response = await http_client.get(
                f"auth-svc/rbac/access-reviews/{review_id}/items",
                params=params
            )

            if auth_response.status_code != 200:
                raise HTTPException(
                    status_code=auth_response.status_code,
                    detail=f"Failed to fetch review items: {auth_response.text}"
                )

            raw_data = auth_response.json()
            items = raw_data.get("data", {}).get("items", [])

            # Enhance items with UI metadata
            enhanced_items = []
            for item in items:
                enhanced_item = {
                    **item,
                    "needs_attention": item.get("status") == "pending",
                    "risk_level": _calculate_access_risk_level(item),
                    "formatted_last_access": _format_last_access_date(item.get("last_access_date"))
                }
                enhanced_items.append(enhanced_item)

            return {
                "success": True,
                "data": {
                    "review_id": review_id,
                    "items": enhanced_items,
                    "summary": {
                        "total": len(items),
                        "pending": len([i for i in items if i.get("status") == "pending"]),
                        "approved": len([i for i in items if i.get("status") == "approved"]),
                        "revoked": len([i for i in items if i.get("status") == "revoked"])
                    }
                }
            }

        except CircuitBreakerError:
            raise HTTPException(
                status_code=503,
                detail="Auth service is temporarily unavailable"
            )
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to get review items for review %s, tenant %s: %s", review_id, tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve review items: {str(e)}"
            )


def _calculate_access_risk_level(item: Dict[str, Any]) -> str:
    """Calculate risk level for an access item."""
    # This is a simplified risk calculation
    # In practice, this would be more sophisticated

    last_access = item.get("last_access_date")
    role_privileges = item.get("role_privileges", [])

    # High risk if no recent access and high privileges
    if not last_access and any("admin" in priv.lower() for priv in role_privileges):
        return "high"
    elif not last_access:
        return "medium"
    else:
        return "low"


def _format_last_access_date(last_access_str: Optional[str]) -> str:
    """Format last access date for UI display."""
    if not last_access_str:
        return "Never"

    try:
        last_access = datetime.fromisoformat(last_access_str.replace('Z', '+00:00'))
        diff = datetime.utcnow().replace(tzinfo=last_access.tzinfo) - last_access

        if diff.days == 0:
            return "Today"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        else:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
    except Exception:
        return "Unknown"


@router.post("/access-reviews/{review_id}/decision")
async def submit_review_decision(
    review_id: str,
    item_id: str = Query(..., description="Review item ID"),
    request: Dict[str, Any] = ...,
    tenant_id: str = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Submit a review decision with UI feedback."""
    with tracer.start_as_current_span("submit_review_decision") as span:
        span.set_attribute("tenant.id", tenant_id)
        span.set_attribute("review.id", review_id)
        span.set_attribute("item.id", item_id)
        span.set_attribute("decision", request.get("decision", ""))

        try:
            # Forward to auth service
            auth_response = await http_client.post(
                f"auth-svc/rbac/access-reviews/{review_id}/decision",
                params={"item_id": item_id},
                json=request
            )

            if auth_response.status_code == 200:
                result = auth_response.json()
                span.set_attribute("operation.success", True)

                return {
                    "success": True,
                    "message": result.get("message"),
                    "ui_actions": {
                        "refresh_review_items": review_id,
                        "refresh_review_progress": review_id,
                        "show_notification": {
                            "type": "success",
                            "title": "Decision Recorded",
                            "message": f"Access {request.get('decision', 'decision')} recorded successfully"
                        }
                    }
                }
            else:
                error_data = auth_response.json()
                raise HTTPException(
                    status_code=auth_response.status_code,
                    detail=error_data.get("detail", "Failed to submit decision")
                )

        except CircuitBreakerError:
            raise HTTPException(
                status_code=503,
                detail="Auth service is temporarily unavailable"
            )
        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to submit decision for review %s, tenant %s: %s", review_id, tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to submit review decision: {str(e)}"
            )


# User Role Management Endpoints (delegated to auth service)

@router.post("/users/roles/assign")
async def assign_user_role(
    request: Dict[str, Any],
    tenant_id: str = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Assign role to user with UI feedback."""
    with tracer.start_as_current_span("assign_user_role") as span:
        span.set_attribute("tenant.id", tenant_id)
        span.set_attribute("user.id", request.get("user_id", ""))
        span.set_attribute("role.id", request.get("role_id", ""))

        try:
            # Ensure tenant_id is in request
            request["tenant_id"] = tenant_id

            # Forward to auth service
            auth_response = await http_client.post(
                "auth-svc/rbac/users/roles/assign",
                json=request
            )

            if auth_response.status_code == 200:
                result = auth_response.json()
                span.set_attribute("operation.success", True)

                return {
                    "success": True,
                    "data": result.get("data"),
                    "message": result.get("message"),
                    "ui_actions": {
                        "refresh_user_roles": request.get("user_id"),
                        "refresh_matrix": True,
                        "show_notification": {
                            "type": "success",
                            "title": "Role Assigned",
                            "message": result.get("message")
                        }
                    }
                }
            else:
                error_data = auth_response.json()
                raise HTTPException(
                    status_code=auth_response.status_code,
                    detail=error_data.get("detail", "Failed to assign role")
                )

        except CircuitBreakerError:
            raise HTTPException(
                status_code=503,
                detail="Auth service is temporarily unavailable"
            )
        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to assign role for tenant %s: %s", tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to assign user role: {str(e)}"
            )


@router.delete("/users/roles/{user_role_id}")
async def revoke_user_role(
    user_role_id: str,
    tenant_id: str = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Revoke user role with UI feedback."""
    with tracer.start_as_current_span("revoke_user_role") as span:
        span.set_attribute("tenant.id", tenant_id)
        span.set_attribute("user_role.id", user_role_id)

        try:
            # Forward to auth service
            auth_response = await http_client.delete(
                f"auth-svc/rbac/users/roles/{user_role_id}"
            )

            if auth_response.status_code == 200:
                result = auth_response.json()
                span.set_attribute("operation.success", True)

                return {
                    "success": True,
                    "message": result.get("message"),
                    "ui_actions": {
                        "refresh_matrix": True,
                        "show_notification": {
                            "type": "success",
                            "title": "Role Revoked",
                            "message": result.get("message")
                        }
                    }
                }
            else:
                error_data = auth_response.json()
                raise HTTPException(
                    status_code=auth_response.status_code,
                    detail=error_data.get("detail", "Failed to revoke role")
                )

        except CircuitBreakerError:
            raise HTTPException(
                status_code=503,
                detail="Auth service is temporarily unavailable"
            )
        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            logger.error("Failed to revoke role %s for tenant %s: %s", user_role_id, tenant_id, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to revoke user role: {str(e)}"
            )
