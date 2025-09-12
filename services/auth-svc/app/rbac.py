"""
RBAC service for role and permission management.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from .models import (
    User, Role, Permission, RolePermission, UserRole,
    AccessReview, AccessReviewItem, AuditLog
)
from .database import get_db


class RBACService:
    """Service for Role-Based Access Control operations."""

    def __init__(self, db: Session):
        self.db = db

    # Role Management

    def create_role(
        self,
        name: str,
        display_name: str,
        tenant_id: Optional[uuid.UUID] = None,
        description: Optional[str] = None,
        creator_id: Optional[uuid.UUID] = None
    ) -> Role:
        """Create a new custom role."""
        role = Role(
            name=name,
            display_name=display_name,
            description=description,
            tenant_id=tenant_id,
            is_system=False
        )

        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)

        # Audit log
        if creator_id:
            self._log_audit_event(
                event_type="role_created",
                entity_type="role",
                entity_id=role.id,
                actor_id=creator_id,
                tenant_id=tenant_id,
                event_data={
                    "role_name": name,
                    "display_name": display_name,
                    "is_custom": True
                }
            )

        return role

    def update_role(
        self,
        role_id: uuid.UUID,
        updates: Dict[str, Any],
        actor_id: uuid.UUID
    ) -> Optional[Role]:
        """Update an existing role."""
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role or role.is_system:
            return None

        # Track changes for audit
        changes = {}
        for key, value in updates.items():
            if hasattr(role, key):
                old_value = getattr(role, key)
                if old_value != value:
                    changes[key] = {"from": old_value, "to": value}
                    setattr(role, key, value)

        if changes:
            self.db.commit()
            self.db.refresh(role)

            # Audit log
            self._log_audit_event(
                event_type="role_updated",
                entity_type="role",
                entity_id=role.id,
                actor_id=actor_id,
                tenant_id=role.tenant_id,
                event_data={"role_name": role.name},
                changes=changes
            )

        return role

    def get_roles_by_tenant(self, tenant_id: Optional[uuid.UUID] = None) -> List[Role]:
        """Get all roles for a tenant (including system roles)."""
        query = self.db.query(Role).filter(
            or_(
                Role.tenant_id == tenant_id,
                Role.tenant_id.is_(None)  # System roles
            )
        ).filter(Role.is_active == True)

        return query.order_by(Role.priority.desc(), Role.name).all()

    def delete_role(self, role_id: uuid.UUID, actor_id: uuid.UUID) -> bool:
        """Soft delete a custom role."""
        role = self.db.query(Role).filter(
            Role.id == role_id,
            Role.is_system == False
        ).first()

        if not role:
            return False

        # Check if role is in use
        active_assignments = self.db.query(UserRole).filter(
            UserRole.role_id == role_id,
            UserRole.is_active == True
        ).count()

        if active_assignments > 0:
            # Just deactivate, don't delete
            role.is_active = False
        else:
            # Safe to delete
            self.db.delete(role)

        self.db.commit()

        # Audit log
        self._log_audit_event(
            event_type="role_deleted",
            entity_type="role",
            entity_id=role_id,
            actor_id=actor_id,
            tenant_id=role.tenant_id,
            event_data={
                "role_name": role.name,
                "had_active_assignments": active_assignments > 0
            }
        )

        return True

    # Permission Management

    def get_all_permissions(self) -> List[Permission]:
        """Get all system permissions."""
        return self.db.query(Permission).order_by(
            Permission.resource, Permission.action
        ).all()

    def get_role_permissions(self, role_id: uuid.UUID) -> List[Permission]:
        """Get all permissions for a specific role."""
        return self.db.query(Permission).join(
            RolePermission, Permission.id == RolePermission.permission_id
        ).filter(
            RolePermission.role_id == role_id,
            RolePermission.granted == True
        ).all()

    def update_role_permissions(
        self,
        role_id: uuid.UUID,
        permission_ids: List[uuid.UUID],
        actor_id: uuid.UUID
    ) -> bool:
        """Update permissions for a role."""
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role or role.is_system:
            return False

        # Get current permissions
        current_perms = set(
            p.permission_id for p in self.db.query(RolePermission).filter(
                RolePermission.role_id == role_id,
                RolePermission.granted == True
            ).all()
        )

        new_perms = set(permission_ids)

        # Calculate changes
        to_add = new_perms - current_perms
        to_remove = current_perms - new_perms

        # Remove permissions
        if to_remove:
            self.db.query(RolePermission).filter(
                RolePermission.role_id == role_id,
                RolePermission.permission_id.in_(to_remove)
            ).delete(synchronize_session=False)

        # Add new permissions
        for perm_id in to_add:
            role_perm = RolePermission(
                role_id=role_id,
                permission_id=perm_id,
                granted=True
            )
            self.db.add(role_perm)

        self.db.commit()

        # Audit log
        if to_add or to_remove:
            self._log_audit_event(
                event_type="role_permissions_updated",
                entity_type="role",
                entity_id=role_id,
                actor_id=actor_id,
                tenant_id=role.tenant_id,
                event_data={
                    "role_name": role.name,
                    "permissions_added": len(to_add),
                    "permissions_removed": len(to_remove)
                },
                changes={
                    "added_permissions": list(to_add),
                    "removed_permissions": list(to_remove)
                }
            )

        return True

    # Permission Matrix

    def get_permission_matrix(self, tenant_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """Get the complete permission matrix for a tenant."""
        # Get all roles for the tenant
        roles = self.get_roles_by_tenant(tenant_id)

        # Get all permissions
        permissions = self.get_all_permissions()

        # Build permission matrix
        matrix = {
            "roles": [],
            "permissions": [],
            "matrix": {}
        }

        # Add roles
        for role in roles:
            matrix["roles"].append({
                "id": str(role.id),
                "name": role.name,
                "display_name": role.display_name,
                "is_system": role.is_system,
                "tenant_id": str(role.tenant_id) if role.tenant_id else None
            })

        # Add permissions grouped by resource
        resources = {}
        for permission in permissions:
            if permission.resource not in resources:
                resources[permission.resource] = []

            resources[permission.resource].append({
                "id": str(permission.id),
                "name": permission.name,
                "display_name": permission.display_name,
                "action": permission.action,
                "scope": permission.scope
            })

        matrix["permissions"] = resources

        # Build matrix data
        for role in roles:
            role_perms = self.get_role_permissions(role.id)
            perm_ids = {str(p.id) for p in role_perms}

            matrix["matrix"][str(role.id)] = perm_ids

        return matrix

    # User Role Management

    def assign_role_to_user(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        tenant_id: Optional[uuid.UUID] = None,
        assigned_by: Optional[uuid.UUID] = None,
        expires_at: Optional[datetime] = None
    ) -> Optional[UserRole]:
        """Assign a role to a user."""
        # Check if assignment already exists
        existing = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.tenant_id == tenant_id,
            UserRole.is_active == True
        ).first()

        if existing:
            return existing

        # Create new assignment
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            tenant_id=tenant_id,
            assigned_by=assigned_by or user_id,
            expires_at=expires_at,
            is_active=True
        )

        self.db.add(user_role)
        self.db.commit()
        self.db.refresh(user_role)

        # Audit log
        if assigned_by:
            role = self.db.query(Role).filter(Role.id == role_id).first()
            self._log_audit_event(
                event_type="role_assigned",
                entity_type="user_role",
                entity_id=user_role.id,
                actor_id=assigned_by,
                tenant_id=tenant_id,
                event_data={
                    "user_id": str(user_id),
                    "role_name": role.name if role else "unknown",
                    "expires_at": expires_at.isoformat() if expires_at else None
                }
            )

        return user_role

    def revoke_user_role(
        self,
        user_role_id: uuid.UUID,
        revoked_by: uuid.UUID
    ) -> bool:
        """Revoke a user's role assignment."""
        user_role = self.db.query(UserRole).filter(
            UserRole.id == user_role_id,
            UserRole.is_active == True
        ).first()

        if not user_role:
            return False

        user_role.is_active = False
        self.db.commit()

        # Audit log
        role = self.db.query(Role).filter(Role.id == user_role.role_id).first()
        self._log_audit_event(
            event_type="role_revoked",
            entity_type="user_role",
            entity_id=user_role_id,
            actor_id=revoked_by,
            tenant_id=user_role.tenant_id,
            event_data={
                "user_id": str(user_role.user_id),
                "role_name": role.name if role else "unknown"
            }
        )

        return True

    def get_user_roles(
        self,
        user_id: uuid.UUID,
        tenant_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get all active roles for a user in a tenant context."""
        query = self.db.query(UserRole, Role).join(
            Role, UserRole.role_id == Role.id
        ).filter(
            UserRole.user_id == user_id,
            UserRole.is_active == True,
            Role.is_active == True
        )

        if tenant_id is not None:
            query = query.filter(
                or_(
                    UserRole.tenant_id == tenant_id,
                    UserRole.tenant_id.is_(None)  # Global roles
                )
            )

        results = []
        for user_role, role in query.all():
            results.append({
                "user_role_id": str(user_role.id),
                "role_id": str(role.id),
                "role_name": role.name,
                "display_name": role.display_name,
                "tenant_id": str(user_role.tenant_id) if user_role.tenant_id else None,
                "assigned_at": user_role.created_at,
                "expires_at": user_role.expires_at
            })

        return results

    def get_user_permissions(
        self,
        user_id: uuid.UUID,
        tenant_id: Optional[uuid.UUID] = None
    ) -> Set[str]:
        """Get all effective permissions for a user."""
        # Get user's roles
        user_roles = self.get_user_roles(user_id, tenant_id)
        role_ids = [ur["role_id"] for ur in user_roles]

        if not role_ids:
            return set()

        # Get all permissions for these roles
        permissions = self.db.query(Permission).join(
            RolePermission, Permission.id == RolePermission.permission_id
        ).filter(
            RolePermission.role_id.in_(role_ids),
            RolePermission.granted == True
        ).all()

        return {p.name for p in permissions}

    # Access Reviews

    def create_access_review(
        self,
        title: str,
        tenant_id: Optional[uuid.UUID] = None,
        scope: str = "admin",
        target_role_id: Optional[uuid.UUID] = None,
        due_days: int = 30,
        started_by: Optional[uuid.UUID] = None,
        description: Optional[str] = None
    ) -> AccessReview:
        """Create a new access review."""
        due_date = datetime.utcnow() + timedelta(days=due_days)

        review = AccessReview(
            title=title,
            description=description,
            tenant_id=tenant_id,
            scope=scope,
            target_role_id=target_role_id,
            status="draft",
            started_by=started_by,
            due_date=due_date
        )

        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)

        # Create review items based on scope
        self._create_review_items(review)

        # Audit log
        if started_by:
            self._log_audit_event(
                event_type="access_review_created",
                entity_type="access_review",
                entity_id=review.id,
                actor_id=started_by,
                tenant_id=tenant_id,
                event_data={
                    "title": title,
                    "scope": scope,
                    "due_date": due_date.isoformat(),
                    "total_items": review.total_items
                }
            )

        return review

    def _create_review_items(self, review: AccessReview) -> None:
        """Create review items based on the review scope."""
        query = self.db.query(UserRole, User, Role).join(
            User, UserRole.user_id == User.id
        ).join(
            Role, UserRole.role_id == Role.id
        ).filter(
            UserRole.is_active == True,
            Role.is_active == True
        )

        # Apply scope filtering
        if review.scope == "admin":
            # Only admin roles
            query = query.filter(Role.name.in_(["admin", "district_admin"]))
        elif review.scope == "role_specific" and review.target_role_id:
            # Specific role
            query = query.filter(Role.id == review.target_role_id)

        # Apply tenant filtering
        if review.tenant_id:
            query = query.filter(
                or_(
                    UserRole.tenant_id == review.tenant_id,
                    UserRole.tenant_id.is_(None)  # Global assignments
                )
            )

        # Create review items
        items_created = 0
        for user_role, user, role in query.all():
            # Assess risk level based on role and permissions
            risk_level = self._assess_risk_level(role, user_role)

            review_item = AccessReviewItem(
                review_id=review.id,
                user_id=user.id,
                user_role_id=user_role.id,
                risk_level=risk_level,
                status="pending"
            )

            self.db.add(review_item)
            items_created += 1

        # Update review statistics
        review.total_items = items_created
        self.db.commit()

    def _assess_risk_level(self, role: Role, user_role: UserRole) -> str:
        """Assess risk level for a role assignment."""
        # Simple risk assessment logic
        if role.name in ["admin", "system_admin"]:
            return "critical"
        elif role.name in ["district_admin", "staff"]:
            return "high"
        elif user_role.expires_at and user_role.expires_at < datetime.utcnow():
            return "high"  # Expired assignments
        else:
            return "medium"

    def start_access_review(self, review_id: uuid.UUID, actor_id: uuid.UUID) -> bool:
        """Start an access review (change status from draft to active)."""
        review = self.db.query(AccessReview).filter(
            AccessReview.id == review_id,
            AccessReview.status == "draft"
        ).first()

        if not review:
            return False

        review.status = "active"
        review.started_at = datetime.utcnow()
        self.db.commit()

        # Audit log
        self._log_audit_event(
            event_type="access_review_started",
            entity_type="access_review",
            entity_id=review_id,
            actor_id=actor_id,
            tenant_id=review.tenant_id,
            event_data={
                "title": review.title,
                "total_items": review.total_items
            }
        )

        return True

    def submit_review_decision(
        self,
        review_item_id: uuid.UUID,
        decision: str,  # approve, revoke, no_change
        reviewer_id: uuid.UUID,
        notes: Optional[str] = None,
        justification: Optional[str] = None
    ) -> bool:
        """Submit a decision for a review item."""
        review_item = self.db.query(AccessReviewItem).filter(
            AccessReviewItem.id == review_item_id,
            AccessReviewItem.status == "pending"
        ).first()

        if not review_item:
            return False

        # Update item
        review_item.decision = decision
        review_item.reviewer_id = reviewer_id
        review_item.review_notes = notes
        review_item.justification = justification
        review_item.reviewed_at = datetime.utcnow()

        # Set status based on decision
        if decision == "approve":
            review_item.status = "approved"
        elif decision == "revoke":
            review_item.status = "revoked"
            # Actually revoke the role
            self.revoke_user_role(review_item.user_role_id, reviewer_id)
        else:
            review_item.status = "no_action"

        # Update review statistics
        review = self.db.query(AccessReview).filter(
            AccessReview.id == review_item.review_id
        ).first()

        if review:
            review.reviewed_items += 1
            if decision == "approve":
                review.approved_items += 1
            elif decision == "revoke":
                review.revoked_items += 1

            # Check if review is complete
            if review.reviewed_items >= review.total_items:
                review.status = "completed"
                review.completed_at = datetime.utcnow()

        self.db.commit()

        # Audit log
        self._log_audit_event(
            event_type="access_review_decision",
            entity_type="access_review_item",
            entity_id=review_item_id,
            actor_id=reviewer_id,
            tenant_id=review.tenant_id if review else None,
            event_data={
                "decision": decision,
                "user_id": str(review_item.user_id),
                "user_role_id": str(review_item.user_role_id),
                "has_justification": bool(justification)
            }
        )

        return True

    def get_access_reviews(
        self,
        tenant_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None
    ) -> List[AccessReview]:
        """Get access reviews for a tenant."""
        query = self.db.query(AccessReview)

        if tenant_id is not None:
            query = query.filter(AccessReview.tenant_id == tenant_id)

        if status:
            query = query.filter(AccessReview.status == status)

        return query.order_by(AccessReview.created_at.desc()).all()

    def get_review_items(
        self,
        review_id: uuid.UUID,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get items for a specific review."""
        query = self.db.query(AccessReviewItem, User, Role).join(
            User, AccessReviewItem.user_id == User.id
        ).join(
            UserRole, AccessReviewItem.user_role_id == UserRole.id
        ).join(
            Role, UserRole.role_id == Role.id
        ).filter(
            AccessReviewItem.review_id == review_id
        )

        if status:
            query = query.filter(AccessReviewItem.status == status)

        results = []
        for item, user, role in query.all():
            results.append({
                "id": str(item.id),
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                },
                "role": {
                    "id": str(role.id),
                    "name": role.name,
                    "display_name": role.display_name
                },
                "status": item.status,
                "decision": item.decision,
                "risk_level": item.risk_level,
                "review_notes": item.review_notes,
                "justification": item.justification,
                "reviewed_at": item.reviewed_at,
                "reviewer_id": str(item.reviewer_id) if item.reviewer_id else None
            })

        return results

    # Audit Logging

    def _log_audit_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: uuid.UUID,
        actor_id: uuid.UUID,
        tenant_id: Optional[uuid.UUID] = None,
        event_data: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Create an immutable audit log entry."""
        audit_log = AuditLog(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            tenant_id=tenant_id,
            event_data=event_data or {},
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            compliance_tags=["rbac", "access_control"]
        )

        self.db.add(audit_log)
        # Note: commit is handled by the calling method

    def get_audit_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[uuid.UUID] = None,
        actor_id: Optional[uuid.UUID] = None,
        tenant_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """Query audit logs with various filters."""
        query = self.db.query(AuditLog)

        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)

        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)

        if actor_id:
            query = query.filter(AuditLog.actor_id == actor_id)

        if tenant_id is not None:
            query = query.filter(AuditLog.tenant_id == tenant_id)

        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)

        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)

        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

    # Utility Methods

    def check_permission(
        self,
        user_id: uuid.UUID,
        permission_name: str,
        tenant_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Check if a user has a specific permission."""
        user_permissions = self.get_user_permissions(user_id, tenant_id)
        return permission_name in user_permissions

    def get_users_with_role(
        self,
        role_id: uuid.UUID,
        tenant_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get all users with a specific role."""
        query = self.db.query(User, UserRole).join(
            UserRole, User.id == UserRole.user_id
        ).filter(
            UserRole.role_id == role_id,
            UserRole.is_active == True
        )

        if tenant_id is not None:
            query = query.filter(UserRole.tenant_id == tenant_id)

        results = []
        for user, user_role in query.all():
            results.append({
                "user_id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "assigned_at": user_role.created_at,
                "expires_at": user_role.expires_at,
                "tenant_id": str(user_role.tenant_id) if user_role.tenant_id else None
            })

        return results


def get_rbac_service(db: Session = None) -> RBACService:
    """Get RBAC service instance."""
    if db is None:
        db = next(get_db())
    return RBACService(db)
