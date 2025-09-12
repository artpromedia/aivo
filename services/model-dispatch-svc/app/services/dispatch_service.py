"""
Model dispatch service for LLM provider selection.

Handles routing decisions based on subject, grade band, and region.
"""

from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.models import (
    DispatchLog,
    DispatchPolicy,
    GradeBand,
    ModelProvider,
    PromptTemplate,
    Region,
    RegionalRouting,
    Subject,
)

logger = get_logger(__name__)


class DispatchRequest(BaseModel):
    """Request for model dispatch."""

    subject: Subject
    grade_band: GradeBand
    region: Region
    teacher_override: bool = False
    override_provider_id: UUID | None = None
    override_reason: str | None = None
    request_id: str


class DispatchResponse(BaseModel):
    """Response from model dispatch."""

    provider_id: UUID
    provider_name: str
    endpoint_url: str
    template_ids: list[UUID]
    moderation_threshold: float
    policy_id: UUID
    allow_teacher_override: bool
    rate_limits: dict[str, int]
    estimated_cost: dict[str, float]


class ModelDispatchService:
    """Service for dispatching requests to appropriate LLM providers."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session

    async def dispatch_request(self, request: DispatchRequest) -> DispatchResponse:
        """
        Dispatch a request to the appropriate model provider.

        Args:
            request: The dispatch request containing subject, grade, region

        Returns:
            DispatchResponse with selected provider and configuration

        Raises:
            ValueError: If no suitable provider found
        """
        logger.info(
            "Processing dispatch request",
            subject=request.subject,
            grade_band=request.grade_band,
            region=request.region,
            request_id=request.request_id,
        )

        # Check regional routing constraints first
        await self._validate_regional_compliance(request.region)

        # Handle teacher override if specified
        if request.teacher_override and request.override_provider_id:
            return await self._handle_teacher_override(request)

        # Find matching policy
        policy = await self._find_matching_policy(
            request.subject, request.grade_band, request.region
        )

        if not policy:
            raise ValueError(
                f"No dispatch policy found for {request.subject}/"
                f"{request.grade_band}/{request.region}"
            )

        # Get provider details
        provider = await self._get_provider(policy.primary_provider_id)
        if not provider or not provider.is_active:
            # Try fallback providers
            provider = await self._get_fallback_provider(policy.fallback_provider_ids)

        if not provider:
            raise ValueError(f"No active provider found for policy {policy.id}")

        # Get template IDs
        template_ids = await self._get_template_ids(
            policy.template_ids, request.subject, request.grade_band
        )

        # Create response
        response = DispatchResponse(
            provider_id=provider.id,
            provider_name=provider.name,
            endpoint_url=provider.endpoint_url,
            template_ids=template_ids,
            moderation_threshold=policy.moderation_threshold,
            policy_id=policy.id,
            allow_teacher_override=policy.allow_teacher_override,
            rate_limits={
                "requests_per_minute": provider.rate_limit_rpm,
                "tokens_per_minute": provider.rate_limit_tpm,
            },
            estimated_cost={
                "per_1k_input_tokens": provider.cost_per_1k_input,
                "per_1k_output_tokens": provider.cost_per_1k_output,
            },
        )

        # Log the dispatch decision
        await self._log_dispatch(request, response, policy.id)

        logger.info(
            "Dispatch completed",
            request_id=request.request_id,
            provider_name=provider.name,
            policy_id=str(policy.id),
        )

        return response

    async def _validate_regional_compliance(self, region: Region) -> None:
        """Validate that the region allows model dispatch."""
        stmt = select(RegionalRouting).where(
            and_(RegionalRouting.region == region, RegionalRouting.is_active.is_(True))
        )
        result = await self.db.execute(stmt)
        routing = result.scalar_one_or_none()

        if not routing:
            logger.warning("No regional routing configuration found", region=region)
            return

        if not routing.is_active:
            raise ValueError(f"Model dispatch disabled for region {region}")

    async def _find_matching_policy(
        self, subject: Subject, grade_band: GradeBand, region: Region
    ) -> DispatchPolicy | None:
        """Find the best matching dispatch policy based on priority."""
        # Build query with fallback logic
        conditions = [DispatchPolicy.is_active.is_(True)]

        # Exact match has highest priority
        exact_stmt = (
            select(DispatchPolicy)
            .where(
                and_(
                    DispatchPolicy.subject == subject,
                    DispatchPolicy.grade_band == grade_band,
                    DispatchPolicy.region == region,
                    *conditions,
                )
            )
            .order_by(DispatchPolicy.priority)
            .limit(1)
        )

        result = await self.db.execute(exact_stmt)
        policy = result.scalar_one_or_none()
        if policy:
            return policy

        # Try subject + grade (any region)
        subject_grade_stmt = (
            select(DispatchPolicy)
            .where(
                and_(
                    DispatchPolicy.subject == subject,
                    DispatchPolicy.grade_band == grade_band,
                    DispatchPolicy.region.is_(None),
                    *conditions,
                )
            )
            .order_by(DispatchPolicy.priority)
            .limit(1)
        )

        result = await self.db.execute(subject_grade_stmt)
        policy = result.scalar_one_or_none()
        if policy:
            return policy

        # Try subject only (any grade, any region)
        subject_stmt = (
            select(DispatchPolicy)
            .where(
                and_(
                    DispatchPolicy.subject == subject,
                    DispatchPolicy.grade_band.is_(None),
                    DispatchPolicy.region.is_(None),
                    *conditions,
                )
            )
            .order_by(DispatchPolicy.priority)
            .limit(1)
        )

        result = await self.db.execute(subject_stmt)
        policy = result.scalar_one_or_none()
        if policy:
            return policy

        # Finally, try default policy (all None)
        default_stmt = (
            select(DispatchPolicy)
            .where(
                and_(
                    DispatchPolicy.subject.is_(None),
                    DispatchPolicy.grade_band.is_(None),
                    DispatchPolicy.region.is_(None),
                    *conditions,
                )
            )
            .order_by(DispatchPolicy.priority)
            .limit(1)
        )

        result = await self.db.execute(default_stmt)
        return result.scalar_one_or_none()

    async def _get_provider(self, provider_id: UUID) -> ModelProvider | None:
        """Get provider by ID."""
        stmt = select(ModelProvider).where(
            and_(ModelProvider.id == provider_id, ModelProvider.is_active.is_(True))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_fallback_provider(self, fallback_ids: list[str]) -> ModelProvider | None:
        """Get first available fallback provider."""
        for provider_id_str in fallback_ids:
            try:
                provider_id = UUID(provider_id_str)
                provider = await self._get_provider(provider_id)
                if provider:
                    return provider
            except ValueError:
                logger.warning("Invalid provider ID in fallback list", id=provider_id_str)
                continue
        return None

    async def _get_template_ids(
        self, policy_template_ids: list[str], subject: Subject, grade_band: GradeBand
    ) -> list[UUID]:
        """Get template IDs for the request."""
        template_ids = []

        # First, use explicitly configured template IDs
        for template_id_str in policy_template_ids:
            try:
                template_ids.append(UUID(template_id_str))
            except ValueError:
                logger.warning("Invalid template ID", id=template_id_str)

        # If no explicit templates, find matching ones
        if not template_ids:
            stmt = (
                select(PromptTemplate.id)
                .where(
                    and_(
                        PromptTemplate.subject == subject,
                        PromptTemplate.grade_band == grade_band,
                        PromptTemplate.is_active.is_(True),
                    )
                )
                .limit(5)  # Limit to avoid too many templates
            )
            result = await self.db.execute(stmt)
            template_ids.extend(result.scalars().all())

        return template_ids

    async def _handle_teacher_override(self, request: DispatchRequest) -> DispatchResponse:
        """Handle teacher override for provider selection."""
        if not request.override_provider_id:
            raise ValueError("Override provider ID required for teacher override")

        provider = await self._get_provider(request.override_provider_id)
        if not provider:
            raise ValueError(f"Override provider {request.override_provider_id} not found")

        # Get default policy for templates and moderation
        default_policy = await self._find_matching_policy(
            request.subject, request.grade_band, request.region
        )

        if not default_policy:
            # Create minimal response for override
            template_ids = []
            moderation_threshold = 0.8
            policy_id = request.override_provider_id  # Use provider ID as policy ID
        else:
            template_ids = await self._get_template_ids(
                default_policy.template_ids, request.subject, request.grade_band
            )
            moderation_threshold = default_policy.moderation_threshold
            policy_id = default_policy.id

        response = DispatchResponse(
            provider_id=provider.id,
            provider_name=provider.name,
            endpoint_url=provider.endpoint_url,
            template_ids=template_ids,
            moderation_threshold=moderation_threshold,
            policy_id=policy_id,
            allow_teacher_override=True,
            rate_limits={
                "requests_per_minute": provider.rate_limit_rpm,
                "tokens_per_minute": provider.rate_limit_tpm,
            },
            estimated_cost={
                "per_1k_input_tokens": provider.cost_per_1k_input,
                "per_1k_output_tokens": provider.cost_per_1k_output,
            },
        )

        # Log the override
        await self._log_dispatch(request, response, policy_id, teacher_override=True)

        return response

    async def _log_dispatch(
        self,
        request: DispatchRequest,
        response: DispatchResponse,
        policy_id: UUID,
        teacher_override: bool = False,
    ) -> None:
        """Log the dispatch decision for auditing."""
        log_entry = DispatchLog(
            request_id=request.request_id,
            subject=request.subject,
            grade_band=request.grade_band,
            region=request.region,
            selected_provider_id=response.provider_id,
            template_ids=[str(tid) for tid in response.template_ids],
            moderation_threshold=response.moderation_threshold,
            policy_id=policy_id,
            teacher_override=teacher_override,
            override_reason=request.override_reason if teacher_override else None,
        )

        self.db.add(log_entry)
        await self.db.commit()

    async def get_available_providers(self, region: Region) -> list[dict]:
        """Get list of available providers for a region."""
        # Check regional constraints
        stmt = select(RegionalRouting).where(RegionalRouting.region == region)
        result = await self.db.execute(stmt)
        routing = result.scalar_one_or_none()

        provider_stmt = select(ModelProvider).where(ModelProvider.is_active.is_(True))

        if routing:
            if routing.allowed_providers:
                # Filter to allowed providers
                allowed_ids = [UUID(pid) for pid in routing.allowed_providers]
                provider_stmt = provider_stmt.where(ModelProvider.id.in_(allowed_ids))
            elif routing.blocked_providers:
                # Exclude blocked providers
                blocked_ids = [UUID(pid) for pid in routing.blocked_providers]
                provider_stmt = provider_stmt.where(~ModelProvider.id.in_(blocked_ids))

        result = await self.db.execute(provider_stmt)
        providers = result.scalars().all()

        return [
            {
                "id": str(provider.id),
                "name": provider.name,
                "type": provider.provider_type,
                "supported_regions": provider.supported_regions,
                "max_tokens": provider.max_tokens,
                "cost_per_1k_input": provider.cost_per_1k_input,
                "cost_per_1k_output": provider.cost_per_1k_output,
                "reliability_score": provider.reliability_score,
            }
            for provider in providers
        ]

    async def get_dispatch_analytics(self, region: Region | None = None, days: int = 7) -> dict:
        """Get analytics on dispatch decisions."""
        # This would contain more complex analytics queries
        # For now, return basic stats
        stmt = select(DispatchLog)

        if region:
            stmt = stmt.where(DispatchLog.region == region)

        # Add time filtering logic here based on 'days' parameter
        result = await self.db.execute(stmt.limit(1000))
        logs = result.scalars().all()

        total_requests = len(logs)
        successful_requests = sum(1 for log in logs if log.success)
        teacher_overrides = sum(1 for log in logs if log.teacher_override)

        return {
            "total_requests": total_requests,
            "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
            "teacher_override_rate": (
                teacher_overrides / total_requests if total_requests > 0 else 0
            ),
            "most_used_subjects": {},  # Would aggregate by subject
            "most_used_grades": {},  # Would aggregate by grade_band
            "average_response_time_ms": 0,  # Would calculate from logs
        }
