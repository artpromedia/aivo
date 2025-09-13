from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import (
    Ticket, TicketComment, SLAPolicy,
    TicketCreate, TicketUpdate, TicketResponse, TicketCommentCreate, TicketCommentResponse,
    TicketStatus, TicketPriority, SLAStatus, TicketStats
)

router = APIRouter(prefix="/tickets", tags=["tickets"])

async def calculate_sla_deadline(priority: TicketPriority, db: AsyncSession) -> Optional[datetime]:
    """Calculate SLA deadline based on priority"""
    result = await db.execute(
        select(SLAPolicy).where(
            and_(SLAPolicy.priority == priority.value, SLAPolicy.is_active == True)
        )
    )
    sla_policy = result.scalar_one_or_none()

    if sla_policy:
        return datetime.utcnow() + timedelta(hours=sla_policy.resolution_time_hours)
    return None

async def update_sla_status(ticket: Ticket) -> None:
    """Update SLA status based on current time and deadline"""
    if not ticket.sla_deadline:
        return

    now = datetime.utcnow()
    time_to_deadline = ticket.sla_deadline - now

    if time_to_deadline.total_seconds() < 0:
        ticket.sla_status = SLAStatus.BREACHED.value
    elif time_to_deadline.total_seconds() < 7200:  # 2 hours warning
        ticket.sla_status = SLAStatus.AT_RISK.value
    else:
        ticket.sla_status = SLAStatus.ON_TIME.value

@router.get("/", response_model=List[TicketResponse])
async def get_tickets(
    tenant_id: Optional[str] = Query(None),
    status: Optional[TicketStatus] = Query(None),
    priority: Optional[TicketPriority] = Query(None),
    assigned_to: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get tickets with filtering options"""

    query = select(Ticket).options(selectinload(Ticket.comments))

    if tenant_id:
        query = query.where(Ticket.tenant_id == tenant_id)
    if status:
        query = query.where(Ticket.status == status.value)
    if priority:
        query = query.where(Ticket.priority == priority.value)
    if assigned_to:
        query = query.where(Ticket.assigned_to == assigned_to)

    query = query.offset(offset).limit(limit).order_by(Ticket.created_at.desc())

    result = await db.execute(query)
    tickets = result.scalars().all()

    # Update SLA status for each ticket
    for ticket in tickets:
        await update_sla_status(ticket)

    await db.commit()

    return tickets

@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific ticket by ID"""

    result = await db.execute(
        select(Ticket).options(selectinload(Ticket.comments)).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Update SLA status
    await update_sla_status(ticket)
    await db.commit()

    return ticket

@router.post("/", response_model=TicketResponse)
async def create_ticket(ticket_data: TicketCreate, db: AsyncSession = Depends(get_db)):
    """Create a new support ticket"""

    # Calculate SLA deadline
    sla_deadline = await calculate_sla_deadline(ticket_data.priority, db)

    ticket = Ticket(
        title=ticket_data.title,
        description=ticket_data.description,
        priority=ticket_data.priority.value,
        tenant_id=ticket_data.tenant_id,
        created_by=ticket_data.created_by,
        assigned_to=ticket_data.assigned_to,
        incident_id=ticket_data.incident_id,
        sla_deadline=sla_deadline,
        sla_status=SLAStatus.ON_TIME.value
    )

    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)

    return ticket

@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a ticket"""

    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Update fields
    if ticket_data.title is not None:
        ticket.title = ticket_data.title
    if ticket_data.description is not None:
        ticket.description = ticket_data.description
    if ticket_data.status is not None:
        old_status = ticket.status
        ticket.status = ticket_data.status.value

        # Track resolution time
        if ticket_data.status == TicketStatus.RESOLVED and old_status != TicketStatus.RESOLVED.value:
            ticket.resolved_at = datetime.utcnow()

    if ticket_data.priority is not None:
        ticket.priority = ticket_data.priority.value
        # Recalculate SLA deadline if priority changed
        ticket.sla_deadline = await calculate_sla_deadline(ticket_data.priority, db)

    if ticket_data.assigned_to is not None:
        ticket.assigned_to = ticket_data.assigned_to
    if ticket_data.incident_id is not None:
        ticket.incident_id = ticket_data.incident_id

    ticket.updated_at = datetime.utcnow()

    # Update SLA status
    await update_sla_status(ticket)

    await db.commit()
    await db.refresh(ticket)

    return ticket

@router.delete("/{ticket_id}")
async def delete_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a ticket"""

    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    await db.delete(ticket)
    await db.commit()

    return {"message": "Ticket deleted successfully"}

@router.post("/{ticket_id}/comment", response_model=TicketCommentResponse)
async def add_ticket_comment(
    ticket_id: int,
    comment_data: TicketCommentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a comment to a ticket"""

    # Verify ticket exists
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Track first response time
    if not ticket.first_response_at and not comment_data.is_internal:
        ticket.first_response_at = datetime.utcnow()

    comment = TicketComment(
        ticket_id=ticket_id,
        comment=comment_data.comment,
        created_by=comment_data.created_by,
        is_internal=comment_data.is_internal
    )

    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return comment

@router.get("/{ticket_id}/comments", response_model=List[TicketCommentResponse])
async def get_ticket_comments(ticket_id: int, db: AsyncSession = Depends(get_db)):
    """Get all comments for a ticket"""

    result = await db.execute(
        select(TicketComment)
        .where(TicketComment.ticket_id == ticket_id)
        .order_by(TicketComment.created_at.asc())
    )
    comments = result.scalars().all()

    return comments

@router.get("/stats/overview", response_model=TicketStats)
async def get_ticket_stats(
    tenant_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get ticket statistics"""

    # Base query
    base_query = select(Ticket)
    if tenant_id:
        base_query = base_query.where(Ticket.tenant_id == tenant_id)

    # Total tickets
    total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total_tickets = total_result.scalar()

    # Open tickets
    open_result = await db.execute(
        select(func.count()).select_from(
            base_query.where(Ticket.status == TicketStatus.OPEN.value).subquery()
        )
    )
    open_tickets = open_result.scalar()

    # In progress tickets
    progress_result = await db.execute(
        select(func.count()).select_from(
            base_query.where(Ticket.status == TicketStatus.IN_PROGRESS.value).subquery()
        )
    )
    in_progress_tickets = progress_result.scalar()

    # Resolved tickets
    resolved_result = await db.execute(
        select(func.count()).select_from(
            base_query.where(Ticket.status == TicketStatus.RESOLVED.value).subquery()
        )
    )
    resolved_tickets = resolved_result.scalar()

    # SLA breached
    breached_result = await db.execute(
        select(func.count()).select_from(
            base_query.where(Ticket.sla_status == SLAStatus.BREACHED.value).subquery()
        )
    )
    sla_breached = breached_result.scalar()

    # Average resolution time
    avg_result = await db.execute(
        select(func.avg(func.julianday(Ticket.resolved_at) - func.julianday(Ticket.created_at)) * 24)
        .select_from(
            base_query.where(Ticket.resolved_at.isnot(None)).subquery()
        )
    )
    avg_resolution_time = avg_result.scalar() or 0.0

    # Tickets by priority
    priority_result = await db.execute(
        select(Ticket.priority, func.count())
        .select_from(base_query.subquery())
        .group_by(Ticket.priority)
    )
    tickets_by_priority = dict(priority_result.all())

    return TicketStats(
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        in_progress_tickets=in_progress_tickets,
        resolved_tickets=resolved_tickets,
        sla_breached=sla_breached,
        avg_resolution_time_hours=avg_resolution_time,
        tickets_by_priority=tickets_by_priority
    )
