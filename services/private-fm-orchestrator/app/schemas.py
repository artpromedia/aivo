"""
Pydantic schemas for private brain orchestrator API.
"""
from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class PrivateBrainStatus(str, Enum):
    """Status enum for private brain instances."""
    PENDING = "PENDING"
    CLONING = "CLONING"
    READY = "READY"
    ERROR = "ERROR"
    TERMINATED = "TERMINATED"


class PrivateBrainRequestCreate(BaseModel):
    """Schema for creating a private brain request."""
    learner_id: int = Field(..., description="ID of the learner")
    request_source: Optional[str] = Field(None, description="Source of the request")
    request_id: Optional[str] = Field(None, description="External request ID")


class PrivateBrainStatusResponse(BaseModel):
    """Schema for private brain status response."""
    learner_id: int = Field(..., description="ID of the learner")
    status: PrivateBrainStatus = Field(..., description="Current status of the private brain")
    ns_uid: Optional[str] = Field(None, description="Namespace UID when ready")
    checkpoint_hash: Optional[str] = Field(None, description="Checkpoint hash when ready")
    request_count: int = Field(..., description="Number of requests for this learner")
    last_request_at: datetime = Field(..., description="Timestamp of last request")
    created_at: datetime = Field(..., description="Timestamp when instance was created")
    ready_at: Optional[datetime] = Field(None, description="Timestamp when instance became ready")
    error_message: Optional[str] = Field(None, description="Error message if status is ERROR")
    retry_count: int = Field(0, description="Number of retry attempts")

    model_config = ConfigDict(from_attributes=True)


class PrivateBrainRequestResponse(BaseModel):
    """Schema for private brain request response."""
    message: str = Field(..., description="Response message")
    learner_id: int = Field(..., description="ID of the learner")
    status: PrivateBrainStatus = Field(..., description="Current status")
    is_new_request: bool = Field(..., description="Whether this was a new request or existing")


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Current timestamp")


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str = Field(..., description="Error type")
    detail: Optional[str] = Field(None, description="Error details")
    timestamp: datetime = Field(..., description="Error timestamp")


class PrivateBrainInstanceUpdate(BaseModel):
    """Schema for updating private brain instance (internal use)."""
    status: Optional[PrivateBrainStatus] = None
    ns_uid: Optional[str] = None
    checkpoint_hash: Optional[str] = None
    error_message: Optional[str] = None
    ready_at: Optional[datetime] = None
