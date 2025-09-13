from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel

Base = declarative_base()

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SLAStatus(str, Enum):
    ON_TIME = "on_time"
    AT_RISK = "at_risk"
    BREACHED = "breached"

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default=TicketStatus.OPEN.value)
    priority = Column(String(50), default=TicketPriority.MEDIUM.value)
    tenant_id = Column(String(100), nullable=False)
    created_by = Column(String(100), nullable=False)
    assigned_to = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # SLA tracking
    sla_deadline = Column(DateTime, nullable=True)
    sla_status = Column(String(50), default=SLAStatus.ON_TIME.value)
    first_response_at = Column(DateTime, nullable=True)

    # Incident linkage
    incident_id = Column(String(100), nullable=True)

    # Relationships
    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan")

class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    comment = Column(Text, nullable=False)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_internal = Column(Boolean, default=False)

    # Relationships
    ticket = relationship("Ticket", back_populates="comments")

class KnowledgeBaseArticle(Base):
    __tablename__ = "kb_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    url = Column(String(500), nullable=True)
    is_public = Column(Boolean, default=True)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    view_count = Column(Integer, default=0)

class SLAPolicy(Base):
    __tablename__ = "sla_policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    priority = Column(String(50), nullable=False)
    response_time_hours = Column(Integer, nullable=False)  # Hours for first response
    resolution_time_hours = Column(Integer, nullable=False)  # Hours for resolution
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic models for API
class TicketBase(BaseModel):
    title: str
    description: str
    priority: TicketPriority = TicketPriority.MEDIUM
    tenant_id: str
    created_by: str
    assigned_to: Optional[str] = None
    incident_id: Optional[str] = None

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_to: Optional[str] = None
    incident_id: Optional[str] = None

class TicketResponse(TicketBase):
    id: int
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    sla_deadline: Optional[datetime] = None
    sla_status: SLAStatus
    first_response_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TicketCommentBase(BaseModel):
    comment: str
    created_by: str
    is_internal: bool = False

class TicketCommentCreate(TicketCommentBase):
    pass

class TicketCommentResponse(TicketCommentBase):
    id: int
    ticket_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class KBArticleBase(BaseModel):
    title: str
    content: str
    category: str
    tags: Optional[str] = None
    url: Optional[str] = None
    is_public: bool = True
    created_by: str

class KBArticleCreate(KBArticleBase):
    pass

class KBArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    url: Optional[str] = None
    is_public: Optional[bool] = None

class KBArticleResponse(KBArticleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    view_count: int

    class Config:
        from_attributes = True

class SLAPolicyBase(BaseModel):
    name: str
    priority: TicketPriority
    response_time_hours: int
    resolution_time_hours: int
    is_active: bool = True

class SLAPolicyCreate(SLAPolicyBase):
    pass

class SLAPolicyResponse(SLAPolicyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TicketStats(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    sla_breached: int
    avg_resolution_time_hours: float
    tickets_by_priority: dict
