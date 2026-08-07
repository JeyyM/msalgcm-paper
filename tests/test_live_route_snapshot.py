"""Tests for live route snapshot writing."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

from optimize.experiments.runner import ExperimentRunner
from optimize.storage.writer import write_live_route_snapshot

ROOT = Path(__file__).resolve().parents[1]
EIL51 = ROOT / "datasets" / "tsp" / "instances" / "eil51.tsp"


def test_write_live_route_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "solutions" / "run_001.live.json"
    problem = Mock()
    problem.serialize_solution.return_value = {"route": [0, 1, 2], "distance": 99.0}
    algorithm = Mock()
    algorithm.get_current_solution.return_value = [0, 1, 2]

    write_live_route_snapshot(path, problem, algorithm, 123)

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["objective_evaluations"] == 123
    assert payload["current"]["route"] == [0, 1, 2]


def test_live_route_snapshot_tracks_evaluations(tmp_path: Path) -> None:
    live_path = tmp_path / "simulated_annealing_run_001.live.json"
    result = ExperimentRunner().run_single(
        algorithm_name="simulated_annealing",
        problem_domain="tsp",
        instance="eil51",
        seed=1,
        evaluation_budget=200,
        domain_config={
            "instance": "eil51",
            "instance_path": str(EIL51),
            "operators": ["swap", "two_opt"],
        },
        live_solution_path=live_path,
    )
    payload = json.loads(live_path.read_text(encoding="utf-8"))

    assert result.objective_evaluations == 200
    assert payload["objective_evaluations"] == 200
    assert len(payload["current"]["route"]) == 51
