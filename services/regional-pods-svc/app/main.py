"""
S2B-11: Regional Pods Deployment Service
Main FastAPI application for managing distributed educational AI infrastructure
"""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .services.data_residency import DataResidencyEngine
from .services.disaster_recovery import DisasterRecoveryManager
from .services.load_balancer import LoadBalancer
from .services.pod_manager import PodManager


class PodStatus(BaseModel):
    """Pod status information"""

    region: str
    status: str = Field(..., description="Pod status: healthy, degraded, unhealthy")
    capacity_used: float = Field(..., ge=0, le=100, description="Capacity utilization %")
    active_connections: int = Field(..., ge=0)
    latency_p99_ms: float = Field(..., ge=0)
    last_health_check: datetime
    compliance_status: str = Field(..., description="FERPA/GDPR compliance status")


class PodCreateRequest(BaseModel):
    """Request to create new regional pod"""

    region: str = Field(..., description="AWS/Azure region identifier")
    pod_type: str = Field(..., regex="^(primary|edge|backup|compliance)$")
    capacity_limit: int = Field(..., gt=0, description="Maximum concurrent connections")
    data_residency_zones: list[str] = Field(..., description="Allowed data residency zones")
    compliance_level: str = Field(..., regex="^(ferpa|gdpr|pipeda|all)$")


class RoutingRequest(BaseModel):
    """Request for optimal pod routing"""

    district_id: str = Field(..., description="School district identifier")
    student_location: str | None = Field(None, description="Student location for FERPA")
    workload_type: str = Field(..., regex="^(realtime|batch|ml_inference|storage)$")
    priority: str = Field("normal", regex="^(low|normal|high|critical)$")


class ResidencyAuditReport(BaseModel):
    """Data residency compliance audit report"""

    district_id: str
    audit_date: datetime
    compliance_status: str
    violations_found: int
    data_locations: dict[str, str]
    recommendations: list[str]
    next_audit_date: datetime


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Initialize services
    app.state.pod_manager = PodManager()
    app.state.data_residency = DataResidencyEngine()
    app.state.load_balancer = LoadBalancer()
    app.state.disaster_recovery = DisasterRecoveryManager()

    # Start background monitoring
    await app.state.pod_manager.start_health_monitoring()
    await app.state.disaster_recovery.start_replication_monitoring()

    yield

    # Cleanup
    await app.state.pod_manager.stop_health_monitoring()
    await app.state.disaster_recovery.stop_replication_monitoring()


app = FastAPI(
    title="S2B-11: Regional Pods Deployment Service",
    description="Distributed educational AI infrastructure management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "service": "regional-pods-svc",
        "version": "1.0.0",
    }


@app.get("/metrics")
async def get_metrics():
    """Prometheus-compatible metrics endpoint"""
    pod_manager: PodManager = app.state.pod_manager
    return await pod_manager.get_prometheus_metrics()


# Pod Management Endpoints


@app.post("/pods", response_model=dict[str, Any])
async def create_pod(request: PodCreateRequest):
    """Deploy new regional pod"""
    pod_manager: PodManager = app.state.pod_manager

    try:
        pod = await pod_manager.create_pod(
            region=request.region,
            pod_type=request.pod_type,
            capacity_limit=request.capacity_limit,
            data_residency_zones=request.data_residency_zones,
            compliance_level=request.compliance_level,
        )

        return {
            "pod_id": pod.pod_id,
            "region": pod.region,
            "status": "deploying",
            "estimated_ready_time": datetime.utcnow() + timedelta(minutes=10),
            "message": f"Pod deployment initiated for region {request.region}",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pod: {str(e)}",
        ) from e


@app.get("/pods/{region}", response_model=PodStatus)
async def get_pod_status(region: str):
    """Get pod status and metrics"""
    pod_manager: PodManager = app.state.pod_manager

    try:
        pod_status = await pod_manager.get_pod_status(region)

        if not pod_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pod not found in region {region}",
            )

        return pod_status

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pod status: {str(e)}",
        ) from e


@app.put("/pods/{region}/scale")
async def scale_pod(region: str, new_capacity: int = Field(..., gt=0)):
    """Manual pod scaling operations"""
    pod_manager: PodManager = app.state.pod_manager

    try:
        result = await pod_manager.scale_pod(region, new_capacity)

        return {
            "region": region,
            "old_capacity": result["old_capacity"],
            "new_capacity": new_capacity,
            "scaling_status": result["status"],
            "estimated_completion": result["estimated_completion"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scale pod: {str(e)}",
        ) from e


@app.delete("/pods/{region}")
async def shutdown_pod(region: str, force: bool = False):
    """Graceful pod shutdown"""
    pod_manager: PodManager = app.state.pod_manager

    try:
        result = await pod_manager.shutdown_pod(region, force=force)

        return {
            "region": region,
            "shutdown_status": result["status"],
            "connections_drained": result["connections_drained"],
            "estimated_completion": result["estimated_completion"],
            "message": "Pod shutdown initiated successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to shutdown pod: {str(e)}",
        ) from e


# Data Residency Endpoints


@app.post("/residency/validate")
async def validate_data_placement(
    district_id: str,
    data_type: str,
    proposed_location: str,
):
    """Validate data placement compliance"""
    data_residency: DataResidencyEngine = app.state.data_residency

    try:
        validation_result = await data_residency.validate_placement(
            district_id=district_id,
            data_type=data_type,
            proposed_location=proposed_location,
        )

        return {
            "district_id": district_id,
            "data_type": data_type,
            "proposed_location": proposed_location,
            "compliant": validation_result["compliant"],
            "violations": validation_result["violations"],
            "approved_locations": validation_result["approved_locations"],
            "reasoning": validation_result["reasoning"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate data placement: {str(e)}",
        ) from e


@app.get("/residency/audit/{district_id}", response_model=ResidencyAuditReport)
async def get_residency_audit(district_id: str):
    """Get residency audit report"""
    data_residency: DataResidencyEngine = app.state.data_residency

    try:
        audit_report = await data_residency.generate_audit_report(district_id)

        if not audit_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No audit data found for district {district_id}",
            )

        return audit_report

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate audit report: {str(e)}",
        ) from e


@app.post("/residency/migrate")
async def initiate_data_migration(
    district_id: str,
    from_region: str,
    to_region: str,
    data_types: list[str],
):
    """Initiate compliant data migration"""
    data_residency: DataResidencyEngine = app.state.data_residency

    try:
        migration_result = await data_residency.initiate_migration(
            district_id=district_id,
            from_region=from_region,
            to_region=to_region,
            data_types=data_types,
        )

        return {
            "migration_id": migration_result["migration_id"],
            "district_id": district_id,
            "from_region": from_region,
            "to_region": to_region,
            "data_types": data_types,
            "status": migration_result["status"],
            "estimated_completion": migration_result["estimated_completion"],
            "compliance_verified": migration_result["compliance_verified"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate migration: {str(e)}",
        ) from e


# Load Balancing Endpoints


@app.get("/routing/{district_id}")
async def get_optimal_routing(district_id: str, workload_type: str = "realtime"):
    """Get optimal pod assignment"""
    load_balancer: LoadBalancer = app.state.load_balancer

    try:
        routing_decision = await load_balancer.get_optimal_pod(
            district_id=district_id,
            workload_type=workload_type,
        )

        return {
            "district_id": district_id,
            "workload_type": workload_type,
            "assigned_pod": routing_decision["pod_id"],
            "region": routing_decision["region"],
            "estimated_latency_ms": routing_decision["estimated_latency"],
            "capacity_available": routing_decision["capacity_available"],
            "compliance_verified": routing_decision["compliance_verified"],
            "fallback_pods": routing_decision["fallback_pods"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to determine optimal routing: {str(e)}",
        ) from e


@app.post("/routing/override")
async def override_routing(
    district_id: str,
    force_region: str,
    duration_minutes: int = 60,
    reason: str = "Manual override",
):
    """Manual routing override for maintenance"""
    load_balancer: LoadBalancer = app.state.load_balancer

    try:
        override_result = await load_balancer.set_routing_override(
            district_id=district_id,
            force_region=force_region,
            duration_minutes=duration_minutes,
            reason=reason,
        )

        return {
            "district_id": district_id,
            "force_region": force_region,
            "override_active_until": override_result["expires_at"],
            "reason": reason,
            "override_id": override_result["override_id"],
            "message": "Routing override activated successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set routing override: {str(e)}",
        ) from e


@app.get("/capacity/metrics")
async def get_capacity_metrics():
    """Real-time capacity across all pods"""
    pod_manager: PodManager = app.state.pod_manager

    try:
        capacity_metrics = await pod_manager.get_global_capacity_metrics()

        return {
            "timestamp": datetime.utcnow(),
            "global_capacity_used": capacity_metrics["global_used"],
            "global_capacity_available": capacity_metrics["global_available"],
            "regional_breakdown": capacity_metrics["regional_breakdown"],
            "scaling_recommendations": capacity_metrics["scaling_recommendations"],
            "alert_status": capacity_metrics["alert_status"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get capacity metrics: {str(e)}",
        ) from e


# Educational-specific endpoints


@app.get("/education/calendar-scaling")
async def get_calendar_scaling_forecast():
    """Get educational calendar-based scaling forecast"""
    pod_manager: PodManager = app.state.pod_manager

    try:
        forecast = await pod_manager.generate_calendar_scaling_forecast()

        return {
            "current_period": forecast["current_period"],
            "next_scaling_event": forecast["next_event"],
            "recommended_actions": forecast["recommendations"],
            "peak_periods": forecast["peak_periods"],
            "cost_optimization": forecast["cost_optimization"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate scaling forecast: {str(e)}",
        ) from e


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info",
    )
