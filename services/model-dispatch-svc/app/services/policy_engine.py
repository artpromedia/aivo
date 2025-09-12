"""Policy Engine Service - Core routing logic."""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any

from app.config import settings
from app.models import (
    GradeBand,
    LLMProvider,
    PolicyConfig,
    PolicyRequest,
    PolicyResponse,
    Region,
    RouteRule,
    SubjectType,
    TeacherOverride,
)


class PolicyEngine:
    """Core policy engine for LLM provider routing."""

    def __init__(self) -> None:
        """Initialize the policy engine."""
        self.config: PolicyConfig | None = None
        self.teacher_overrides: dict[str, dict[str, Any]] = {}
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "provider_distribution": {},
            "region_distribution": {},
            "response_times": [],
            "last_updated": datetime.now(),
        }
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the policy engine with default configuration."""
        # Create default rules for different subject/grade/region combinations
        default_rules = self._create_default_rules()

        self.config = PolicyConfig(
            rules=default_rules,
            default_provider=LLMProvider.OPENAI,
            default_moderation_threshold=settings.default_moderation_threshold,
            cache_enabled=settings.cache_enabled,
            cache_ttl_seconds=settings.cache_ttl_seconds,
        )

    def _create_default_rules(self) -> list[RouteRule]:
        """Create default routing rules."""
        rules = []

        # High priority rules for specific combinations
        # STEM subjects in K-2 use local models for safety
        rules.append(
            RouteRule(
                priority=100,
                conditions={
                    "subject": [SubjectType.MATH, SubjectType.SCIENCE],
                    "grade_band": [GradeBand.K_2],
                },
                provider=LLMProvider.LOCAL,
                template_ids=["local_stem_k2_safe", "local_basic_math"],
                moderation_threshold=0.9,
                provider_config={
                    "safety_mode": "strict",
                    "content_filter": "high",
                },
                description=("STEM subjects for K-2 use local models with high safety"),
            )
        )

        # EU regions use Azure OpenAI for data residency
        rules.append(
            RouteRule(
                priority=90,
                conditions={
                    "region": [Region.EU_WEST, Region.EU_CENTRAL],
                },
                provider=LLMProvider.AZURE_OPENAI,
                template_ids=["azure_general", "azure_educational"],
                moderation_threshold=0.8,
                provider_config={"region": "eu", "data_residency": True},
                description=("EU regions use Azure OpenAI for data residency compliance"),
            )
        )

        # High school advanced subjects use Anthropic Claude
        rules.append(
            RouteRule(
                priority=80,
                conditions={
                    "grade_band": [GradeBand.GRADE_9_12],
                    "subject": [SubjectType.ENGLISH, SubjectType.HISTORY],
                },
                provider=LLMProvider.ANTHROPIC,
                template_ids=[
                    "claude_advanced_reasoning",
                    "claude_literary_analysis",
                ],
                moderation_threshold=0.6,
                provider_config={
                    "model": "claude-3-sonnet",
                    "max_tokens": 4000,
                },
                description=("High school humanities use Claude for advanced reasoning"),
            )
        )

        # Creative subjects use specialized templates
        rules.append(
            RouteRule(
                priority=70,
                conditions={
                    "subject": [SubjectType.ART, SubjectType.MUSIC],
                },
                provider=LLMProvider.OPENAI,
                template_ids=["openai_creative", "openai_artistic"],
                moderation_threshold=0.5,
                provider_config={"model": "gpt-4", "temperature": 0.8},
                description=("Creative subjects use OpenAI with " "higher creativity settings"),
            )
        )

        # Asia Pacific uses Google for regional optimization
        rules.append(
            RouteRule(
                priority=60,
                conditions={
                    "region": [Region.ASIA_PACIFIC],
                },
                provider=LLMProvider.GOOGLE,
                template_ids=["google_regional", "google_multilingual"],
                moderation_threshold=0.7,
                provider_config={
                    "region": "asia",
                    "language_support": "enhanced",
                },
                description=("Asia Pacific uses Google for regional optimization"),
            )
        )

        # Default catch-all rule
        rules.append(
            RouteRule(
                priority=1,
                conditions={},  # Matches everything
                provider=LLMProvider.OPENAI,
                template_ids=["openai_general", "openai_educational"],
                moderation_threshold=0.7,
                provider_config={"model": "gpt-4", "temperature": 0.3},
                description="Default rule for all other combinations",
            )
        )

        return rules

    async def get_policy(self, request: PolicyRequest) -> PolicyResponse:
        """Get routing policy for the given request."""
        start_time = time.time()

        async with self._lock:
            self.stats["total_requests"] += 1

            # Update region distribution
            region_key = request.region.value
            self.stats["region_distribution"][region_key] = (
                self.stats["region_distribution"].get(region_key, 0) + 1
            )

        # Check for teacher override first
        if request.teacher_override:
            override_result = await self._check_teacher_override(request)
            if override_result:
                return override_result

        # Find matching rule
        matching_rule = await self._find_matching_rule(request)

        # Build response
        response = PolicyResponse(
            provider=matching_rule.provider,
            template_ids=matching_rule.template_ids.copy(),
            moderation_threshold=matching_rule.moderation_threshold,
            provider_config=matching_rule.provider_config.copy(),
            routing_reason=matching_rule.description,
            cache_ttl_seconds=(self.config.cache_ttl_seconds if self.config else 3600),
            request_id=request.request_id,
        )

        # Apply regional adjustments
        response = await self._apply_regional_adjustments(request, response)

        # Update statistics
        async with self._lock:
            provider_key = response.provider.value
            self.stats["provider_distribution"][provider_key] = (
                self.stats["provider_distribution"].get(provider_key, 0) + 1
            )

            response_time = (time.time() - start_time) * 1000
            self.stats["response_times"].append(response_time)
            if len(self.stats["response_times"]) > 1000:
                self.stats["response_times"] = self.stats["response_times"][-1000:]

        return response

    async def _find_matching_rule(self, request: PolicyRequest) -> RouteRule:
        """Find the highest priority matching rule."""
        if not self.config or not self.config.rules:
            # Return a default rule if no configuration
            return RouteRule(
                priority=1,
                conditions={},
                provider=LLMProvider.OPENAI,
                template_ids=["openai_general"],
                moderation_threshold=0.7,
                provider_config={},
                description="Default fallback rule",
            )

        # Sort rules by priority (highest first)
        sorted_rules = sorted(self.config.rules, key=lambda r: r.priority, reverse=True)

        for rule in sorted_rules:
            if not rule.enabled:
                continue

            if await self._rule_matches(rule, request):
                return rule

        # If no rules match, return the lowest priority rule as fallback
        return sorted_rules[-1] if sorted_rules else self._get_default_rule()

    async def _rule_matches(self, rule: RouteRule, request: PolicyRequest) -> bool:
        """Check if a rule matches the request."""
        conditions = rule.conditions

        # Check subject condition
        if "subject" in conditions:
            subjects = conditions["subject"]
            if isinstance(subjects, list):
                if request.subject not in subjects:
                    return False
            elif request.subject != subjects:
                return False

        # Check grade_band condition
        if "grade_band" in conditions:
            grade_bands = conditions["grade_band"]
            if isinstance(grade_bands, list):
                if request.grade_band not in grade_bands:
                    return False
            elif request.grade_band != grade_bands:
                return False

        # Check region condition
        if "region" in conditions:
            regions = conditions["region"]
            if isinstance(regions, list):
                if request.region not in regions:
                    return False
            elif request.region != regions:
                return False

        return True

    async def _apply_regional_adjustments(
        self, request: PolicyRequest, response: PolicyResponse
    ) -> PolicyResponse:
        """Apply regional adjustments to the response."""
        # Ensure data residency compliance
        if settings.enforce_data_residency:
            if request.region in [Region.EU_WEST, Region.EU_CENTRAL]:
                if response.provider not in [
                    LLMProvider.AZURE_OPENAI,
                    LLMProvider.LOCAL,
                ]:
                    if settings.fallback_to_local:
                        response.provider = LLMProvider.LOCAL
                        response.template_ids = ["local_eu_compliant"]
                        response.routing_reason += " (adjusted for EU data residency)"
                    else:
                        response.provider = LLMProvider.AZURE_OPENAI
                        response.routing_reason += " (adjusted for EU data residency)"

        return response

    async def _check_teacher_override(self, _request: PolicyRequest) -> PolicyResponse | None:
        """Check for active teacher override."""
        # For demo purposes, this would check a database or cache
        # Here we'll just return None indicating no override
        return None

    def _get_default_rule(self) -> RouteRule:
        """Get the default fallback rule."""
        return RouteRule(
            priority=1,
            conditions={},
            provider=LLMProvider.OPENAI,
            template_ids=["openai_general"],
            moderation_threshold=0.7,
            provider_config={"model": "gpt-4", "temperature": 0.3},
            description="System default rule",
        )

    async def add_teacher_override(self, override: TeacherOverride) -> str:
        """Add a teacher override."""
        override_id = f"override_{override.teacher_id}_{int(time.time())}"
        expires_at = datetime.now() + timedelta(hours=override.duration_hours)

        override_data = {
            "teacher_id": override.teacher_id,
            "subject": override.subject,
            "grade_band": override.grade_band,
            "preferred_provider": override.preferred_provider,
            "reason": override.reason,
            "expires_at": expires_at,
            "created_at": datetime.now(),
        }

        async with self._lock:
            self.teacher_overrides[override_id] = override_data

        return override_id

    async def get_stats(self) -> dict[str, Any]:
        """Get current policy statistics."""
        async with self._lock:
            avg_response_time = (
                sum(self.stats["response_times"]) / len(self.stats["response_times"])
                if self.stats["response_times"]
                else 0.0
            )

            return {
                "total_requests": self.stats["total_requests"],
                "cache_hits": self.stats["cache_hits"],
                "cache_misses": self.stats["cache_misses"],
                "provider_distribution": self.stats["provider_distribution"].copy(),
                "region_distribution": self.stats["region_distribution"].copy(),
                "average_response_time_ms": avg_response_time,
                "rules_count": len(self.config.rules) if self.config else 0,
                "last_updated": self.stats["last_updated"],
            }

    async def reload_config(self) -> bool:
        """Reload configuration from file."""
        # For demo purposes, this would reload from a file
        # Here we'll just reinitialize with defaults
        try:
            await self.initialize()
            return True
        except Exception:  # pylint: disable=broad-exception-caught
            # Intentionally broad to ensure reload is robust
            return False


# Global policy engine instance
policy_engine = PolicyEngine()
