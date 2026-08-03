"""Load and validate experiment configuration files."""

from __future__ import annotations

import json
from pathlib import Path

from optimize.experiments.models import ExperimentConfig


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"config not found: {config_path}")

    with config_path.open(encoding="utf-8") as handle:
        raw = json.load(handle)

    return ExperimentConfig.model_validate(raw)


def validate_experiment_config(config: ExperimentConfig) -> list[str]:
    """Return a list of validation errors (empty if valid)."""
    errors: list[str] = []

    if config.runs <= 0:
        errors.append("runs must be positive")
    if config.evaluation_budget <= 0:
        errors.append("evaluation_budget must be positive")
    if not config.algorithms:
        errors.append("at least one algorithm must be selected")

    if config.domain == "feature_selection":
        if "performance_weight" not in config.domain_config:
            errors.append("feature_selection requires domain_config.performance_weight")
        if "reduction_weight" not in config.domain_config:
            errors.append("feature_selection requires domain_config.reduction_weight")
        if not config.instance_path:
            errors.append("feature_selection requires instance_path")

    return errors
