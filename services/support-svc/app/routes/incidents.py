from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import Ticket, TicketResponse

router = APIRouter(prefix="/incidents", tags=["incidents"])

@router.get("/{incident_id}/tickets", response_model=List[TicketResponse])
async def get_tickets_for_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Get all tickets linked to a specific incident"""

    result = await db.execute(
        select(Ticket).where(Ticket.incident_id == incident_id)
    )
    tickets = result.scalars().all()

    return tickets

@router.post("/{incident_id}/link-ticket/{ticket_id}")
async def link_ticket_to_incident(
    incident_id: str,
    ticket_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Link a ticket to an incident"""

    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.incident_id = incident_id
    await db.commit()

    return {"message": f"Ticket {ticket_id} linked to incident {incident_id}"}

@router.delete("/{incident_id}/unlink-ticket/{ticket_id}")
async def unlink_ticket_from_incident(
    incident_id: str,
    ticket_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Unlink a ticket from an incident"""

    result = await db.execute(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.incident_id == incident_id
        )
    )
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found or not linked to this incident")

    ticket.incident_id = None
    await db.commit()

    return {"message": f"Ticket {ticket_id} unlinked from incident {incident_id}"}

@router.get("/tickets/status-sync")
async def sync_ticket_statuses_with_incidents(db: AsyncSession = Depends(get_db)):
    """Sync ticket statuses with their linked incidents (placeholder for external integration)"""

    # This would typically integrate with an external incident management system
    # For now, we'll just return the tickets that have incident links

    result = await db.execute(
        select(Ticket).where(Ticket.incident_id.isnot(None))
    )
    linked_tickets = result.scalars().all()

    # In a real implementation, you would:
    # 1. Query the incident management system for incident statuses
    # 2. Update ticket statuses based on incident statuses
    # 3. Handle status mapping (e.g., incident resolved -> ticket resolved)

    return {
        "message": "Status sync completed",
        "linked_tickets_count": len(linked_tickets),
        "tickets": [{"id": t.id, "incident_id": t.incident_id, "status": t.status} for t in linked_tickets]
    }
