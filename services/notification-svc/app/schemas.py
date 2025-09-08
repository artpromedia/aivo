"""
Pydantic schemas for the Notification Service API.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class TemplateId(str, Enum):
    """Available email templates."""

    TEACHER_INVITE = "teacher_invite"
    APPROVAL_REQUEST = "approval_request"
    ENROLLMENT_DECISION = "enrollment_decision"


class NotificationRequest(BaseModel):
    """Request schema for sending notifications."""

    to: EmailStr = Field(..., description="Recipient email address")
    template_id: TemplateId = Field(..., description="Template identifier")
    data: dict[str, Any] = Field(
        default_factory=dict, description="Template data"
    )

    # Optional overrides
    subject: str | None = Field(None, description="Override subject line")
    from_email: EmailStr | None = Field(
        None, description="Override from email"
    )
    from_name: str | None = Field(None, description="Override from name")

    # Metadata
    tenant_id: str | None = Field(None, description="Tenant identifier")
    user_id: str | None = Field(None, description="User identifier")
    reference_id: str | None = Field(None, description="Reference identifier")


class BulkNotificationRequest(BaseModel):
    """Request schema for sending bulk notifications."""

    to: list[EmailStr] = Field(
        ..., description="List of recipient email addresses"
    )
    template_id: TemplateId = Field(..., description="Template identifier")
    data: dict[str, Any] = Field(
        default_factory=dict, description="Template data"
    )

    # Optional overrides
    subject: str | None = Field(None, description="Override subject line")
    from_email: EmailStr | None = Field(
        None, description="Override from email"
    )
    from_name: str | None = Field(None, description="Override from name")

    # Metadata
    tenant_id: str | None = Field(None, description="Tenant identifier")


class NotificationResponse(BaseModel):
    """Response schema for notification requests."""

    success: bool = Field(
        ..., description="Whether the notification was sent successfully"
    )
    message_id: str | None = Field(None, description="Message identifier")
    error: str | None = Field(None, description="Error message if failed")


class BulkNotificationResponse(BaseModel):
    """Response schema for bulk notification requests."""

    total_sent: int = Field(..., description="Total number of emails sent")
    successful: list[str] = Field(
        ..., description="Successfully sent email addresses"
    )
    failed: list[dict[str, str]] = Field(
        ..., description="Failed email addresses with errors"
    )


class TemplateInfo(BaseModel):
    """Information about an email template."""

    id: TemplateId = Field(..., description="Template identifier")
    name: str = Field(..., description="Template display name")
    description: str = Field(..., description="Template description")
    required_data: list[str] = Field(..., description="Required data fields")
    optional_data: list[str] = Field(
        default_factory=list, description="Optional data fields"
    )


class TemplateListResponse(BaseModel):
    """Response schema for template listing."""

    templates: list[TemplateInfo] = Field(
        ..., description="Available templates"
    )


class RenderTemplateRequest(BaseModel):
    """Request schema for template rendering (dev/testing)."""

    template_id: TemplateId = Field(..., description="Template identifier")
    data: dict[str, Any] = Field(
        default_factory=dict, description="Template data"
    )


class RenderTemplateResponse(BaseModel):
    """Response schema for template rendering."""

    html: str = Field(..., description="Rendered HTML content")
    subject: str = Field(..., description="Rendered subject line")
    template_id: TemplateId = Field(..., description="Template identifier")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    smtp_configured: bool = Field(
        ..., description="Whether SMTP is configured"
    )
    templates_loaded: int = Field(
        ..., description="Number of templates loaded"
    )
