"""Analytics Service - Metrics API over Snowflake with differential privacy."""

import hashlib
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Query, Request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.snowflake import SnowflakeInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config import Settings
from app.models import (
    AnalyticsResponse,
    MasteryMetrics,
    StreakMetrics,
    SummaryMetrics,
)
from app.privacy import DifferentialPrivacy
from app.snowflake import SnowflakeClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
settings: Settings | None = None
snowflake_client: SnowflakeClient | None = None
cache: dict[str, dict] = {}
diff_privacy: DifferentialPrivacy | None = None

# OpenTelemetry setup
resource = Resource(attributes={SERVICE_NAME: "analytics-svc"})
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint="http://jaeger:14250", insecure=True)
)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# Instrument packages
SnowflakeInstrumentor().instrument()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    global settings, snowflake_client, diff_privacy

    # Startup
    settings = Settings()
    snowflake_client = SnowflakeClient(settings)
    diff_privacy = DifferentialPrivacy(epsilon=settings.dp_epsilon)

    # Test Snowflake connection
    try:
        await snowflake_client.test_connection()
        logger.info("✅ Snowflake connection established")
    except Exception as e:
        logger.error(f"❌ Snowflake connection failed: {e}")
        raise

    yield

    # Shutdown
    if snowflake_client:
        await snowflake_client.close()


app = FastAPI(
    title="Analytics Service",
    description="Metrics API over Snowflake with differential privacy",
    version="1.0.0",
    lifespan=lifespan,
)

# Add OpenTelemetry instrumentation
FastAPIInstrumentor.instrument_app(app)


def get_cache_key(tenant_id: str, endpoint: str, **params) -> str:
    """Generate cache key for request."""
    key_data = f"{tenant_id}:{endpoint}:{params}"
    return hashlib.md5(key_data.encode()).hexdigest()


def is_cache_valid(timestamp: datetime) -> bool:
    """Check if cache entry is still valid (30s TTL)."""
    return datetime.utcnow() - timestamp < timedelta(seconds=30)


async def get_cached_or_compute(
    cache_key: str, compute_func, *args, **kwargs
) -> dict:
    """Get from cache or compute and cache the result."""
    if cache_key in cache:
        entry = cache[cache_key]
        if is_cache_valid(entry["timestamp"]):
            logger.info(f"Cache hit for key: {cache_key}")
            return entry["data"]

    # Compute new result
    logger.info(f"Cache miss for key: {cache_key}")
    result = await compute_func(*args, **kwargs)

    # Cache the result
    cache[cache_key] = {"data": result, "timestamp": datetime.utcnow()}

    return result


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    with tracer.start_as_current_span("health_check"):
        return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.get("/metrics/summary", response_model=AnalyticsResponse[SummaryMetrics])
async def get_summary_metrics(
    request: Request,
    tenant_id: str = Query(..., description="Tenant ID"),
    start_date: str | None = Query(
        None, description="Start date (YYYY-MM-DD)"
    ),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Get summary learning metrics for a tenant."""
    with tracer.start_as_current_span("get_summary_metrics") as span:
        span.set_attribute("tenant_id", tenant_id)
        span.set_attribute("start_date", start_date or "")
        span.set_attribute("end_date", end_date or "")

        cache_key = get_cache_key(
            tenant_id, "summary", start_date=start_date, end_date=end_date
        )

        async def compute_summary():
            return await snowflake_client.get_summary_metrics(
                tenant_id, start_date, end_date
            )

        try:
            raw_data = await get_cached_or_compute(cache_key, compute_summary)

            # Apply differential privacy
            private_data = diff_privacy.add_noise_to_metrics(raw_data)

            return AnalyticsResponse(
                data=SummaryMetrics(**private_data),
                tenant_id=tenant_id,
                generated_at=datetime.utcnow(),
                cache_hit=cache_key in cache,
            )

        except Exception as e:
            logger.error(f"Error getting summary metrics: {e}")
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise HTTPException(
                status_code=500, detail="Internal server error"
            )


@app.get(
    "/metrics/mastery",
    response_model=AnalyticsResponse[list[MasteryMetrics]]
)
async def get_mastery_metrics(
    request: Request,
    tenant_id: str = Query(..., description="Tenant ID"),
    start_date: str | None = Query(
        None, description="Start date (YYYY-MM-DD)"
    ),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, description="Max results", le=1000),
) -> AnalyticsResponse[list[MasteryMetrics]]:
    """Get mastery progression metrics for a tenant."""
    with tracer.start_as_current_span("get_mastery_metrics") as span:
        span.set_attribute("tenant_id", tenant_id)
        span.set_attribute("start_date", start_date or "")
        span.set_attribute("end_date", end_date or "")
        span.set_attribute("limit", limit)

        cache_key = get_cache_key(
            tenant_id,
            "mastery",
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        async def compute_mastery():
            return await snowflake_client.get_mastery_metrics(
                tenant_id, start_date, end_date, limit
            )

        try:
            raw_data = await get_cached_or_compute(cache_key, compute_mastery)

            # Apply differential privacy to each mastery entry
            private_data = [
                diff_privacy.add_noise_to_metrics(entry) for entry in raw_data
            ]

            return AnalyticsResponse(
                data=[MasteryMetrics(**entry) for entry in private_data],
                tenant_id=tenant_id,
                generated_at=datetime.utcnow(),
                cache_hit=cache_key in cache,
            )

        except Exception as e:
            logger.error(f"Error getting mastery metrics: {e}")
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise HTTPException(
                status_code=500, detail="Internal server error"
            )


@app.get(
    "/metrics/streaks",
    response_model=AnalyticsResponse[list[StreakMetrics]]
)
async def get_streak_metrics(
    request: Request,
    tenant_id: str = Query(..., description="Tenant ID"),
    start_date: str | None = Query(
        None, description="Start date (YYYY-MM-DD)"
    ),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, description="Max results", le=1000),
) -> AnalyticsResponse[list[StreakMetrics]]:
    """Get learning streak metrics for a tenant."""
    with tracer.start_as_current_span("get_streak_metrics") as span:
        span.set_attribute("tenant_id", tenant_id)
        span.set_attribute("start_date", start_date or "")
        span.set_attribute("end_date", end_date or "")
        span.set_attribute("limit", limit)

        cache_key = get_cache_key(
            tenant_id,
            "streaks",
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        async def compute_streaks():
            return await snowflake_client.get_streak_metrics(
                tenant_id, start_date, end_date, limit
            )

        try:
            raw_data = await get_cached_or_compute(cache_key, compute_streaks)

            # Apply differential privacy to each streak entry
            private_data = [
                diff_privacy.add_noise_to_metrics(entry) for entry in raw_data
            ]

            return AnalyticsResponse(
                data=[StreakMetrics(**entry) for entry in private_data],
                tenant_id=tenant_id,
                generated_at=datetime.utcnow(),
                cache_hit=cache_key in cache,
            )

        except Exception as e:
            logger.error(f"Error getting streak metrics: {e}")
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise HTTPException(
                status_code=500, detail="Internal server error"
            )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
