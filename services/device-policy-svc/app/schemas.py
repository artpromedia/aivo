"""Pydantic schemas for Device Policy Service."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from .models import PolicyStatus, PolicyType, SyncStatus


# Base schemas
class PolicyBase(BaseModel):
    """Base policy schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    policy_type: PolicyType
    config: dict = Field(..., description="Policy configuration JSON")
    target_criteria: dict | None = Field(None, description="Target device criteria")
    priority: int = Field(100, ge=1, le=1000)
    effective_from: datetime | None = None
    effective_until: datetime | None = None


class PolicyCreate(PolicyBase):
    """Schema for creating a new policy."""

    tenant_id: str | None = Field(None, max_length=255)


class PolicyUpdate(BaseModel):
    """Schema for updating a policy."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    config: dict | None = None
    target_criteria: dict | None = None
    priority: int | None = Field(None, ge=1, le=1000)
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    status: PolicyStatus | None = None


class PolicyResponse(PolicyBase):
    """Schema for policy responses."""

    policy_id: UUID
    status: PolicyStatus
    version: int
    checksum: str
    created_by: str | None
    tenant_id: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


# Device policy assignment schemas
class DevicePolicyAssign(BaseModel):
    """Schema for assigning policy to device."""

    device_id: UUID
    policy_id: UUID


class DevicePolicyResponse(BaseModel):
    """Schema for device policy assignment response."""

    assignment_id: UUID
    device_id: UUID
    policy_id: UUID
    sync_status: SyncStatus
    last_sync_at: datetime | None
    sync_attempts: int
    last_error: str | None
    applied_version: int | None
    applied_checksum: str | None
    assigned_by: str | None
    assigned_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


# Policy sync schemas
class PolicySyncRequest(BaseModel):
    """Schema for policy sync request."""

    device_id: UUID
    current_policies: dict[str, int] = Field(
        default_factory=dict, description="Current policy versions by policy_id"
    )


class PolicyDiff(BaseModel):
    """Schema for policy differences."""

    policy_id: UUID
    action: str = Field(..., pattern="^(add|update|remove)$")
    from_version: int | None = None
    to_version: int | None = None
    config: dict | None = None
    checksum: str | None = None


class PolicySyncResponse(BaseModel):
    """Schema for policy sync response."""

    device_id: UUID
    sync_type: str = Field(..., pattern="^(full|diff|patch)$")
    policies: list[PolicyDiff]
    sync_timestamp: datetime = Field(default_factory=datetime.utcnow)


# Allowlist schemas
class AllowlistEntryBase(BaseModel):
    """Base allowlist entry schema."""

    entry_type: str = Field(..., pattern="^(domain|url|ip|subnet)$")
    value: str = Field(..., min_length=1, max_length=2048)
    description: str | None = Field(None, max_length=1000)
    category: str | None = Field(None, max_length=100)
    tags: list[str] | None = None
    priority: int = Field(100, ge=1, le=1000)


class AllowlistEntryCreate(AllowlistEntryBase):
    """Schema for creating allowlist entry."""

    tenant_id: str | None = Field(None, max_length=255)


class AllowlistEntryUpdate(BaseModel):
    """Schema for updating allowlist entry."""

    value: str | None = Field(None, min_length=1, max_length=2048)
    description: str | None = Field(None, max_length=1000)
    category: str | None = Field(None, max_length=100)
    tags: list[str] | None = None
    priority: int | None = Field(None, ge=1, le=1000)
    is_active: bool | None = None


class AllowlistEntryResponse(AllowlistEntryBase):
    """Schema for allowlist entry response."""

    entry_id: UUID
    is_active: bool
    created_by: str | None
    tenant_id: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


# Kiosk policy schemas
class KioskAppConfig(BaseModel):
    """Schema for kiosk app configuration."""

    package_name: str = Field(..., description="App package name")
    app_name: str = Field(..., description="Display name")
    version: str | None = None
    auto_launch: bool = True
    allow_exit: bool = False
    fullscreen: bool = True


class KioskPolicyConfig(BaseModel):
    """Schema for kiosk policy configuration."""

    mode: str = Field("single_app", pattern="^(single_app|multi_app)$")
    apps: list[KioskAppConfig] = Field(..., min_items=1)
    study_windows: list[dict] | None = None
    restrictions: dict | None = None


# Network policy schemas
class NetworkProfile(BaseModel):
    """Schema for network profile configuration."""

    ssid: str = Field(..., description="Network SSID")
    security_type: str = Field(..., pattern="^(open|wep|wpa|wpa2|wpa3)$")
    password: str | None = None
    hidden: bool = False
    auto_connect: bool = True
    priority: int = Field(1, ge=1, le=10)


class NetworkPolicyConfig(BaseModel):
    """Schema for network policy configuration."""

    profiles: list[NetworkProfile] = Field(..., min_items=1)
    dns_servers: list[str] | None = None
    proxy_config: dict | None = None
    firewall_rules: list[dict] | None = None


# DNS filter schemas
class DNSFilterRule(BaseModel):
    """Schema for DNS filter rule."""

    rule_type: str = Field(..., pattern="^(block|allow|redirect)$")
    pattern: str = Field(..., description="Domain pattern or regex")
    action: str = Field(..., description="Action to take")
    category: str | None = None
    priority: int = Field(100, ge=1, le=1000)


class DNSPolicyConfig(BaseModel):
    """Schema for DNS policy configuration."""

    default_action: str = Field("allow", pattern="^(allow|block)$")
    rules: list[DNSFilterRule] = Field(default_factory=list)
    safe_search: bool = True
    block_malware: bool = True
    custom_dns: list[str] | None = None


# Study window schemas
class StudyWindow(BaseModel):
    """Schema for study window configuration."""

    name: str = Field(..., description="Window name")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    days: list[str] = Field(..., description="Days of week", min_items=1)
    timezone: str = Field("UTC", description="Timezone")
    allowed_apps: list[str] | None = None
    restrictions: dict | None = None


class StudyWindowPolicyConfig(BaseModel):
    """Schema for study window policy configuration."""

    windows: list[StudyWindow] = Field(..., min_items=1)
    default_mode: str = Field("restricted", pattern="^(open|restricted|locked)$")
    break_duration: int = Field(15, ge=5, le=60, description="Break duration in minutes")


# Paginated response schemas
class PaginatedResponse(BaseModel):
    """Schema for paginated responses."""

    items: list
    total: int
    page: int
    size: int
    pages: int


class PolicyListResponse(PaginatedResponse):
    """Schema for paginated policy list."""

    items: list[PolicyResponse]


class AllowlistResponse(PaginatedResponse):
    """Schema for paginated allowlist response."""

    items: list[AllowlistEntryResponse]


# Error response schemas
class ErrorResponse(BaseModel):
    """Schema for error responses."""

    error: str
    message: str
    details: dict | None = None


class ValidationErrorResponse(BaseModel):
    """Schema for validation error responses."""

    error: str = "validation_error"
    message: str
    errors: list[dict]
