"""API tests for the dashboard backend."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from optimize.api.app import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_experiments() -> None:
    response = client.get("/api/experiments")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_dashboard() -> None:
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    payload = response.json()
    assert "experiments" in payload
    assert "studies" in payload


def test_tsp_catalog() -> None:
    response = client.get("/api/domains/tsp")
    assert response.status_code == 200
    payload = response.json()
    assert payload["runs_per_experiment"] == 30
    assert len(payload["algorithms"]) == 3
    entry = payload["completion"]["eil51"]["simulated_annealing"]
    assert "completed_runs" in entry
    assert "target_runs" in entry
    assert "can_launch" in entry
    assert "experiment_id" in entry


def test_tsp_instance_geometry() -> None:
    response = client.get("/api/domains/tsp/instances/eil51/geometry")
    assert response.status_code == 200
    payload = response.json()
    assert payload["num_cities"] == 51
    assert len(payload["coordinates"]) == 51


def test_live_solution_query_param(tmp_path: Path) -> None:
    from optimize.api.services import results_reader

    experiment_id = "test_exp_live"
    run_id = "simulated_annealing_run_001"
    solutions_dir = tmp_path / experiment_id / "solutions"
    solutions_dir.mkdir(parents=True)
    live_payload = {
        "live": True,
        "objective_evaluations": 42,
        "current": {"route": [0, 1, 2], "distance": 123.0},
    }
    (solutions_dir / f"{run_id}.live.json").write_text(json.dumps(live_payload), encoding="utf-8")

    original_root = results_reader.results_root
    results_reader.results_root = lambda: tmp_path  # type: ignore[method-assign]
    try:
        response = client.get(f"/api/experiments/{experiment_id}/solutions/{run_id}?live=true")
        live_route = client.get(f"/api/experiments/{experiment_id}/solutions/{run_id}/live")
    finally:
        results_reader.results_root = original_root  # type: ignore[method-assign]

    assert response.status_code == 200
    assert response.json()["objective_evaluations"] == 42
    assert live_route.status_code == 200
    assert live_route.json()["current"]["route"] == [0, 1, 2]


def test_build_tsp_config() -> None:
    from optimize.api.services.tsp_catalog import build_tsp_config

    config = build_tsp_config("eil51", "tabu_search")
    assert config.instance == "eil51"
    assert config.algorithms == ["tabu_search"]
    assert config.runs == 30
