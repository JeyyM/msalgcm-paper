"""Tests for TSP one-batch-per-pair catalog behavior."""

from __future__ import annotations

import csv
from pathlib import Path

from optimize.api.services.tsp_catalog import (
    TSP_RUNS,
    get_tsp_batch,
    list_tsp_runs,
    prepare_tsp_launch,
    prune_duplicate_tsp_experiments,
    tsp_completion_status,
)


def _write_batch(tmp_path: Path, experiment_id: str, instance: str, algorithm: str, completed: int) -> None:
    exp = tmp_path / experiment_id
    exp.mkdir(parents=True)
    (exp / "experiment_config.json").write_text(
        f"""{{
  "config": {{
    "experiment_name": "tsp_{instance}_{algorithm}",
    "domain": "tsp",
    "instance": "{instance}",
    "algorithms": ["{algorithm}"],
    "runs": {TSP_RUNS}
  }}
}}""",
        encoding="utf-8",
    )
    rows = []
    for index in range(1, completed + 1):
        rows.append(
            {
                "run_id": f"{algorithm}_run_{index:03d}",
                "algorithm": algorithm,
                "domain": "tsp",
                "instance": instance,
                "status": "completed",
                "best_objective": "100.0",
                "runtime_seconds": "1.0",
            }
        )
    with (exp / "runs.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_prune_keeps_latest_complete_batch(tmp_path: Path) -> None:
    _write_batch(tmp_path, "2026-08-06_100000_tsp_eil51_simulated_annealing", "eil51", "simulated_annealing", 30)
    _write_batch(tmp_path, "2026-08-06_110000_tsp_eil51_simulated_annealing", "eil51", "simulated_annealing", 30)
    _write_batch(tmp_path, "2026-08-06_120000_tsp_eil51_simulated_annealing", "eil51", "simulated_annealing", 5)

    removed = prune_duplicate_tsp_experiments(tmp_path)
    assert len(removed) == 2
    assert (tmp_path / "2026-08-06_110000_tsp_eil51_simulated_annealing").exists()
    assert not (tmp_path / "2026-08-06_100000_tsp_eil51_simulated_annealing").exists()
    assert not (tmp_path / "2026-08-06_120000_tsp_eil51_simulated_annealing").exists()


def test_list_tsp_runs_uses_canonical_batch_only(tmp_path: Path) -> None:
    _write_batch(tmp_path, "2026-08-06_100000_tsp_eil51_simulated_annealing", "eil51", "simulated_annealing", 30)
    _write_batch(tmp_path, "2026-08-06_110000_tsp_eil51_simulated_annealing", "eil51", "simulated_annealing", 30)

    rows = list_tsp_runs("eil51", "simulated_annealing", results_dir=tmp_path)
    assert len(rows) == 30
    assert all(row["experiment_id"] == "2026-08-06_110000_tsp_eil51_simulated_annealing" for row in rows)


def test_prepare_launch_replaces_complete_batch(tmp_path: Path) -> None:
    complete = "2026-08-06_110000_tsp_eil51_simulated_annealing"
    _write_batch(tmp_path, complete, "eil51", "simulated_annealing", 30)

    prepare_tsp_launch("eil51", "simulated_annealing", results_dir=tmp_path)
    assert not (tmp_path / complete).exists()
    assert get_tsp_batch("eil51", "simulated_annealing", results_dir=tmp_path) is None


def test_prepare_launch_removes_incomplete_batch(tmp_path: Path) -> None:
    incomplete = "2026-08-06_120000_tsp_eil51_simulated_annealing"
    _write_batch(tmp_path, incomplete, "eil51", "simulated_annealing", 4)

    prepare_tsp_launch("eil51", "simulated_annealing", results_dir=tmp_path)
    assert not (tmp_path / incomplete).exists()


def test_completion_status_reports_single_batch(tmp_path: Path) -> None:
    _write_batch(tmp_path, "2026-08-06_110000_tsp_eil51_simulated_annealing", "eil51", "simulated_annealing", 30)
    status = tsp_completion_status(tmp_path)
    entry = status["completion"]["eil51"]["simulated_annealing"]
    assert entry["completed_runs"] == 30
    assert entry["done"] is True
    assert entry["can_launch"] is True
    assert entry["successful_runs"] == 30
    assert entry["best_objective"] == 100.0
