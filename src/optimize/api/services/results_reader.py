"""Read experiment and study artifacts from the results directory."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    return Path.cwd()


def results_root() -> Path:
    return _project_root() / "results"


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _parse_json_field(value: str) -> Any:
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _experiment_meta(experiment_dir: Path) -> dict[str, Any]:
    config_payload: dict[str, Any] = {}
    config_path = experiment_dir / "experiment_config.json"
    if config_path.exists():
        config_payload = json.loads(config_path.read_text(encoding="utf-8"))

    runs = _read_csv(experiment_dir / "runs.csv")
    name = experiment_dir.name
    parts = name.split("_", 2)
    experiment_name = parts[2] if len(parts) >= 3 else name

    domain = runs[0]["domain"] if runs else config_payload.get("config", {}).get("domain")
    instance = runs[0]["instance"] if runs else config_payload.get("config", {}).get("instance")

    return {
        "id": experiment_dir.name,
        "path": str(experiment_dir),
        "type": "experiment",
        "name": experiment_name,
        "domain": domain,
        "instance": instance,
        "run_count": len(runs),
        "completed_runs": sum(1 for row in runs if row.get("status") == "completed"),
        "modified_at": experiment_dir.stat().st_mtime,
    }


def list_experiments(results_dir: Path | None = None) -> list[dict[str, Any]]:
    root = results_dir or results_root()
    if not root.exists():
        return []

    items: list[dict[str, Any]] = []
    for path in sorted(root.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True):
        if not path.is_dir():
            continue
        if (path / "study_manifest.json").exists():
            continue
        if not (path / "runs.csv").exists():
            continue
        items.append(_experiment_meta(path))
    return items


def list_studies(results_dir: Path | None = None) -> list[dict[str, Any]]:
    root = results_dir or results_root()
    if not root.exists():
        return []

    items: list[dict[str, Any]] = []
    for path in sorted(root.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True):
        if not path.is_dir():
            continue
        manifest_path = path / "study_manifest.json"
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        items.append(
            {
                "id": path.name,
                "path": str(path),
                "type": "study",
                "name": manifest.get("study_name", path.name),
                "instance_count": len(manifest.get("experiments", [])),
                "modified_at": path.stat().st_mtime,
            }
        )
    return items


def get_experiment_detail(experiment_id: str, results_dir: Path | None = None) -> dict[str, Any]:
    root = results_dir or results_root()
    experiment_dir = root / experiment_id
    if not experiment_dir.exists():
        raise FileNotFoundError(f"experiment not found: {experiment_id}")

    runs_raw = _read_csv(experiment_dir / "runs.csv")
    runs = []
    for row in runs_raw:
        item = dict(row)
        item["parameters"] = _parse_json_field(row.get("parameters", ""))
        runs.append(item)

    summary = _read_csv(experiment_dir / "summary.csv")
    statistics = _read_csv(experiment_dir / "statistics.csv")

    config_payload = {}
    config_path = experiment_dir / "experiment_config.json"
    if config_path.exists():
        config_payload = json.loads(config_path.read_text(encoding="utf-8"))

    charts_dir = experiment_dir / "charts"
    charts = sorted(chart.name for chart in charts_dir.glob("*.png")) if charts_dir.exists() else []

    return {
        **_experiment_meta(experiment_dir),
        "config": config_payload,
        "summary": summary,
        "statistics": statistics,
        "runs": runs,
        "charts": charts,
    }


def get_study_detail(study_id: str, results_dir: Path | None = None) -> dict[str, Any]:
    root = results_dir or results_root()
    study_dir = root / study_id
    if not study_dir.exists():
        raise FileNotFoundError(f"study not found: {study_id}")

    manifest = json.loads((study_dir / "study_manifest.json").read_text(encoding="utf-8"))
    scalability = _read_csv(study_dir / "scalability_summary.csv")
    charts_dir = study_dir / "charts"
    charts = sorted(chart.name for chart in charts_dir.glob("*.png")) if charts_dir.exists() else []

    return {
        "id": study_dir.name,
        "path": str(study_dir),
        "type": "study",
        "name": manifest.get("study_name", study_dir.name),
        "manifest": manifest,
        "scalability_summary": scalability,
        "charts": charts,
    }


def _downsample_convergence(rows: list[dict[str, Any]], max_points: int) -> list[dict[str, Any]]:
    """Keep first/last points, best-improvement steps, then uniform fill up to max_points."""
    if max_points <= 0 or len(rows) <= max_points:
        return rows

    keep: set[int] = {0, len(rows) - 1}
    best = float("inf")
    for index, row in enumerate(rows):
        value = float(row["best_objective"])
        if value < best - 1e-9:
            best = value
            keep.add(index)

    remaining = max_points - len(keep)
    if remaining > 0:
        step = max(1, len(rows) // remaining)
        for index in range(0, len(rows), step):
            keep.add(index)

    ordered = sorted(keep)
    if len(ordered) > max_points:
        step = max(1, len(ordered) // max_points)
        ordered = sorted({ordered[index] for index in range(0, len(ordered), step)} | {0, len(rows) - 1})

    ordered = ordered[: max_points - 1] + [len(rows) - 1]
    return [rows[index] for index in ordered]


def get_convergence(
    experiment_id: str,
    run_id: str,
    downsample: int = 300,
    results_dir: Path | None = None,
) -> list[dict[str, Any]]:
    root = results_dir or results_root()
    path = root / experiment_id / "convergence" / f"{run_id}.csv"
    if not path.exists():
        raise FileNotFoundError(f"convergence not found: {run_id}")

    rows = _read_csv(path)
    if downsample > 0 and len(rows) > downsample:
        rows = _downsample_convergence(rows, downsample)
    return [
        {
            "objective_evaluations": int(row["objective_evaluations"]),
            "best_objective": float(row["best_objective"]),
            "current_objective": float(row["current_objective"]) if row.get("current_objective") else None,
            "iteration": int(row["iteration"]) if row.get("iteration") else None,
        }
        for row in rows
    ]


def get_solution(
    experiment_id: str,
    run_id: str,
    results_dir: Path | None = None,
) -> dict[str, Any]:
    root = results_dir or results_root()
    path = root / experiment_id / "solutions" / f"{run_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"solution not found: {run_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def get_live_solution(
    experiment_id: str,
    run_id: str,
    results_dir: Path | None = None,
) -> dict[str, Any]:
    import time

    root = results_dir or results_root()
    path = root / experiment_id / "solutions" / f"{run_id}.live.json"
    if not path.exists():
        raise FileNotFoundError(f"live solution not found: {run_id}")

    last_error: json.JSONDecodeError | None = None
    for _ in range(5):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            last_error = exc
            time.sleep(0.02)

    if last_error is not None:
        raise last_error
    raise FileNotFoundError(f"live solution not readable: {run_id}")


def list_configs(config_dir: Path | None = None) -> list[dict[str, Any]]:
    root = config_dir or (_project_root() / "config" / "examples")
    items: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "study_name" in payload:
            kind = "study"
            name = payload["study_name"]
        else:
            kind = "experiment"
            name = payload.get("experiment_name", path.stem)
        items.append(
            {
                "path": str(path.relative_to(_project_root())).replace("\\", "/"),
                "filename": path.name,
                "kind": kind,
                "name": name,
                "domain": payload.get("domain"),
                "instance": payload.get("instance"),
            }
        )
    return items
