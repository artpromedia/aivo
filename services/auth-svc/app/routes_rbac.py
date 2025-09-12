"""
RBAC API routes for role and permission management.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session

from .database import get_db
from .rbac import get_rbac_service, RBACService
from .security import get_current_user
from .models import User
from .schemas import ErrorResponse


router = APIRouter(prefix="/rbac", tags=["rbac"])


# Pydantic schemas for RBAC endpoints

from pydantic import BaseModel, Field


class RoleCreateRequest(BaseModel):
    """Schema for role creation."""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    tenant_id: Optional[uuid.UUID] = None


class RoleUpdateRequest(BaseModel):
    """Schema for role updates."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class RolePermissionsUpdateRequest(BaseModel):
    """Schema for updating role permissions."""
    permission_ids: List[uuid.UUID] = Field(..., description="List of permission IDs to assign")


class UserRoleAssignRequest(BaseModel):
    """Schema for assigning roles to users."""
    user_id: uuid.UUID
    role_id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    expires_at: Optional[datetime] = None


class AccessReviewCreateRequest(BaseModel):
    """Schema for creating access reviews."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    tenant_id: Optional[uuid.UUID] = None
    scope: str = Field("admin", pattern="^(admin|all_users|role_specific)$")
    target_role_id: Optional[uuid.UUID] = None
    due_days: int = Field(30, ge=1, le=365)


class ReviewDecisionRequest(BaseModel):
    """Schema for access review decisions."""
    decision: str = Field(..., pattern="^(approve|revoke|no_change)$")
    notes: Optional[str] = Field(None, max_length=1000)
    justification: Optional[str] = Field(None, max_length=2000)


class RoleResponse(BaseModel):
    """Role response schema."""
    id: str
    name: str
    display_name: str
    description: Optional[str]
    tenant_id: Optional[str]
    is_system: bool
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime


class PermissionResponse(BaseModel):
    """Permission response schema."""
    id: str
    name: str
    display_name: str
    description: Optional[str]
    resource: str
    action: str
    scope: str


class AccessReviewResponse(BaseModel):
    """Access review response schema."""
    id: str
    title: str
    description: Optional[str]
    tenant_id: Optional[str]
    scope: str
    status: str
    total_items: int
    reviewed_items: int
    approved_items: int
    revoked_items: int
    due_date: datetime
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


# Role Management Endpoints

@router.get("/roles/matrix")
async def get_permission_matrix(
    tenant_id: Optional[uuid.UUID] = Query(None, description="Tenant ID for permission matrix"),
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Dict[str, Any]:
    """Get the permission matrix for a tenant."""

    # Check if user has permission to view role matrix
    if not rbac_service.check_permission(current_user.id, "roles.read", tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view role matrix"
        )

    try:
        matrix = rbac_service.get_permission_matrix(tenant_id)
        return {
            "success": True,
            "data": matrix
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve permission matrix: {str(e)}"
        )


@router.get("/roles")
async def get_roles(
    tenant_id: Optional[uuid.UUID] = Query(None, description="Tenant ID to filter roles"),
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Dict[str, Any]:
    """Get all roles for a tenant."""

    if not rbac_service.check_permission(current_user.id, "roles.read", tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view roles"
        )

    try:
        roles = rbac_service.get_roles_by_tenant(tenant_id)
        role_data = []

        for role in roles:
            role_data.append({
                "id": str(role.id),
                "name": role.name,
                "display_name": role.display_name,
                "description": role.description,
                "tenant_id": str(role.tenant_id) if role.tenant_id else None,
                "is_system": role.is_system,
                "is_active": role.is_active,
                "priority": role.priority,
                "created_at": role.created_at,
                "updated_at": role.updated_at
            })

        return {
            "success": True,
            "data": role_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve roles: {str(e)}"
        )


@router.post("/roles/custom")
async def create_custom_role(
    request: RoleCreateRequest,
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Dict[str, Any]:
    """Create a new custom role."""

    if not rbac_service.check_permission(current_user.id, "roles.create", request.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create roles"
        )

    try:
        # Check if role name already exists for this tenant
        existing_roles = rbac_service.get_roles_by_tenant(request.tenant_id)
        if any(r.name == request.name for r in existing_roles):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{request.name}' already exists"
            )

        role = rbac_service.create_role(
            name=request.name,
            display_name=request.display_name,
            tenant_id=request.tenant_id,
            description=request.description,
            creator_id=current_user.id
        )

        return {
            "success": True,
            "data": {
                "id": str(role.id),
                "name": role.name,
                "display_name": role.display_name,
                "description": role.description,
                "tenant_id": str(role.tenant_id) if role.tenant_id else None,
                "is_system": role.is_system,
                "created_at": role.created_at
            },
            "message": f"Custom role '{role.display_name}' created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create role: {str(e)}"
        )


@router.put("/roles/{role_id}")
async def update_role(
    role_id: uuid.UUID,
    request: RoleUpdateRequest,
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Dict[str, Any]:
    """Update an existing role."""

    # Get the role to check tenant context
    roles = rbac_service.get_roles_by_tenant()  # Get all roles
    role = next((r for r in roles if r.id == role_id), None)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    if not rbac_service.check_permission(current_user.id, "roles.update", role.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update roles"
        )

    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify system roles"
        )

    try:
        # Convert request to dict, excluding None values
        updates = {k: v for k, v in request.dict().items() if v is not None}

        updated_role = rbac_service.update_role(role_id, updates, current_user.id)

        if not updated_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found or cannot be updated"
            )

        return {
            "success": True,
            "data": {
                "id": str(updated_role.id),
                "name": updated_role.name,
                "display_name": updated_role.display_name,
                "description": updated_role.description,
                "is_active": updated_role.is_active,
                "updated_at": updated_role.updated_at
            },
            "message": f"Role '{updated_role.display_name}' updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update role: {str(e)}"
        )


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Dict[str, Any]:
    """Delete a custom role."""

    # Get the role to check tenant context
    roles = rbac_service.get_roles_by_tenant()
    role = next((r for r in roles if r.id == role_id), None)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    if not rbac_service.check_permission(current_user.id, "roles.delete", role.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete roles"
        )

    try:
        success = rbac_service.delete_role(role_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete system role or role not found"
            )

        return {
            "success": True,
            "message": f"Role '{role.display_name}' deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete role: {str(e)}"
        )


# Permission Management Endpoints

@router.get("/permissions")
async def get_permissions(
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Dict[str, Any]:
    """Get all system permissions."""

    if not rbac_service.check_permission(current_user.id, "permissions.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view permissions"
        )

    try:
        permissions = rbac_service.get_all_permissions()

        permission_data = []
        for perm in permissions:
            permission_data.append({
                "id": str(perm.id),
                "name": perm.name,
                "display_name": perm.display_name,
                "description": perm.description,
                "resource": perm.resource,
                "action": perm.action,
                "scope": perm.scope
            })

        return {
            "success": True,
            "data": permission_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve permissions: {str(e)}"
        )


@router.get("/roles/{role_id}/permissions")
async def get_role_permissions(
    role_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Dict[str, Any]:
    """Get permissions for a specific role."""

    # Get role to check tenant context
    roles = rbac_service.get_roles_by_tenant()
    role = next((r for r in roles if r.id == role_id), None)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    if not rbac_service.check_permission(current_user.id, "roles.read", role.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view role permissions"
        )

    try:
        permissions = rbac_service.get_role_permissions(role_id)

        permission_data = []
        for perm in permissions:
            permission_data.append({
                "id": str(perm.id),
                "name": perm.name,
                "display_name": perm.display_name,
                "resource": perm.resource,
                "action": perm.action,
                "scope": perm.scope
            })

        return {
            "success": True,
            "data": {
                "role_id": str(role_id),
                "role_name": role.name,
                "permissions": permission_data
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve role permissions: {str(e)}"
        )


@router.put("/roles/{role_id}/permissions")
async def update_role_permissions(
    role_id: uuid.UUID,
    request: RolePermissionsUpdateRequest,
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Dict[str, Any]:
    """Update permissions for a role."""

    # Get role to check tenant context
    roles = rbac_service.get_roles_by_tenant()
    role = next((r for r in roles if r.id == role_id), None)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    if not rbac_service.check_permission(current_user.id, "roles.update", role.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update role permissions"
        )

    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify permissions for system roles"
        )

    try:
        success = rbac_service.update_role_permissions(
            role_id,
            request.permission_ids,
            current_user.id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update role permissions"
            )

        return {
            "success": True,
            "message": f"Permissions updated for role '{role.display_name}'"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update role permissions: {str(e)}"
        )


# User Role Management Endpoints

@router.post("/users/roles/assign")
async def assign_user_role(
    request: UserRoleAssignRequest,
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Dict[str, Any]:
    """Assign a role to a user."""

    if not rbac_service.check_permission(current_user.id, "user_roles.create", request.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to assign roles"
        )

    try:
        user_role = rbac_service.assign_role_to_user(
            user_id=request.user_id,
            role_id=request.role_id,
            tenant_id=request.tenant_id,
            assigned_by=current_user.id,
            expires_at=request.expires_at
        )

        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to assign role to user"
            )

        return {
            "success": True,
            "data": {
                "user_role_id": str(user_role.id),
                "user_id": str(user_role.user_id),
                "role_id": str(user_role.role_id),
                "tenant_id": str(user_role.tenant_id) if user_role.tenant_id else None,
                "expires_at": user_role.expires_at,
                "created_at": user_role.created_at
            },
            "message": "Role assigned to user successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign role: {str(e)}"
        )


@router.delete("/users/roles/{user_role_id}")
async def revoke_user_role(
    user_role_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Dict[str, Any]:
    """Revoke a user's role assignment."""

    # TODO: Check tenant context for the user role
    if not rbac_service.check_permission(current_user.id, "user_roles.delete"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to revoke roles"
        )

    try:
        success = rbac_service.revoke_user_role(user_role_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User role assignment not found"
            )

        return {
            "success": True,
            "message": "Role revoked from user successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke role: {str(e)}"
        )


@router.get("/users/{user_id}/roles")
async def get_user_roles(
    user_id: uuid.UUID,
    tenant_id: Optional[uuid.UUID] = Query(None, description="Tenant context for roles"),
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Dict[str, Any]:
    """Get all roles for a user."""

    # Users can view their own roles, admins can view any user's roles
    if user_id != current_user.id and not rbac_service.check_permission(current_user.id, "user_roles.read", tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view user roles"
        )

    try:
        user_roles = rbac_service.get_user_roles(user_id, tenant_id)

        return {
            "success": True,
            "data": {
                "user_id": str(user_id),
                "tenant_id": str(tenant_id) if tenant_id else None,
                "roles": user_roles
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user roles: {str(e)}"
        )


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: uuid.UUID,
    tenant_id: Optional[uuid.UUID] = Query(None, description="Tenant context for permissions"),
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Dict[str, Any]:
    """Get effective permissions for a user."""

    # Users can view their own permissions, admins can view any user's permissions
    if user_id != current_user.id and not rbac_service.check_permission(current_user.id, "user_roles.read", tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view user permissions"
        )

    try:
        permissions = rbac_service.get_user_permissions(user_id, tenant_id)

        return {
            "success": True,
            "data": {
                "user_id": str(user_id),
                "tenant_id": str(tenant_id) if tenant_id else None,
                "permissions": list(permissions)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user permissions: {str(e)}"
        )


# Access Review Endpoints

@router.post("/access-reviews/start")
async def create_access_review(
    request: AccessReviewCreateRequest,
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Dict[str, Any]:
    """Create and start a new access review."""

    if not rbac_service.check_permission(current_user.id, "access_reviews.create", request.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create access reviews"
        )

    try:
        review = rbac_service.create_access_review(
            title=request.title,
            tenant_id=request.tenant_id,
            scope=request.scope,
            target_role_id=request.target_role_id,
            due_days=request.due_days,
            started_by=current_user.id,
            description=request.description
        )

        # Automatically start the review
        rbac_service.start_access_review(review.id, current_user.id)

        return {
            "success": True,
            "data": {
                "id": str(review.id),
                "title": review.title,
                "scope": review.scope,
                "status": "active",
                "total_items": review.total_items,
                "due_date": review.due_date,
                "created_at": review.created_at
            },
            "message": f"Access review '{review.title}' created and started successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create access review: {str(e)}"
        )


@router.get("/access-reviews")
async def get_access_reviews(
    tenant_id: Optional[uuid.UUID] = Query(None, description="Tenant ID to filter reviews"),
    status: Optional[str] = Query(None, description="Status to filter reviews"),
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Dict[str, Any]:
    """Get access reviews."""

    if not rbac_service.check_permission(current_user.id, "access_reviews.read", tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view access reviews"
        )

    try:
        reviews = rbac_service.get_access_reviews(tenant_id, status)

        review_data = []
        for review in reviews:
            review_data.append({
                "id": str(review.id),
                "title": review.title,
                "description": review.description,
                "tenant_id": str(review.tenant_id) if review.tenant_id else None,
                "scope": review.scope,
                "status": review.status,
                "total_items": review.total_items,
                "reviewed_items": review.reviewed_items,
                "approved_items": review.approved_items,
                "revoked_items": review.revoked_items,
                "due_date": review.due_date,
                "created_at": review.created_at,
                "started_at": review.started_at,
                "completed_at": review.completed_at
            })

        return {
            "success": True,
            "data": review_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve access reviews: {str(e)}"
        )


@router.get("/access-reviews/{review_id}/items")
async def get_review_items(
    review_id: uuid.UUID,
    status: Optional[str] = Query(None, description="Status to filter items"),
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Dict[str, Any]:
    """Get items for a specific access review."""

    # TODO: Check tenant context for the review
    if not rbac_service.check_permission(current_user.id, "access_reviews.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view review items"
        )

    try:
        items = rbac_service.get_review_items(review_id, status)

        return {
            "success": True,
            "data": {
                "review_id": str(review_id),
                "items": items
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve review items: {str(e)}"
        )


@router.post("/access-reviews/{review_id}/decision")
async def submit_review_decision(
    review_id: uuid.UUID,
    item_id: uuid.UUID = Query(..., description="Review item ID"),
    request: ReviewDecisionRequest = ...,
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Dict[str, Any]:
    """Submit a decision for an access review item."""

    # TODO: Check tenant context for the review
    if not rbac_service.check_permission(current_user.id, "access_reviews.decide"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to make review decisions"
        )

    try:
        success = rbac_service.submit_review_decision(
            review_item_id=item_id,
            decision=request.decision,
            reviewer_id=current_user.id,
            notes=request.notes,
            justification=request.justification
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review item not found or already processed"
            )

        return {
            "success": True,
            "message": f"Review decision '{request.decision}' submitted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit review decision: {str(e)}"
        )


# Audit Log Endpoints

@router.get("/audit-logs")
async def get_audit_logs(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[uuid.UUID] = Query(None, description="Filter by entity ID"),
    tenant_id: Optional[uuid.UUID] = Query(None, description="Filter by tenant ID"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
) -> Dict[str, Any]:
    """Get audit logs with filtering options."""

    if not rbac_service.check_permission(current_user.id, "audit_logs.read", tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view audit logs"
        )

    try:
        logs = rbac_service.get_audit_logs(
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            limit=limit
        )

        log_data = []
        for log in logs:
            log_data.append({
                "id": str(log.id),
                "event_type": log.event_type,
                "entity_type": log.entity_type,
                "entity_id": str(log.entity_id),
                "actor_id": str(log.actor_id),
                "tenant_id": str(log.tenant_id) if log.tenant_id else None,
                "event_data": log.event_data,
                "changes": log.changes,
                "timestamp": log.timestamp
            })

        return {
            "success": True,
            "data": log_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit logs: {str(e)}"
        )
