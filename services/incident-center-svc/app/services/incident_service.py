"""
Incident Management Service
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
import structlog
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models import (
    Incident, IncidentSeverity, IncidentStatus, IncidentUpdate
)

logger = structlog.get_logger(__name__)


class IncidentService:
    """Service for managing incidents."""

    def __init__(self):
        self.statuspage_client = None
        if settings.STATUSPAGE_API_KEY and settings.STATUSPAGE_PAGE_ID:
            self.statuspage_client = httpx.AsyncClient(
                base_url=settings.STATUSPAGE_BASE_URL,
                headers={
                    "Authorization": f"OAuth {settings.STATUSPAGE_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )

    async def create_incident(
        self,
        db: AsyncSession,
        title: str,
        description: Optional[str] = None,
        severity: IncidentSeverity = IncidentSeverity.MEDIUM,
        affected_services: Optional[List[str]] = None,
        impact_description: Optional[str] = None,
        created_by: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
        sync_to_statuspage: bool = False
    ) -> Incident:
        """Create a new incident."""

        incident = Incident(
            title=title,
            description=description,
            severity=severity,
            status=IncidentStatus.INVESTIGATING,
            affected_services=affected_services or [],
            impact_description=impact_description,
            created_by=created_by,
            metadata=metadata or {},
            started_at=datetime.utcnow()
        )

        # Sync to statuspage if enabled
        if sync_to_statuspage and self.statuspage_client:
            try:
                statuspage_incident = await self._create_statuspage_incident(incident)
                if statuspage_incident:
                    incident.statuspage_id = statuspage_incident.get("id")
                    incident.external_id = statuspage_incident.get("shortlink")
            except Exception as e:
                logger.error("Failed to sync incident to statuspage", error=str(e))

        db.add(incident)
        await db.commit()
        await db.refresh(incident)

        logger.info(
            "Incident created",
            incident_id=str(incident.id),
            title=incident.title,
            severity=incident.severity.value
        )

        return incident

    async def get_incident(
        self,
        db: AsyncSession,
        incident_id: uuid.UUID,
        include_updates: bool = True
    ) -> Optional[Incident]:
        """Get incident by ID."""

        query = select(Incident).where(Incident.id == incident_id)

        if include_updates:
            query = query.options(selectinload(Incident.updates))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def list_incidents(
        self,
        db: AsyncSession,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        affected_service: Optional[str] = None,
        created_by: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_resolved: bool = True,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """List incidents with filtering."""

        query = select(Incident).options(selectinload(Incident.updates))

        # Apply filters
        filters = []

        if status:
            filters.append(Incident.status == status)

        if severity:
            filters.append(Incident.severity == severity)

        if affected_service:
            filters.append(Incident.affected_services.contains([affected_service]))

        if created_by:
            filters.append(Incident.created_by == created_by)

        if start_date:
            filters.append(Incident.started_at >= start_date)

        if end_date:
            filters.append(Incident.started_at <= end_date)

        if not include_resolved:
            filters.append(Incident.status != IncidentStatus.RESOLVED)

        if filters:
            query = query.where(and_(*filters))

        # Order by started_at desc
        query = query.order_by(desc(Incident.started_at))

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        incidents = result.scalars().all()

        # Get total count for pagination
        count_query = select(Incident.id)
        if filters:
            count_query = count_query.where(and_(*filters))

        count_result = await db.execute(count_query)
        total_count = len(count_result.scalars().all())

        return {
            "incidents": incidents,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_count,
                "pages": (total_count + page_size - 1) // page_size
            }
        }

    async def update_incident_status(
        self,
        db: AsyncSession,
        incident_id: uuid.UUID,
        new_status: IncidentStatus,
        update_title: str,
        update_message: str,
        created_by: str,
        is_public: bool = True,
        sync_to_statuspage: bool = False
    ) -> Optional[IncidentUpdate]:
        """Update incident status with a new update."""

        # Get the incident
        incident = await self.get_incident(db, incident_id, include_updates=False)
        if not incident:
            return None

        # Create the update
        update = IncidentUpdate(
            incident_id=incident_id,
            title=update_title,
            message=update_message,
            new_status=new_status,
            created_by=created_by,
            is_public=is_public
        )

        # Update incident status
        incident.status = new_status

        # Set resolved timestamp if resolving
        if new_status == IncidentStatus.RESOLVED and not incident.resolved_at:
            incident.resolved_at = datetime.utcnow()

        # Sync to statuspage if enabled
        if sync_to_statuspage and self.statuspage_client and incident.statuspage_id:
            try:
                statuspage_update = await self._create_statuspage_update(
                    incident.statuspage_id, update
                )
                if statuspage_update:
                    update.statuspage_update_id = statuspage_update.get("id")
            except Exception as e:
                logger.error(
                    "Failed to sync update to statuspage",
                    incident_id=str(incident_id),
                    error=str(e)
                )

        db.add(update)
        await db.commit()
        await db.refresh(update)

        logger.info(
            "Incident status updated",
            incident_id=str(incident_id),
            new_status=new_status.value,
            update_id=str(update.id)
        )

        return update

    async def get_active_incidents(
        self,
        db: AsyncSession,
        severity_filter: Optional[IncidentSeverity] = None
    ) -> List[Incident]:
        """Get all active (non-resolved) incidents."""

        query = select(Incident).where(
            Incident.status != IncidentStatus.RESOLVED
        ).options(selectinload(Incident.updates))

        if severity_filter:
            query = query.where(Incident.severity == severity_filter)

        query = query.order_by(desc(Incident.severity), desc(Incident.started_at))

        result = await db.execute(query)
        return list(result.scalars().all())

    async def auto_resolve_old_incidents(self, db: AsyncSession) -> int:
        """Auto-resolve incidents that have been open too long."""

        cutoff_time = datetime.utcnow() - timedelta(
            hours=settings.INCIDENT_AUTO_RESOLVE_HOURS
        )

        query = select(Incident).where(
            and_(
                Incident.status.in_([
                    IncidentStatus.INVESTIGATING,
                    IncidentStatus.IDENTIFIED,
                    IncidentStatus.MONITORING
                ]),
                Incident.started_at < cutoff_time
            )
        )

        result = await db.execute(query)
        old_incidents = result.scalars().all()

        resolved_count = 0
        for incident in old_incidents:
            try:
                await self.update_incident_status(
                    db=db,
                    incident_id=incident.id,
                    new_status=IncidentStatus.RESOLVED,
                    update_title="Auto-resolved",
                    update_message="This incident was automatically resolved due to age.",
                    created_by="system",
                    is_public=True
                )
                resolved_count += 1
            except Exception as e:
                logger.error(
                    "Failed to auto-resolve incident",
                    incident_id=str(incident.id),
                    error=str(e)
                )

        logger.info("Auto-resolved old incidents", count=resolved_count)
        return resolved_count

    async def sync_from_statuspage(self, db: AsyncSession) -> int:
        """Sync incidents from statuspage."""

        if not self.statuspage_client:
            return 0

        try:
            response = await self.statuspage_client.get(
                f"/pages/{settings.STATUSPAGE_PAGE_ID}/incidents"
            )
            response.raise_for_status()

            statuspage_incidents = response.json()
            synced_count = 0

            for sp_incident in statuspage_incidents:
                # Check if we already have this incident
                existing = await db.execute(
                    select(Incident).where(
                        Incident.statuspage_id == sp_incident["id"]
                    )
                )

                if existing.scalar_one_or_none():
                    continue  # Already exists

                # Create new incident from statuspage data
                severity = self._map_statuspage_impact_to_severity(
                    sp_incident.get("impact", "minor")
                )

                status = self._map_statuspage_status_to_status(
                    sp_incident.get("status", "investigating")
                )

                incident = Incident(
                    title=sp_incident["name"],
                    description=sp_incident.get("incident_updates", [{}])[0].get("body"),
                    status=status,
                    severity=severity,
                    statuspage_id=sp_incident["id"],
                    external_id=sp_incident.get("shortlink"),
                    started_at=datetime.fromisoformat(
                        sp_incident["created_at"].replace("Z", "+00:00")
                    ),
                    created_by="statuspage_sync"
                )

                if sp_incident.get("resolved_at"):
                    incident.resolved_at = datetime.fromisoformat(
                        sp_incident["resolved_at"].replace("Z", "+00:00")
                    )

                db.add(incident)
                synced_count += 1

            if synced_count > 0:
                await db.commit()
                logger.info("Synced incidents from statuspage", count=synced_count)

            return synced_count

        except Exception as e:
            logger.error("Failed to sync from statuspage", error=str(e))
            return 0

    async def _create_statuspage_incident(self, incident: Incident) -> Optional[Dict[str, Any]]:
        """Create incident on statuspage."""

        if not self.statuspage_client:
            return None

        try:
            data = {
                "incident": {
                    "name": incident.title,
                    "status": self._map_status_to_statuspage(incident.status),
                    "impact_override": self._map_severity_to_statuspage_impact(incident.severity),
                    "body": incident.description or incident.title
                }
            }

            response = await self.statuspage_client.post(
                f"/pages/{settings.STATUSPAGE_PAGE_ID}/incidents",
                json=data
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error("Failed to create statuspage incident", error=str(e))
            return None

    async def _create_statuspage_update(
        self,
        statuspage_incident_id: str,
        update: IncidentUpdate
    ) -> Optional[Dict[str, Any]]:
        """Create incident update on statuspage."""

        if not self.statuspage_client:
            return None

        try:
            data = {
                "incident_update": {
                    "body": update.message,
                    "status": self._map_status_to_statuspage(update.new_status),
                    "wants_twitter_update": False
                }
            }

            response = await self.statuspage_client.post(
                f"/pages/{settings.STATUSPAGE_PAGE_ID}/incidents/{statuspage_incident_id}/incident_updates",
                json=data
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error("Failed to create statuspage update", error=str(e))
            return None

    def _map_severity_to_statuspage_impact(self, severity: IncidentSeverity) -> str:
        """Map our severity to statuspage impact."""
        mapping = {
            IncidentSeverity.LOW: "minor",
            IncidentSeverity.MEDIUM: "major",
            IncidentSeverity.HIGH: "major",
            IncidentSeverity.CRITICAL: "critical"
        }
        return mapping.get(severity, "minor")

    def _map_status_to_statuspage(self, status: IncidentStatus) -> str:
        """Map our status to statuspage status."""
        mapping = {
            IncidentStatus.INVESTIGATING: "investigating",
            IncidentStatus.IDENTIFIED: "identified",
            IncidentStatus.MONITORING: "monitoring",
            IncidentStatus.RESOLVED: "resolved",
            IncidentStatus.POSTMORTEM: "postmortem"
        }
        return mapping.get(status, "investigating")

    def _map_statuspage_impact_to_severity(self, impact: str) -> IncidentSeverity:
        """Map statuspage impact to our severity."""
        mapping = {
            "none": IncidentSeverity.LOW,
            "minor": IncidentSeverity.LOW,
            "major": IncidentSeverity.HIGH,
            "critical": IncidentSeverity.CRITICAL
        }
        return mapping.get(impact, IncidentSeverity.MEDIUM)

    def _map_statuspage_status_to_status(self, status: str) -> IncidentStatus:
        """Map statuspage status to our status."""
        mapping = {
            "investigating": IncidentStatus.INVESTIGATING,
            "identified": IncidentStatus.IDENTIFIED,
            "monitoring": IncidentStatus.MONITORING,
            "resolved": IncidentStatus.RESOLVED,
            "postmortem": IncidentStatus.POSTMORTEM
        }
        return mapping.get(status, IncidentStatus.INVESTIGATING)
