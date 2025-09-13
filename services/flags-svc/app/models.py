from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=False)

    # Rollout configuration
    rollout_percentage = Column(Float, default=0.0)  # 0-100

    # Targeting configuration
    targeting_rules = Column(JSON, default=dict)  # role, region, grade_band filters

    # Tenant scoping
    tenant_id = Column(String, index=True)  # null for global flags

    # Experiment configuration
    is_experiment = Column(Boolean, default=False)
    experiment_id = Column(String, index=True)

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String)

    # Relationships
    exposures = relationship("FlagExposure", back_populates="flag")
    experiments = relationship("Experiment", back_populates="flag")

class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String, unique=True, index=True, nullable=False)
    flag_id = Column(Integer, ForeignKey("feature_flags.id"))

    name = Column(String, nullable=False)
    description = Column(Text)
    hypothesis = Column(Text)

    # Experiment configuration
    variants = Column(JSON, default=list)  # [{"name": "control", "weight": 50}, {"name": "treatment", "weight": 50}]
    success_metrics = Column(JSON, default=list)  # metrics to track

    # Status
    status = Column(String, default="draft")  # draft, running, paused, completed

    # Timeline
    start_date = Column(DateTime)
    end_date = Column(DateTime)

    # Results
    results = Column(JSON, default=dict)
    statistical_significance = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String)

    # Relationships
    flag = relationship("FeatureFlag", back_populates="experiments")
    exposures = relationship("FlagExposure", back_populates="experiment")

class FlagExposure(Base):
    __tablename__ = "flag_exposures"

    id = Column(Integer, primary_key=True, index=True)
    flag_id = Column(Integer, ForeignKey("feature_flags.id"))
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=True)

    # User context
    user_id = Column(String, index=True)
    tenant_id = Column(String, index=True)
    session_id = Column(String, index=True)

    # User attributes for targeting
    user_role = Column(String)
    user_region = Column(String)
    user_grade_band = Column(String)

    # Evaluation result
    flag_key = Column(String, index=True)
    variant = Column(String)  # For experiments
    evaluated_value = Column(Boolean)

    # Context
    evaluation_context = Column(JSON, default=dict)

    # Timestamp
    exposed_at = Column(DateTime, default=func.now())

    # Relationships
    flag = relationship("FeatureFlag", back_populates="exposures")
    experiment = relationship("Experiment", back_populates="exposures")

# Indexes for performance
Index('idx_flag_exposures_flag_time', FlagExposure.flag_id, FlagExposure.exposed_at)
Index('idx_flag_exposures_user_time', FlagExposure.user_id, FlagExposure.exposed_at)
Index('idx_flag_exposures_experiment_time', FlagExposure.experiment_id, FlagExposure.exposed_at)
