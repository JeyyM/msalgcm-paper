"""TSP domain and algorithm smoke tests."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from optimize.algorithms.registry import get_algorithm
from optimize.domains.registry import create_problem
from optimize.domains.tsp.distance import tour_length
from optimize.domains.tsp.loader import load_tsplib
from optimize.experiments.budget import EvaluationBudget
from optimize.experiments.runner import ExperimentRunner
from optimize.types import StopReason

ROOT = Path(__file__).resolve().parents[1]
EIL51 = ROOT / "datasets" / "tsp" / "instances" / "eil51.tsp"


def test_load_eil51() -> None:
    instance = load_tsplib(EIL51)
    assert instance.name == "eil51"
    assert instance.num_cities == 51


def test_tsp_known_optimum() -> None:
    budget = EvaluationBudget(10)
    problem = create_problem(
        "tsp",
        budget,
        {"instance_path": str(EIL51)},
    )
    assert problem.known_optimum == 426


def test_tsp_sa_smoke() -> None:
    budget = EvaluationBudget(500)
    problem = create_problem(
        "tsp",
        budget,
        {
            "instance_path": str(EIL51),
            "operators": ["swap", "two_opt"],
        },
    )
    algorithm = get_algorithm("simulated_annealing")
    algorithm.initialize(
        problem,
        {
            "initial_temperature": 100.0,
            "final_temperature": 0.1,
            "cooling_factor": 0.95,
            "moves_per_temperature": 10,
            "operators": ["swap", "two_opt"],
        },
        seed=42,
    )
    algorithm.run()
    assert algorithm.get_best_objective() < float("inf")
    assert algorithm.get_stop_reason() in {
        StopReason.COMPLETED,
        StopReason.EVALUATION_BUDGET,
    }


def test_tsp_runner_smoke(tmp_path: Path) -> None:
    config_path = tmp_path / "tsp_smoke.json"
    output_dir = tmp_path / "out"
    config_path.write_text(
        """
{
  "experiment_name": "tsp_smoke",
  "domain": "tsp",
  "instance": "eil51",
  "instance_path": "datasets/tsp/instances/eil51.tsp",
  "algorithms": ["simulated_annealing"],
  "runs": 1,
  "evaluation_budget": 200,
  "seed_policy": {"base_seed": 1},
  "domain_config": {"operators": ["swap", "two_opt"]},
  "algorithm_configs": {
    "simulated_annealing": {
      "initial_temperature": 50.0,
      "final_temperature": 0.1,
      "cooling_factor": 0.95,
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
    assert (result_dir / "seeds.csv").exists()


@pytest.mark.parametrize(
    ("operator",),
    [
        ("swap",),
        ("insertion",),
        ("inversion",),
        ("two_opt",),
    ],
)
def test_neighborhood_preserves_permutation(operator: str) -> None:
    from optimize.domains.tsp.neighborhoods import apply_operator

    rng = np.random.default_rng(0)
    route = list(range(10))
    neighbor = apply_operator(route, operator, rng)
    assert sorted(neighbor) == list(range(10))
