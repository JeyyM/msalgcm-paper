"""Tests for experiment chart generation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from optimize.experiments.models import ExperimentConfig, HistoryRecord, RunResult
from optimize.experiments.runner import ExperimentRunner
from optimize.types import RunStatus, StopReason
from optimize.visualization.charts import (
    _mean_convergence_curve,
    generate_experiment_charts,
)

matplotlib = pytest.importorskip("matplotlib")


def _history(evaluations: list[int], start: float, end: float) -> list[HistoryRecord]:
    if len(evaluations) == 1:
        return [HistoryRecord(objective_evaluations=evaluations[0], best_objective=end)]
    step = (start - end) / (len(evaluations) - 1)
    records = []
    for index, evaluation in enumerate(evaluations):
        best = start - step * index
        records.append(
            HistoryRecord(
                objective_evaluations=evaluation,
                best_objective=best,
                current_objective=best,
                iteration=index,
            )
        )
    return records


def test_mean_convergence_curve_averages_runs() -> None:
    run_a = ([10, 20, 30], [100.0, 80.0, 60.0])
    run_b = ([10, 20, 30], [120.0, 90.0, 70.0])
    x_values, y_values = _mean_convergence_curve([run_a, run_b], budget=30, n_bins=3)
    assert x_values == [0, 10, 20, 30]
    assert y_values[0] == pytest.approx(110.0)
    assert y_values[-1] == pytest.approx(65.0)


def test_generate_charts_for_mock_run(tmp_path: Path) -> None:
    config = ExperimentConfig(
        experiment_name="chart_smoke",
        domain="mock",
        instance="sphere_5d",
        algorithms=["mock_random_search"],
        runs=2,
        evaluation_budget=20,
    )
    results = [
        RunResult(
            experiment_name="chart_smoke",
            run_id="mock_random_search_run_001",
            algorithm="mock_random_search",
            domain="mock",
            instance="sphere_5d",
            seed=1,
            status=RunStatus.COMPLETED,
            stop_reason=StopReason.EVALUATION_BUDGET,
            initial_objective=4.0,
            best_objective=1.0,
            final_objective=1.0,
            runtime_seconds=0.1,
            objective_evaluations=20,
            iterations=19,
            history=_history(list(range(1, 21)), start=4.0, end=1.0),
        ),
        RunResult(
            experiment_name="chart_smoke",
            run_id="mock_random_search_run_002",
            algorithm="mock_random_search",
            domain="mock",
            instance="sphere_5d",
            seed=2,
            status=RunStatus.COMPLETED,
            stop_reason=StopReason.EVALUATION_BUDGET,
            initial_objective=3.0,
            best_objective=0.5,
            final_objective=0.5,
            runtime_seconds=0.2,
            objective_evaluations=20,
            iterations=19,
            history=_history(list(range(1, 21)), start=3.0, end=0.5),
        ),
    ]

    experiment_dir = tmp_path / "experiment"
    experiment_dir.mkdir()
    chart_paths = generate_experiment_charts(experiment_dir, results, config)

    assert (experiment_dir / "charts" / "convergence.png").exists()
    assert (experiment_dir / "charts" / "objective_boxplot.png").exists()
    assert (experiment_dir / "charts" / "runtime_comparison.png").exists()
    assert len(chart_paths) >= 4


def test_runner_generates_charts(tmp_path: Path) -> None:
    config_path = tmp_path / "mock.json"
    output_dir = tmp_path / "out"
    config_path.write_text(
        json.dumps(
            {
                "experiment_name": "chart_runner_smoke",
                "domain": "mock",
                "instance": "sphere_5d",
                "algorithms": ["mock_random_search"],
                "runs": 1,
                "evaluation_budget": 30,
                "domain_config": {"dimension": 5},
                "output": {"directory": str(output_dir)},
            }
        ),
        encoding="utf-8",
    )

    experiment_dir = ExperimentRunner().run(config_path)
    charts_dir = experiment_dir / "charts"
    assert charts_dir.exists()
    assert (charts_dir / "convergence.png").exists()
    log_text = (experiment_dir / "logs" / "experiment.log").read_text(encoding="utf-8")
    assert "charts=" in log_text
