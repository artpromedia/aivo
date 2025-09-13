"""Pydantic schemas for the reports service."""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from uuid import UUID
import uuid

# Base schemas
class ReportBase(BaseModel):
    name: str = Field(..., description="Report name")
    description: Optional[str] = Field(None, description="Report description")
    query_config: Dict[str, Any] = Field(..., description="Query DSL configuration")
    visualization_config: Optional[Dict[str, Any]] = Field(None, description="Chart/table config")
    filters: Optional[Dict[str, Any]] = Field(None, description="Default filters")
    row_limit: int = Field(10000, description="Maximum rows per export")
    is_public: bool = Field(False, description="Whether report is public")
    tags: Optional[List[str]] = Field(None, description="Report tags")

class ReportCreate(ReportBase):
    tenant_id: str = Field(..., description="Tenant ID")
    created_by: str = Field(..., description="User who created the report")

class ReportUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    query_config: Optional[Dict[str, Any]] = None
    visualization_config: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    row_limit: Optional[int] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None

class Report(ReportBase):
    id: UUID
    tenant_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schedule schemas
class ScheduleBase(BaseModel):
    name: str = Field(..., description="Schedule name")
    description: Optional[str] = Field(None, description="Schedule description")
    cron_expression: str = Field(..., description="Cron expression for scheduling")
    timezone: str = Field("UTC", description="Timezone for scheduling")
    format: Literal["csv", "pdf", "xlsx"] = Field(..., description="Export format")
    delivery_method: Literal["email", "s3", "both"] = Field(..., description="Delivery method")
    recipients: Optional[List[EmailStr]] = Field(None, description="Email recipients")
    s3_config: Optional[Dict[str, Any]] = Field(None, description="S3 configuration")
    email_config: Optional[Dict[str, Any]] = Field(None, description="Email configuration")
    is_active: bool = Field(True, description="Whether schedule is active")

class ScheduleCreate(ScheduleBase):
    report_id: UUID = Field(..., description="Report ID to schedule")
    tenant_id: str = Field(..., description="Tenant ID")
    created_by: str = Field(..., description="User who created the schedule")

class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    format: Optional[Literal["csv", "pdf", "xlsx"]] = None
    delivery_method: Optional[Literal["email", "s3", "both"]] = None
    recipients: Optional[List[EmailStr]] = None
    s3_config: Optional[Dict[str, Any]] = None
    email_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class Schedule(ScheduleBase):
    id: UUID
    report_id: UUID
    tenant_id: str
    created_by: str
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Export schemas
class ExportBase(BaseModel):
    format: Literal["csv", "pdf", "xlsx"] = Field(..., description="Export format")

class ExportCreate(ExportBase):
    report_id: UUID = Field(..., description="Report ID to export")
    schedule_id: Optional[UUID] = Field(None, description="Schedule ID if scheduled export")
    tenant_id: str = Field(..., description="Tenant ID")
    initiated_by: str = Field(..., description="User who initiated the export")

class Export(ExportBase):
    id: UUID
    report_id: UUID
    schedule_id: Optional[UUID] = None
    tenant_id: str
    initiated_by: str
    status: Literal["pending", "processing", "completed", "failed"]
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    row_count: Optional[int] = None
    error_message: Optional[str] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    delivery_status: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Query DSL schemas
class QueryFilter(BaseModel):
    field: str = Field(..., description="Field name to filter")
    operator: Literal["eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in", "like", "between"] = Field(..., description="Filter operator")
    value: Any = Field(..., description="Filter value(s)")

class QuerySort(BaseModel):
    field: str = Field(..., description="Field name to sort by")
    direction: Literal["asc", "desc"] = Field("asc", description="Sort direction")

class QueryConfig(BaseModel):
    table: str = Field(..., description="Primary table/view name")
    fields: List[str] = Field(..., description="Fields to select")
    joins: Optional[List[Dict[str, Any]]] = Field(None, description="Table joins")
    filters: Optional[List[QueryFilter]] = Field(None, description="Query filters")
    group_by: Optional[List[str]] = Field(None, description="GROUP BY fields")
    sort: Optional[List[QuerySort]] = Field(None, description="Sort configuration")
    limit: Optional[int] = Field(None, description="Result limit")

# Template schemas
class QueryTemplate(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    query_config: Dict[str, Any]
    default_filters: Optional[Dict[str, Any]] = None
    is_system: bool = False
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Response schemas
class ReportListResponse(BaseModel):
    reports: List[Report]
    total: int
    page: int
    per_page: int

class ScheduleListResponse(BaseModel):
    schedules: List[Schedule]
    total: int
    page: int
    per_page: int

class ExportListResponse(BaseModel):
    exports: List[Export]
    total: int
    page: int
    per_page: int

class QueryPreviewResponse(BaseModel):
    data: List[Dict[str, Any]]
    columns: List[str]
    total_rows: int
    execution_time_ms: int

class ScheduleTestResponse(BaseModel):
    is_valid: bool
    next_runs: List[datetime]
    error_message: Optional[str] = None
