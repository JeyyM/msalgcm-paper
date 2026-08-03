"""Job-shop scheduling domain and algorithm smoke tests."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from optimize.algorithms.registry import get_algorithm
from optimize.domains.registry import create_problem
from optimize.domains.scheduling.jsp.decoder import compute_makespan, decode_schedule
from optimize.domains.scheduling.jsp.loader import load_jsp
from optimize.experiments.budget import EvaluationBudget
from optimize.experiments.runner import ExperimentRunner
from optimize.types import StopReason

ROOT = Path(__file__).resolve().parents[1]
FT10 = ROOT / "datasets" / "scheduling" / "jsp" / "instances" / "ft10.txt"


def test_load_ft10() -> None:
    instance = load_jsp(FT10)
    assert instance.name == "ft10"
    assert instance.num_jobs == 10
    assert instance.num_machines == 10
    assert instance.num_operations == 100


def test_jsp_known_optimum() -> None:
    budget = EvaluationBudget(10)
    problem = create_problem(
        "scheduling",
        budget,
        {"instance_path": str(FT10)},
    )
    assert problem.known_optimum == 930


def test_jsp_validity_and_decoder() -> None:
    budget = EvaluationBudget(10)
    problem = create_problem(
        "scheduling",
        budget,
        {"instance_path": str(FT10)},
    )
    rng = np.random.default_rng(0)
    sequence = problem.create_initial_solution(rng)
    assert problem.is_valid(sequence)
    schedule = decode_schedule(problem.instance, sequence)
    assert schedule.makespan == compute_makespan(problem.instance, sequence)
    assert len(schedule.operations) == problem.instance.num_operations


@pytest.mark.parametrize(
    ("operator",),
    [
        ("swap",),
        ("insertion",),
        ("inversion",),
    ],
)
def test_jsp_neighborhood_preserves_counts(operator: str) -> None:
    from optimize.domains.scheduling.jsp.neighborhoods import apply_operator

    rng = np.random.default_rng(0)
    sequence = [job for job in range(10) for _ in range(10)]
    neighbor = apply_operator(sequence, operator, rng)
    assert Counter(neighbor) == Counter(sequence)


def test_jsp_sa_smoke() -> None:
    budget = EvaluationBudget(1000)
    problem = create_problem(
        "scheduling",
        budget,
        {
            "instance_path": str(FT10),
            "operators": ["swap", "insertion", "inversion"],
            "initial_solution": "longest_processing_time",
        },
    )
    algorithm = get_algorithm("simulated_annealing")
    algorithm.initialize(
        problem,
        {
            "initial_temperature": 500.0,
            "final_temperature": 0.1,
            "cooling_factor": 0.95,
            "moves_per_temperature": 20,
            "operators": ["swap", "insertion", "inversion"],
        },
        seed=42,
    )
    algorithm.run()
    assert algorithm.get_best_objective() < float("inf")
    assert algorithm.get_stop_reason() in {
        StopReason.COMPLETED,
        StopReason.EVALUATION_BUDGET,
    }


def test_jsp_runner_smoke(tmp_path: Path) -> None:
    config_path = tmp_path / "jsp_smoke.json"
    output_dir = tmp_path / "out"
    config_path.write_text(
        """
{
  "experiment_name": "jsp_smoke",
  "domain": "scheduling",
  "instance": "ft10",
  "instance_path": "datasets/scheduling/jsp/instances/ft10.txt",
  "algorithms": ["simulated_annealing"],
  "runs": 1,
  "evaluation_budget": 500,
  "seed_policy": {"base_seed": 1},
  "domain_config": {
    "initial_solution": "longest_processing_time",
    "operators": ["swap", "insertion", "inversion"]
  },
  "algorithm_configs": {
    "simulated_annealing": {
      "initial_temperature": 200.0,
      "final_temperature": 0.1,
      "cooling_factor": 0.95,
      "moves_per_temperature": 10
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
