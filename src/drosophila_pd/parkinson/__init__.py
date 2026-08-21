"""Computational Parkinson phenotype analysis over existing rollout outputs.

This package is a post-processing layer. It does not run simulations, define
clinical thresholds, or establish biological Parkinson disease validity.
"""

from .model import (
    COMPUTATIONAL_SCOPE,
    MOTOR_FEATURE_NAMES,
    ComputationalPDIndex,
    ParkinsonMotorConfig,
    ParkinsonMotorModel,
    build_behavior_model,
    extract_motor_features,
)
from .validation import (
    bootstrap_confidence_interval,
    compare_feature_sets,
    feature_ablation,
    correlation_matrix,
    cross_validate_index,
    leave_one_out_feature_validation,
    outlier_sensitivity,
    validate_computational_report,
)
from .comparison import compare_computational_reports
from .report import generate_computational_pd_report, render_markdown_report

__all__ = [
    "COMPUTATIONAL_SCOPE",
    "MOTOR_FEATURE_NAMES",
    "ComputationalPDIndex",
    "ParkinsonMotorConfig",
    "compare_computational_reports",
    "ParkinsonMotorModel",
    "bootstrap_confidence_interval",
    "build_behavior_model",
    "compare_feature_sets",
    "extract_motor_features",
    "feature_ablation",
    "correlation_matrix",
    "cross_validate_index",
    "leave_one_out_feature_validation",
    "outlier_sensitivity",
    "generate_computational_pd_report",
    "render_markdown_report",
    "validate_computational_report",
]
