"""Tests for experiment aggregation and metadata output."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from optimize.experiments.aggregate import build_seed_rows, build_summary_rows
from optimize.experiments.models import ExperimentConfig, RunResult
from optimize.experiments.runner import ExperimentRunner
from optimize.types import RunStatus, StopReason


def _sample_result(
    algorithm: str,
    seed: int,
    objective: float,
    gap: float | None = None,
) -> RunResult:
    best_solution = {"distance": objective}
    if gap is not None:
        best_solution["gap_percentage"] = gap
    return RunResult(
        experiment_name="test_exp",
        run_id=f"{algorithm}_run_001",
        algorithm=algorithm,
        domain="tsp",
        instance="eil51",
        seed=seed,
        status=RunStatus.COMPLETED,
        stop_reason=StopReason.EVALUATION_BUDGET,
        initial_objective=objective + 100,
        best_objective=objective,
        final_objective=objective,
        runtime_seconds=1.0,
        objective_evaluations=1000,
        iterations=1000,
        parameters={"x": 1},
        best_solution=best_solution,
    )


def test_build_seed_rows() -> None:
    config = ExperimentConfig(
        experiment_name="test",
        domain="mock",
        instance="sphere",
        algorithms=["mock_random_search", "simulated_annealing"],
        runs=2,
        evaluation_budget=100,
    )
    rows = build_seed_rows(config, [1000, 1001])
    assert len(rows) == 4
    assert rows[0] == {
        "run_id": "mock_random_search_run_001",
        "algorithm": "mock_random_search",
        "seed": 1000,
        "run_index": 1,
    }


def test_build_summary_rows() -> None:
    config = ExperimentConfig(
        experiment_name="test",
        domain="tsp",
        instance="eil51",
        instance_path="datasets/tsp/instances/eil51.tsp",
        algorithms=["simulated_annealing", "tabu_search"],
        runs=2,
        evaluation_budget=1000,
    )
    results = [
        _sample_result("simulated_annealing", 1000, 600.0, 40.8),
        _sample_result("simulated_annealing", 1001, 620.0, 45.5),
        _sample_result("tabu_search", 1000, 500.0, 17.4),
        _sample_result("tabu_search", 1001, 510.0, 19.7),
    ]
    for index, result in enumerate(results, start=1):
        result.run_id = f"{result.algorithm}_run_{index:03d}"

    rows = build_summary_rows(results, config)
    assert len(rows) == 2
    sa = next(row for row in rows if row["algorithm"] == "simulated_annealing")
    assert sa["successful_runs"] == 2
    assert sa["min_objective"] == 600.0
    assert sa["problem_size"] == 51
    assert sa["mean_gap_percentage"] == 43.15


def test_mock_run_writes_metadata(tmp_path: Path) -> None:
    config_path = tmp_path / "mock.json"
    output_dir = tmp_path / "out"
    config_path.write_text(
        json.dumps(
            {
                "experiment_name": "metadata_smoke",
                "domain": "mock",
                "instance": "sphere_5d",
                "algorithms": ["mock_random_search"],
                "runs": 2,
                "evaluation_budget": 50,
                "domain_config": {"dimension": 5},
                "output": {"directory": str(output_dir)},
            }
        ),
        encoding="utf-8",
    )

    experiment_dir = ExperimentRunner().run(config_path)

    assert (experiment_dir / "experiment_config.json").exists()
    assert (experiment_dir / "environment.json").exists()
    assert (experiment_dir / "seeds.csv").exists()
    assert (experiment_dir / "summary.csv").exists()
    assert (experiment_dir / "statistics.csv").exists()
    assert (experiment_dir / "logs" / "experiment.log").exists()

    try:
        import matplotlib  # noqa: F401

        assert (experiment_dir / "charts" / "convergence.png").exists()
    except ImportError:
        pass

    with (experiment_dir / "runs.csv").open(encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert row["parameters"].startswith("{")
