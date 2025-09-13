from sqlalchemy.orm import Session
from typing import Optional, List
import hashlib
import random
import structlog

from ..models import FeatureFlag, Experiment, FlagExposure
from ..schemas import EvaluationContext, EvaluationResponse, TargetingRules

logger = structlog.get_logger()

class EvaluationService:
    def __init__(self, db: Session):
        self.db = db

    def evaluate_flag(
        self,
        flag_key: str,
        context: EvaluationContext,
        default_value: bool = False
    ) -> EvaluationResponse:
        """
        Evaluate a feature flag with tenant scoping, rollout percentage,
        and targeting rules
        """
        # Get the flag from database
        flag = self.db.query(FeatureFlag).filter(FeatureFlag.key == flag_key).first()

        if not flag:
            return EvaluationResponse(
                flag_key=flag_key,
                value=default_value,
                reason="flag_not_found"
            )

        # Check if flag is disabled
        if not flag.enabled:
            return EvaluationResponse(
                flag_key=flag_key,
                value=False,
                reason="disabled"
            )

        # Check tenant scoping
        if flag.tenant_id and flag.tenant_id != context.tenant_id:
            return EvaluationResponse(
                flag_key=flag_key,
                value=default_value,
                reason="tenant_mismatch"
            )

        # Check targeting rules
        if not self._matches_targeting_rules(flag, context):
            return EvaluationResponse(
                flag_key=flag_key,
                value=False,
                reason="targeting_rules_not_met"
            )

        # Handle experiments
        if flag.is_experiment and flag.experiment_id:
            return self._evaluate_experiment(flag, context)

        # Handle percentage rollout
        if flag.rollout_percentage < 100:
            if not self._in_rollout_percentage(flag.key, context.user_id, flag.rollout_percentage):
                return EvaluationResponse(
                    flag_key=flag_key,
                    value=False,
                    reason="rollout_percentage"
                )

        return EvaluationResponse(
            flag_key=flag_key,
            value=True,
            reason="enabled"
        )

    def _matches_targeting_rules(self, flag: FeatureFlag, context: EvaluationContext) -> bool:
        """Check if user context matches the flag's targeting rules"""
        if not flag.targeting_rules:
            return True

        rules = flag.targeting_rules

        # Check role targeting
        if rules.get("roles") and context.user_role:
            if context.user_role not in rules["roles"]:
                return False

        # Check region targeting
        if rules.get("regions") and context.user_region:
            if context.user_region not in rules["regions"]:
                return False

        # Check grade band targeting
        if rules.get("grade_bands") and context.user_grade_band:
            if context.user_grade_band not in rules["grade_bands"]:
                return False

        # Check explicit user inclusion
        if rules.get("include_users"):
            if context.user_id in rules["include_users"]:
                return True

        # Check explicit user exclusion
        if rules.get("exclude_users"):
            if context.user_id in rules["exclude_users"]:
                return False

        return True

    def _in_rollout_percentage(self, flag_key: str, user_id: str, percentage: float) -> bool:
        """Determine if user is in the rollout percentage using consistent hashing"""
        # Create a stable hash based on flag key and user ID
        hash_input = f"{flag_key}:{user_id}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()

        # Convert first 8 characters to integer and get percentage
        hash_int = int(hash_value[:8], 16)
        user_percentage = (hash_int % 10000) / 100.0  # 0-99.99

        return user_percentage < percentage

    def _evaluate_experiment(self, flag: FeatureFlag, context: EvaluationContext) -> EvaluationResponse:
        """Evaluate flag as part of an experiment with variant assignment"""
        experiment = self.db.query(Experiment).filter(
            Experiment.experiment_id == flag.experiment_id
        ).first()

        if not experiment or experiment.status != "running":
            return EvaluationResponse(
                flag_key=flag.key,
                value=False,
                reason="experiment_not_running"
            )

        # Assign variant based on user hash and variant weights
        variant = self._assign_experiment_variant(experiment, context.user_id)

        if not variant:
            return EvaluationResponse(
                flag_key=flag.key,
                value=False,
                reason="no_variant_assigned"
            )

        # For simplicity, control variant = False, treatment variants = True
        # In practice, this could be more sophisticated
        value = variant["name"] != "control"

        return EvaluationResponse(
            flag_key=flag.key,
            value=value,
            variant=variant["name"],
            experiment_id=experiment.experiment_id,
            reason="experiment"
        )

    def _assign_experiment_variant(self, experiment: Experiment, user_id: str) -> Optional[dict]:
        """Assign a user to an experiment variant based on weights"""
        if not experiment.variants:
            return None

        # Create stable hash for variant assignment
        hash_input = f"{experiment.experiment_id}:{user_id}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()
        hash_int = int(hash_value[:8], 16)
        user_percentage = (hash_int % 10000) / 100.0  # 0-99.99

        # Assign variant based on cumulative weights
        cumulative_weight = 0
        for variant in experiment.variants:
            cumulative_weight += variant.get("weight", 0)
            if user_percentage < cumulative_weight:
                return variant

        # Fallback to first variant if weights don't add up to 100
        return experiment.variants[0] if experiment.variants else None

    def get_enabled_flags_for_tenant(self, tenant_id: Optional[str]) -> List[FeatureFlag]:
        """Get all enabled flags for a specific tenant"""
        query = self.db.query(FeatureFlag).filter(FeatureFlag.enabled == True)

        if tenant_id:
            # Include both tenant-specific flags and global flags
            query = query.filter(
                (FeatureFlag.tenant_id == tenant_id) |
                (FeatureFlag.tenant_id.is_(None))
            )
        else:
            # Only global flags if no tenant specified
            query = query.filter(FeatureFlag.tenant_id.is_(None))

        return query.all()

    async def log_exposure(
        self,
        flag_key: str,
        context: EvaluationContext,
        result: EvaluationResponse
    ):
        """Log flag exposure for analytics"""
        try:
            # Get flag ID
            flag = self.db.query(FeatureFlag).filter(FeatureFlag.key == flag_key).first()
            if not flag:
                return

            # Get experiment ID if applicable
            experiment_id = None
            if result.experiment_id:
                experiment = self.db.query(Experiment).filter(
                    Experiment.experiment_id == result.experiment_id
                ).first()
                if experiment:
                    experiment_id = experiment.id

            # Create exposure record
            exposure = FlagExposure(
                flag_id=flag.id,
                experiment_id=experiment_id,
                user_id=context.user_id,
                tenant_id=context.tenant_id,
                session_id=context.session_id,
                user_role=context.user_role,
                user_region=context.user_region,
                user_grade_band=context.user_grade_band,
                flag_key=flag_key,
                variant=result.variant,
                evaluated_value=result.value,
                evaluation_context=context.custom_attributes or {}
            )

            self.db.add(exposure)
            self.db.commit()

            logger.info("exposure_logged",
                       flag_key=flag_key,
                       user_id=context.user_id,
                       value=result.value,
                       variant=result.variant)

        except Exception as e:
            logger.error("exposure_logging_failed",
                        flag_key=flag_key,
                        user_id=context.user_id,
                        error=str(e))
            self.db.rollback()
