from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# Feature Flag schemas
class TargetingRules(BaseModel):
    roles: Optional[List[str]] = []
    regions: Optional[List[str]] = []
    grade_bands: Optional[List[str]] = []
    include_users: Optional[List[str]] = []
    exclude_users: Optional[List[str]] = []

class FeatureFlagCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    enabled: bool = False
    rollout_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    targeting_rules: Optional[TargetingRules] = None
    tenant_id: Optional[str] = None
    is_experiment: bool = False
    experiment_id: Optional[str] = None

class FeatureFlagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    rollout_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    targeting_rules: Optional[TargetingRules] = None
    is_experiment: Optional[bool] = None
    experiment_id: Optional[str] = None

class FeatureFlagResponse(BaseModel):
    id: int
    key: str
    name: str
    description: Optional[str]
    enabled: bool
    rollout_percentage: float
    targeting_rules: Dict[str, Any]
    tenant_id: Optional[str]
    is_experiment: bool
    experiment_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True

# Experiment schemas
class ExperimentVariant(BaseModel):
    name: str
    weight: float = Field(..., ge=0.0, le=100.0)
    description: Optional[str] = None

class ExperimentCreate(BaseModel):
    experiment_id: str = Field(..., min_length=1, max_length=100)
    flag_id: int
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    variants: List[ExperimentVariant] = []
    success_metrics: List[str] = []
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ExperimentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    variants: Optional[List[ExperimentVariant]] = None
    success_metrics: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None

class ExperimentResponse(BaseModel):
    id: int
    experiment_id: str
    flag_id: int
    name: str
    description: Optional[str]
    hypothesis: Optional[str]
    variants: List[Dict[str, Any]]
    success_metrics: List[str]
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    results: Dict[str, Any]
    statistical_significance: Optional[float]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True

# Evaluation schemas
class EvaluationContext(BaseModel):
    user_id: str
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    user_role: Optional[str] = None
    user_region: Optional[str] = None
    user_grade_band: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = {}

class EvaluationRequest(BaseModel):
    flag_key: str
    context: EvaluationContext
    default_value: bool = False

class EvaluationResponse(BaseModel):
    flag_key: str
    value: bool
    variant: Optional[str] = None
    experiment_id: Optional[str] = None
    reason: str  # "enabled", "disabled", "rollout", "targeting", "experiment"

class BulkEvaluationRequest(BaseModel):
    flag_keys: List[str]
    context: EvaluationContext
    default_values: Optional[Dict[str, bool]] = {}

class BulkEvaluationResponse(BaseModel):
    evaluations: Dict[str, EvaluationResponse]

# Exposure schemas
class ExposureEvent(BaseModel):
    flag_key: str
    user_id: str
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    user_role: Optional[str] = None
    user_region: Optional[str] = None
    user_grade_band: Optional[str] = None
    variant: Optional[str] = None
    evaluated_value: bool
    evaluation_context: Optional[Dict[str, Any]] = {}

class ExposureResponse(BaseModel):
    success: bool
    message: str

# Analytics schemas
class FlagAnalytics(BaseModel):
    flag_id: int
    flag_key: str
    total_exposures: int
    unique_users: int
    exposure_rate: float
    conversion_rate: Optional[float] = None
    period_start: datetime
    period_end: datetime

class ExperimentAnalytics(BaseModel):
    experiment_id: str
    variants: Dict[str, Dict[str, Any]]  # variant_name -> metrics
    statistical_significance: Optional[float]
    confidence_interval: Optional[Dict[str, float]]
    sample_size: int
    period_start: datetime
    period_end: datetime
