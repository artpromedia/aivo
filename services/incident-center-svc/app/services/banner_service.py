"""
Banner Management Service
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Banner, BannerDismissal, BannerType

logger = structlog.get_logger(__name__)


class BannerService:
    """Service for managing admin banners."""

    async def create_banner(
        self,
        db: AsyncSession,
        title: str,
        message: str,
        banner_type: BannerType = BannerType.INFO,
        is_dismissible: bool = True,
        show_in_admin: bool = True,
        show_in_tenant: bool = False,
        target_tenants: Optional[List[str]] = None,
        target_roles: Optional[List[str]] = None,
        duration_minutes: Optional[int] = None,
        priority: int = 0,
        created_by: str = "system",
        incident_id: Optional[uuid.UUID] = None,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None
    ) -> Banner:
        """Create a new banner."""

        start_time = datetime.utcnow()
        end_time = None

        if duration_minutes:
            end_time = start_time + timedelta(minutes=duration_minutes)
        elif duration_minutes is None and banner_type != BannerType.INFO:
            # Default duration for non-info banners
            end_time = start_time + timedelta(
                minutes=settings.BANNER_DEFAULT_DURATION_MINUTES
            )

        banner = Banner(
            title=title,
            message=message,
            banner_type=banner_type,
            is_dismissible=is_dismissible,
            show_in_admin=show_in_admin,
            show_in_tenant=show_in_tenant,
            target_tenants=target_tenants,
            target_roles=target_roles,
            start_time=start_time,
            end_time=end_time,
            priority=priority,
            created_by=created_by,
            incident_id=incident_id,
            action_url=action_url,
            action_text=action_text
        )

        db.add(banner)
        await db.commit()
        await db.refresh(banner)

        logger.info(
            "Banner created",
            banner_id=str(banner.id),
            title=banner.title,
            banner_type=banner.banner_type.value
        )

        return banner

    async def get_banner(
        self,
        db: AsyncSession,
        banner_id: uuid.UUID
    ) -> Optional[Banner]:
        """Get banner by ID."""

        result = await db.execute(
            select(Banner).where(Banner.id == banner_id)
        )
        return result.scalar_one_or_none()

    async def list_banners(
        self,
        db: AsyncSession,
        active_only: bool = False,
        banner_type: Optional[BannerType] = None,
        show_in_admin: Optional[bool] = None,
        show_in_tenant: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """List banners with filtering."""

        query = select(Banner)
        filters = []

        # Apply filters
        if active_only:
            now = datetime.utcnow()
            filters.append(Banner.is_active == True)
            filters.append(Banner.start_time <= now)
            filters.append(
                or_(
                    Banner.end_time.is_(None),
                    Banner.end_time > now
                )
            )

        if banner_type:
            filters.append(Banner.banner_type == banner_type)

        if show_in_admin is not None:
            filters.append(Banner.show_in_admin == show_in_admin)

        if show_in_tenant is not None:
            filters.append(Banner.show_in_tenant == show_in_tenant)

        if filters:
            query = query.where(and_(*filters))

        # Order by priority desc, then created_at desc
        query = query.order_by(desc(Banner.priority), desc(Banner.created_at))

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        banners = result.scalars().all()

        # Get total count
        count_query = select(Banner.id)
        if filters:
            count_query = count_query.where(and_(*filters))

        count_result = await db.execute(count_query)
        total_count = len(count_result.scalars().all())

        return {
            "banners": banners,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_count,
                "pages": (total_count + page_size - 1) // page_size
            }
        }

    async def get_active_banners_for_user(
        self,
        db: AsyncSession,
        user_id: str,
        tenant_id: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        show_in_admin: bool = True,
        show_in_tenant: bool = False
    ) -> List[Banner]:
        """Get active banners for a specific user."""

        now = datetime.utcnow()

        # Base query for active banners
        query = select(Banner).where(
            and_(
                Banner.is_active == True,
                Banner.start_time <= now,
                or_(
                    Banner.end_time.is_(None),
                    Banner.end_time > now
                )
            )
        )

        # Apply context filters
        context_filters = []

        if show_in_admin:
            context_filters.append(Banner.show_in_admin == True)

        if show_in_tenant:
            context_filters.append(Banner.show_in_tenant == True)

        if context_filters:
            query = query.where(or_(*context_filters))

        result = await db.execute(query)
        all_banners = result.scalars().all()

        # Filter banners based on targeting and dismissals
        filtered_banners = []

        for banner in all_banners:
            # Check tenant targeting
            if banner.target_tenants and tenant_id:
                if tenant_id not in banner.target_tenants:
                    continue

            # Check role targeting
            if banner.target_roles and user_roles:
                if not any(role in banner.target_roles for role in user_roles):
                    continue

            # Check if user dismissed this banner
            if banner.is_dismissible:
                dismissal_result = await db.execute(
                    select(BannerDismissal).where(
                        and_(
                            BannerDismissal.banner_id == banner.id,
                            BannerDismissal.user_id == user_id
                        )
                    )
                )

                if dismissal_result.scalar_one_or_none():
                    continue  # User dismissed this banner

            filtered_banners.append(banner)

        # Sort by priority and creation time
        filtered_banners.sort(
            key=lambda b: (-b.priority, -b.created_at.timestamp())
        )

        return filtered_banners

    async def dismiss_banner(
        self,
        db: AsyncSession,
        banner_id: uuid.UUID,
        user_id: str,
        tenant_id: Optional[str] = None
    ) -> bool:
        """Dismiss a banner for a user."""

        # Check if banner exists and is dismissible
        banner = await self.get_banner(db, banner_id)
        if not banner or not banner.is_dismissible:
            return False

        # Check if already dismissed
        existing_dismissal = await db.execute(
            select(BannerDismissal).where(
                and_(
                    BannerDismissal.banner_id == banner_id,
                    BannerDismissal.user_id == user_id
                )
            )
        )

        if existing_dismissal.scalar_one_or_none():
            return True  # Already dismissed

        # Create dismissal record
        dismissal = BannerDismissal(
            banner_id=banner_id,
            user_id=user_id,
            tenant_id=tenant_id
        )

        db.add(dismissal)
        await db.commit()

        logger.info(
            "Banner dismissed",
            banner_id=str(banner_id),
            user_id=user_id
        )

        return True

    async def update_banner(
        self,
        db: AsyncSession,
        banner_id: uuid.UUID,
        title: Optional[str] = None,
        message: Optional[str] = None,
        banner_type: Optional[BannerType] = None,
        is_active: Optional[bool] = None,
        is_dismissible: Optional[bool] = None,
        show_in_admin: Optional[bool] = None,
        show_in_tenant: Optional[bool] = None,
        target_tenants: Optional[List[str]] = None,
        target_roles: Optional[List[str]] = None,
        end_time: Optional[datetime] = None,
        priority: Optional[int] = None,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None
    ) -> Optional[Banner]:
        """Update an existing banner."""

        banner = await self.get_banner(db, banner_id)
        if not banner:
            return None

        # Update fields if provided
        if title is not None:
            banner.title = title
        if message is not None:
            banner.message = message
        if banner_type is not None:
            banner.banner_type = banner_type
        if is_active is not None:
            banner.is_active = is_active
        if is_dismissible is not None:
            banner.is_dismissible = is_dismissible
        if show_in_admin is not None:
            banner.show_in_admin = show_in_admin
        if show_in_tenant is not None:
            banner.show_in_tenant = show_in_tenant
        if target_tenants is not None:
            banner.target_tenants = target_tenants
        if target_roles is not None:
            banner.target_roles = target_roles
        if end_time is not None:
            banner.end_time = end_time
        if priority is not None:
            banner.priority = priority
        if action_url is not None:
            banner.action_url = action_url
        if action_text is not None:
            banner.action_text = action_text

        await db.commit()
        await db.refresh(banner)

        logger.info("Banner updated", banner_id=str(banner_id))

        return banner

    async def deactivate_banner(
        self,
        db: AsyncSession,
        banner_id: uuid.UUID
    ) -> bool:
        """Deactivate a banner."""

        banner = await self.get_banner(db, banner_id)
        if not banner:
            return False

        banner.is_active = False
        banner.end_time = datetime.utcnow()

        await db.commit()

        logger.info("Banner deactivated", banner_id=str(banner_id))

        return True

    async def cleanup_expired_banners(self, db: AsyncSession) -> int:
        """Deactivate expired banners."""

        now = datetime.utcnow()

        # Find expired banners
        result = await db.execute(
            select(Banner).where(
                and_(
                    Banner.is_active == True,
                    Banner.end_time <= now
                )
            )
        )

        expired_banners = result.scalars().all()

        # Deactivate them
        for banner in expired_banners:
            banner.is_active = False

        if expired_banners:
            await db.commit()
            logger.info("Cleaned up expired banners", count=len(expired_banners))

        return len(expired_banners)

    async def create_incident_banner(
        self,
        db: AsyncSession,
        incident_id: uuid.UUID,
        incident_title: str,
        incident_severity: str,
        created_by: str = "system"
    ) -> Banner:
        """Create a banner for an incident."""

        # Determine banner type based on severity
        banner_type_map = {
            "low": BannerType.INFO,
            "medium": BannerType.WARNING,
            "high": BannerType.ERROR,
            "critical": BannerType.ERROR
        }

        banner_type = banner_type_map.get(incident_severity, BannerType.WARNING)

        # Create banner
        banner = await self.create_banner(
            db=db,
            title=f"Service Incident: {incident_title}",
            message=f"We are currently investigating an issue. Updates will be posted here.",
            banner_type=banner_type,
            is_dismissible=True,
            show_in_admin=True,
            show_in_tenant=True,
            priority=10 if incident_severity == "critical" else 5,
            created_by=created_by,
            incident_id=incident_id,
            action_url="/admin/operations/incidents",
            action_text="View Details"
        )

        return banner
