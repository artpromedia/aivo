from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List
import structlog

from ..models import FeatureFlag, Experiment
from ..schemas import (
    FeatureFlagCreate, FeatureFlagUpdate,
    ExperimentCreate, ExperimentUpdate
)

logger = structlog.get_logger()

class FlagService:
    def __init__(self, db: Session):
        self.db = db

    def create_flag(self, flag_data: FeatureFlagCreate) -> FeatureFlag:
        """Create a new feature flag"""
        # Convert targeting rules to dict if provided
        targeting_rules = {}
        if flag_data.targeting_rules:
            targeting_rules = flag_data.targeting_rules.dict()

        flag = FeatureFlag(
            key=flag_data.key,
            name=flag_data.name,
            description=flag_data.description,
            enabled=flag_data.enabled,
            rollout_percentage=flag_data.rollout_percentage,
            targeting_rules=targeting_rules,
            tenant_id=flag_data.tenant_id,
            is_experiment=flag_data.is_experiment,
            experiment_id=flag_data.experiment_id,
            created_by="system"  # TODO: Get from auth context
        )

        self.db.add(flag)
        self.db.commit()
        self.db.refresh(flag)

        return flag

    def update_flag(self, flag: FeatureFlag, flag_data: FeatureFlagUpdate) -> FeatureFlag:
        """Update an existing feature flag"""
        update_data = flag_data.dict(exclude_unset=True)

        # Handle targeting rules conversion
        if "targeting_rules" in update_data and update_data["targeting_rules"]:
            update_data["targeting_rules"] = update_data["targeting_rules"].dict()

        for field, value in update_data.items():
            setattr(flag, field, value)

        flag.updated_at = func.now()
        self.db.commit()
        self.db.refresh(flag)

        return flag

    def delete_flag(self, flag: FeatureFlag):
        """Delete a feature flag and associated data"""
        # TODO: Consider soft delete for audit purposes
        self.db.delete(flag)
        self.db.commit()

    def create_experiment(self, experiment_data: ExperimentCreate) -> Experiment:
        """Create a new experiment"""
        # Validate variant weights sum to 100
        total_weight = sum(variant.weight for variant in experiment_data.variants)
        if abs(total_weight - 100.0) > 0.01:  # Allow small floating point errors
            raise ValueError("Variant weights must sum to 100")

        # Convert variants to dict format
        variants = [variant.dict() for variant in experiment_data.variants]

        experiment = Experiment(
            experiment_id=experiment_data.experiment_id,
            flag_id=experiment_data.flag_id,
            name=experiment_data.name,
            description=experiment_data.description,
            hypothesis=experiment_data.hypothesis,
            variants=variants,
            success_metrics=experiment_data.success_metrics,
            start_date=experiment_data.start_date,
            end_date=experiment_data.end_date,
            status="draft",
            created_by="system"  # TODO: Get from auth context
        )

        self.db.add(experiment)
        self.db.commit()
        self.db.refresh(experiment)

        return experiment

    def update_experiment(self, experiment: Experiment, experiment_data: ExperimentUpdate) -> Experiment:
        """Update an existing experiment"""
        update_data = experiment_data.dict(exclude_unset=True)

        # Handle variants conversion
        if "variants" in update_data and update_data["variants"]:
            variants = [variant.dict() for variant in update_data["variants"]]
            # Validate weights
            total_weight = sum(variant["weight"] for variant in variants)
            if abs(total_weight - 100.0) > 0.01:
                raise ValueError("Variant weights must sum to 100")
            update_data["variants"] = variants

        for field, value in update_data.items():
            setattr(experiment, field, value)

        experiment.updated_at = func.now()
        self.db.commit()
        self.db.refresh(experiment)

        return experiment

    def start_experiment(self, experiment: Experiment) -> Experiment:
        """Start an experiment (change status to running)"""
        if experiment.status != "draft":
            raise ValueError("Only draft experiments can be started")

        experiment.status = "running"
        if not experiment.start_date:
            experiment.start_date = func.now()

        self.db.commit()
        self.db.refresh(experiment)

        return experiment

    def stop_experiment(self, experiment: Experiment) -> Experiment:
        """Stop an experiment (change status to completed)"""
        if experiment.status != "running":
            raise ValueError("Only running experiments can be stopped")

        experiment.status = "completed"
        if not experiment.end_date:
            experiment.end_date = func.now()

        self.db.commit()
        self.db.refresh(experiment)

        return experiment
