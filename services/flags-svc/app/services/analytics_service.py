from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Dict, Any
from datetime import datetime, timedelta
import structlog

from ..models import FlagExposure, FeatureFlag, Experiment
from ..schemas import ExposureEvent, FlagAnalytics, ExperimentAnalytics

logger = structlog.get_logger()

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    async def log_exposure(self, exposure: ExposureEvent):
        """Log a single flag exposure event"""
        # Get flag
        flag = self.db.query(FeatureFlag).filter(FeatureFlag.key == exposure.flag_key).first()
        if not flag:
            logger.warning("exposure_for_unknown_flag", flag_key=exposure.flag_key)
            return

        # Get experiment if applicable
        experiment_id = None
        if flag.is_experiment and flag.experiment_id:
            experiment = self.db.query(Experiment).filter(
                Experiment.experiment_id == flag.experiment_id
            ).first()
            if experiment:
                experiment_id = experiment.id

        # Create exposure record
        exposure_record = FlagExposure(
            flag_id=flag.id,
            experiment_id=experiment_id,
            user_id=exposure.user_id,
            tenant_id=exposure.tenant_id,
            session_id=exposure.session_id,
            user_role=exposure.user_role,
            user_region=exposure.user_region,
            user_grade_band=exposure.user_grade_band,
            flag_key=exposure.flag_key,
            variant=exposure.variant,
            evaluated_value=exposure.evaluated_value,
            evaluation_context=exposure.evaluation_context
        )

        self.db.add(exposure_record)
        self.db.commit()

        logger.info("exposure_logged",
                   flag_key=exposure.flag_key,
                   user_id=exposure.user_id,
                   value=exposure.evaluated_value)

    async def log_exposures_batch(self, exposures: List[ExposureEvent]):
        """Log multiple flag exposure events efficiently"""
        exposure_records = []

        for exposure in exposures:
            # Get flag
            flag = self.db.query(FeatureFlag).filter(FeatureFlag.key == exposure.flag_key).first()
            if not flag:
                logger.warning("exposure_for_unknown_flag", flag_key=exposure.flag_key)
                continue

            # Get experiment if applicable
            experiment_id = None
            if flag.is_experiment and flag.experiment_id:
                experiment = self.db.query(Experiment).filter(
                    Experiment.experiment_id == flag.experiment_id
                ).first()
                if experiment:
                    experiment_id = experiment.id

            exposure_record = FlagExposure(
                flag_id=flag.id,
                experiment_id=experiment_id,
                user_id=exposure.user_id,
                tenant_id=exposure.tenant_id,
                session_id=exposure.session_id,
                user_role=exposure.user_role,
                user_region=exposure.user_region,
                user_grade_band=exposure.user_grade_band,
                flag_key=exposure.flag_key,
                variant=exposure.variant,
                evaluated_value=exposure.evaluated_value,
                evaluation_context=exposure.evaluation_context
            )
            exposure_records.append(exposure_record)

        if exposure_records:
            self.db.add_all(exposure_records)
            self.db.commit()

            logger.info("batch_exposures_logged", count=len(exposure_records))

    async def get_flag_analytics(self, flag_key: str, period_days: int = 7) -> FlagAnalytics:
        """Get analytics data for a specific flag"""
        # Get flag
        flag = self.db.query(FeatureFlag).filter(FeatureFlag.key == flag_key).first()
        if not flag:
            raise ValueError(f"Flag {flag_key} not found")

        # Calculate period
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)

        # Query exposures in period
        exposures_query = self.db.query(FlagExposure).filter(
            FlagExposure.flag_id == flag.id,
            FlagExposure.exposed_at >= start_date,
            FlagExposure.exposed_at <= end_date
        )

        # Calculate metrics
        total_exposures = exposures_query.count()
        unique_users = exposures_query.distinct(FlagExposure.user_id).count()

        # Calculate exposure rate (exposures that evaluated to True)
        positive_exposures = exposures_query.filter(FlagExposure.evaluated_value == True).count()
        exposure_rate = (positive_exposures / total_exposures * 100) if total_exposures > 0 else 0

        return FlagAnalytics(
            flag_id=flag.id,
            flag_key=flag_key,
            total_exposures=total_exposures,
            unique_users=unique_users,
            exposure_rate=exposure_rate,
            period_start=start_date,
            period_end=end_date
        )

    async def get_experiment_analytics(self, experiment_id: str, period_days: int = 30) -> ExperimentAnalytics:
        """Get analytics data for a specific experiment"""
        # Get experiment
        experiment = self.db.query(Experiment).filter(
            Experiment.experiment_id == experiment_id
        ).first()
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Calculate period
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)

        # If experiment has specific dates, use those
        if experiment.start_date:
            start_date = max(start_date, experiment.start_date)
        if experiment.end_date:
            end_date = min(end_date, experiment.end_date)

        # Query exposures for this experiment
        exposures_query = self.db.query(FlagExposure).filter(
            FlagExposure.experiment_id == experiment.id,
            FlagExposure.exposed_at >= start_date,
            FlagExposure.exposed_at <= end_date
        )

        # Calculate variant-specific metrics
        variants_data = {}
        total_sample_size = 0

        for variant_config in experiment.variants:
            variant_name = variant_config["name"]

            # Get exposures for this variant
            variant_exposures = exposures_query.filter(FlagExposure.variant == variant_name)
            variant_count = variant_exposures.count()
            unique_users = variant_exposures.distinct(FlagExposure.user_id).count()

            # Calculate conversion rate (simplified - in practice, this would integrate with business metrics)
            conversions = variant_exposures.filter(FlagExposure.evaluated_value == True).count()
            conversion_rate = (conversions / variant_count * 100) if variant_count > 0 else 0

            variants_data[variant_name] = {
                "exposures": variant_count,
                "unique_users": unique_users,
                "conversion_rate": conversion_rate,
                "conversions": conversions,
                "expected_weight": variant_config.get("weight", 0)
            }

            total_sample_size += variant_count

        # Calculate statistical significance (simplified)
        statistical_significance = self._calculate_statistical_significance(variants_data)

        return ExperimentAnalytics(
            experiment_id=experiment_id,
            variants=variants_data,
            statistical_significance=statistical_significance,
            sample_size=total_sample_size,
            period_start=start_date,
            period_end=end_date
        )

    def _calculate_statistical_significance(self, variants_data: Dict[str, Dict[str, Any]]) -> float:
        """Calculate statistical significance between variants (simplified implementation)"""
        # This is a simplified implementation
        # In practice, you'd use proper statistical tests like chi-square or t-test

        if len(variants_data) < 2:
            return 0.0

        # Get control and treatment data
        control_data = variants_data.get("control")
        if not control_data:
            return 0.0

        # Find treatment with highest conversion rate
        best_treatment = None
        best_rate = 0

        for variant_name, data in variants_data.items():
            if variant_name != "control" and data["conversion_rate"] > best_rate:
                best_treatment = data
                best_rate = data["conversion_rate"]

        if not best_treatment:
            return 0.0

        # Simple significance calculation based on sample size and effect size
        control_rate = control_data["conversion_rate"]
        treatment_rate = best_treatment["conversion_rate"]

        effect_size = abs(treatment_rate - control_rate) / 100.0
        sample_size = min(control_data["exposures"], best_treatment["exposures"])

        # Simplified significance score based on effect size and sample size
        significance = min(effect_size * sample_size * 0.1, 0.99)

        return significance

    async def get_tenant_analytics(self, tenant_id: str, period_days: int = 7) -> Dict[str, Any]:
        """Get aggregated analytics for all flags in a tenant"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)

        # Get tenant flags
        tenant_flags = self.db.query(FeatureFlag).filter(
            (FeatureFlag.tenant_id == tenant_id) | (FeatureFlag.tenant_id.is_(None))
        ).all()

        tenant_analytics = {
            "tenant_id": tenant_id,
            "period_start": start_date,
            "period_end": end_date,
            "total_flags": len(tenant_flags),
            "enabled_flags": len([f for f in tenant_flags if f.enabled]),
            "experiments": len([f for f in tenant_flags if f.is_experiment]),
            "flag_analytics": []
        }

        for flag in tenant_flags:
            try:
                flag_analytics = await self.get_flag_analytics(flag.key, period_days)
                tenant_analytics["flag_analytics"].append(flag_analytics.dict())
            except Exception as e:
                logger.error("tenant_flag_analytics_failed",
                           tenant_id=tenant_id,
                           flag_key=flag.key,
                           error=str(e))

        return tenant_analytics
