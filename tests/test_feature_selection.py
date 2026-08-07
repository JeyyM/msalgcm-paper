"""Feature-selection domain and algorithm tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

pytest.importorskip("sklearn")

from optimize.algorithms.registry import get_algorithm
from optimize.config.loader import load_experiment_config, validate_experiment_config
from optimize.domains.feature_selection.evaluator import FeatureSubsetEvaluator
from optimize.domains.feature_selection.loader import load_ew_dataset
from optimize.domains.registry import create_problem
from optimize.experiments.budget import EvaluationBudget
from optimize.experiments.runner import ExperimentRunner
from optimize.types import StopReason

ROOT = Path(__file__).resolve().parents[1]
BREASTEW = ROOT / "datasets" / "feature_selection" / "ew" / "BreastEW.csv"
WINEEW = ROOT / "datasets" / "feature_selection" / "ew" / "WineEW.csv"


def test_load_breastew() -> None:
    dataset = load_ew_dataset(BREASTEW)
    assert dataset.name == "BreastEW"
    assert dataset.num_features == 30
    assert dataset.num_samples == 569


def test_fs_requires_explicit_weights() -> None:
    budget = EvaluationBudget(10)
    with pytest.raises(ValueError, match="performance_weight"):
        create_problem(
            "feature_selection",
            budget,
            {"instance_path": str(BREASTEW)},
        )


def test_validate_fs_config_requires_weights() -> None:
    config = load_experiment_config(ROOT / "config" / "examples" / "fs_breastew_smoke.json")
    errors = validate_experiment_config(config)
    assert errors == []


def test_fs_repair_and_validity() -> None:
    budget = EvaluationBudget(10)
    problem = create_problem(
        "feature_selection",
        budget,
        {
            "instance_path": str(BREASTEW),
            "performance_weight": 0.9,
            "reduction_weight": 0.1,
            "split_seed": 42,
        },
    )
    mask = [0] * problem.dataset.num_features
    repaired = problem.repair(mask, np.random.default_rng(0))
    assert problem.is_valid(repaired)
    assert sum(repaired) >= 1


def test_fs_evaluator_uses_training_only_for_cv() -> None:
    dataset = load_ew_dataset(BREASTEW)
    evaluator = FeatureSubsetEvaluator.from_dataset(
        dataset,
        test_size=0.3,
        split_seed=7,
        k_neighbors=3,
        cv_folds=3,
    )
    mask = [1] * dataset.num_features

    original_test = evaluator.X_test.copy()

    with patch.object(evaluator, "X_test", evaluator.X_test) as mocked_test:
        evaluator.cross_validation_loss(mask)
        assert np.array_equal(mocked_test, original_test)


def test_fs_evaluator_standardization_scales_features() -> None:
    dataset = load_ew_dataset(BREASTEW)
    evaluator = FeatureSubsetEvaluator.from_dataset(
        dataset,
        test_size=0.3,
        split_seed=7,
        k_neighbors=3,
        cv_folds=3,
        standardize_features=True,
    )
    raw = np.array([[1.0, 1000.0], [2.0, 2000.0], [3.0, 3000.0]])
    scaled, _ = evaluator._scale_train_test(raw, raw[:1])
    assert not np.allclose(raw, scaled)
    assert np.isclose(scaled[:, 0].std(), 1.0, atol=1e-6)


def test_fs_default_weights_are_literature_aligned() -> None:
    config = load_experiment_config(ROOT / "config" / "examples" / "fs_breastew_comparison.json")
    assert config.domain_config["performance_weight"] == 0.99
    assert config.domain_config["reduction_weight"] == 0.01
    assert config.domain_config.get("standardize_features", True) is True


def test_fs_sa_smoke() -> None:
    budget = EvaluationBudget(50)
    problem = create_problem(
        "feature_selection",
        budget,
        {
            "instance_path": str(BREASTEW),
            "performance_weight": 0.99,
            "reduction_weight": 0.01,
            "standardize_features": True,
            "split_seed": 11,
            "operators": ["flip", "swap"],
        },
    )
    algorithm = get_algorithm("simulated_annealing")
    algorithm.initialize(
        problem,
        {
            "initial_temperature": 1.0,
            "final_temperature": 0.05,
            "cooling_factor": 0.9,
            "moves_per_temperature": 5,
            "operators": ["flip", "swap"],
        },
        seed=42,
    )
    algorithm.run()
    assert algorithm.get_best_objective() < float("inf")
    assert algorithm.get_stop_reason() in {
        StopReason.COMPLETED,
        StopReason.EVALUATION_BUDGET,
    }
    solution = algorithm.get_best_solution()
    assert solution is not None
    payload = problem.serialize_solution(solution)
    assert 0 < payload["selected_feature_count"] <= problem.dataset.num_features
    assert "test_score" in payload


def test_fs_pso_smoke() -> None:
    """Regression test: PSO previously crashed on every FS run with
    "unable to infer PSO dimension from problem" because FeatureSelectionProblem
    exposed neither `.instance` nor `.dimension` — ParticleSwarmOptimization._infer_dimension
    had nothing to fall back on. Fixed by adding a `dimension` property. This test
    would have caught it: no FS+PSO smoke test existed before."""
    budget = EvaluationBudget(60)
    problem = create_problem(
        "feature_selection",
        budget,
        {
            "instance_path": str(BREASTEW),
            "performance_weight": 0.99,
            "reduction_weight": 0.01,
            "standardize_features": True,
            "split_seed": 11,
            "operators": ["flip", "swap"],
        },
    )
    algorithm = get_algorithm("particle_swarm")
    algorithm.initialize(
        problem,
        {
            "swarm_size": 5,
            "inertia_weight": 0.7,
            "cognitive_coefficient": 1.5,
            "social_coefficient": 1.5,
        },
        seed=42,
    )
    algorithm.run()
    assert algorithm.get_best_objective() < float("inf")
    assert algorithm.get_stop_reason() in {
        StopReason.COMPLETED,
        StopReason.EVALUATION_BUDGET,
    }
    solution = algorithm.get_best_solution()
    assert solution is not None
    payload = problem.serialize_solution(solution)
    assert 0 < payload["selected_feature_count"] <= problem.dataset.num_features


def test_fs_runner_smoke(tmp_path: Path) -> None:
    config_path = tmp_path / "fs_smoke.json"
    output_dir = tmp_path / "out"
    config_path.write_text(
        """
{
  "experiment_name": "fs_smoke",
  "domain": "feature_selection",
  "instance": "BreastEW",
  "instance_path": "datasets/feature_selection/ew/BreastEW.csv",
  "algorithms": ["simulated_annealing"],
  "runs": 1,
  "evaluation_budget": 30,
  "seed_policy": {"base_seed": 99},
  "domain_config": {
    "performance_weight": 0.9,
    "reduction_weight": 0.1,
    "operators": ["flip", "swap"]
  },
  "algorithm_configs": {
    "simulated_annealing": {
      "initial_temperature": 1.0,
      "final_temperature": 0.05,
      "cooling_factor": 0.9,
      "moves_per_temperature": 5
    }
  },
  "output": {"directory": "%s"}
}
"""
        % output_dir.as_posix(),
        encoding="utf-8",
    )

    runner = ExperimentRunner()
    result_dir = runner.run(config_path)
    assert (result_dir / "runs.csv").exists()
    assert (result_dir / "summary.csv").exists()
