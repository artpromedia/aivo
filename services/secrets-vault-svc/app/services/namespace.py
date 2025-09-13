"""Namespace management service."""

from typing import Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Namespace


class NamespaceExistsError(Exception):
    """Exception raised when trying to create a namespace that already exists."""
    pass


class NamespaceService:
    """Service for managing namespaces."""

    async def create_namespace(
        self,
        db: AsyncSession,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        tenant_id: Optional[str] = None,
        parent_namespace: Optional[str] = None,
        max_secrets: Optional[int] = None,
        retention_days: Optional[int] = None,
        allowed_users: Optional[List[str]] = None,
        allowed_services: Optional[List[str]] = None,
        tags: Optional[Dict[str, str]] = None,
        created_by: Optional[str] = None,
    ) -> Namespace:
        """Create a new namespace."""
        # Check if namespace already exists
        existing = await self.get_namespace_by_name(db, name, tenant_id)
        if existing:
            raise NamespaceExistsError(f"Namespace '{name}' already exists")

        namespace = Namespace(
            name=name,
            display_name=display_name,
            description=description,
            tenant_id=tenant_id,
            parent_namespace=parent_namespace,
            is_active=True,
            max_secrets=max_secrets,
            retention_days=retention_days,
            allowed_users=allowed_users,
            allowed_services=allowed_services,
            tags=tags,
            created_by=created_by,
        )

        db.add(namespace)
        await db.commit()
        await db.refresh(namespace)
        return namespace

    async def get_namespace(self, db: AsyncSession, namespace_id: str) -> Optional[Namespace]:
        """Get a namespace by ID."""
        query = select(Namespace).where(Namespace.id == namespace_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_namespace_by_name(
        self,
        db: AsyncSession,
        name: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[Namespace]:
        """Get a namespace by name."""
        query = select(Namespace).where(Namespace.name == name)

        if tenant_id:
            query = query.where(Namespace.tenant_id == tenant_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def update_namespace(
        self,
        db: AsyncSession,
        namespace_id: str,
        update_data: Dict[str, any],
        updated_by: Optional[str] = None,
    ) -> Optional[Namespace]:
        """Update a namespace."""
        if updated_by:
            update_data["updated_by"] = updated_by

        query = (
            update(Namespace)
            .where(Namespace.id == namespace_id)
            .values(**update_data)
            .returning(Namespace)
        )

        result = await db.execute(query)
        await db.commit()
        return result.scalar_one_or_none()

    async def list_namespaces(
        self,
        db: AsyncSession,
        tenant_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Namespace]:
        """List namespaces with optional filtering."""
        query = select(Namespace)

        if tenant_id:
            query = query.where(Namespace.tenant_id == tenant_id)

        if is_active is not None:
            query = query.where(Namespace.is_active == is_active)

        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    async def delete_namespace(
        self,
        db: AsyncSession,
        namespace_id: str,
        soft_delete: bool = True,
    ) -> bool:
        """Delete a namespace (soft or hard delete)."""
        if soft_delete:
            query = (
                update(Namespace)
                .where(Namespace.id == namespace_id)
                .values(is_active=False)
            )
            await db.execute(query)
        else:
            # Hard delete would be implemented here
            pass

        await db.commit()
        return True

    async def get_namespace_stats(
        self,
        db: AsyncSession,
        namespace_id: str,
    ) -> Dict[str, any]:
        """Get statistics for a namespace."""
        # This would include secret counts, access logs, etc.
        # For now, return empty stats
        return {
            "total_secrets": 0,
            "active_secrets": 0,
            "expired_secrets": 0,
            "total_accesses": 0,
        }
