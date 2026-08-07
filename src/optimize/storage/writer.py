"""Persist experiment artifacts."""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any

from optimize.experiments.aggregate import build_seed_rows, build_statistics_rows, build_summary_rows
from optimize.experiments.models import ExperimentConfig, HistoryRecord, RunResult
from optimize.storage.environment import capture_environment


def _serialize_csv_value(value: Any) -> Any:
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    if hasattr(value, "value"):
        return value.value
    return value


class LiveConvergenceWriter:
    """Append convergence rows during a run so dashboards can poll partial curves."""

    _FIELDNAMES = ["objective_evaluations", "best_objective", "current_objective", "iteration"]

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = path.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._handle, fieldnames=self._FIELDNAMES)
        self._writer.writeheader()
        self._handle.flush()

    def append(self, record: HistoryRecord) -> None:
        row = record.model_dump()
        self._writer.writerow({key: row.get(key) for key in self._FIELDNAMES})
        self._handle.flush()

    def close(self) -> None:
        self._handle.close()


def write_live_route_snapshot(
    path: Path,
    problem: Any,
    algorithm: Any,
    objective_evaluations: int,
) -> None:
    """Write the current tour snapshot for live dashboard maps."""
    current = algorithm.get_current_solution()
    payload = {
        "live": True,
        "objective_evaluations": objective_evaluations,
        "current": problem.serialize_solution(current) if current is not None else None,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, indent=2)
    for attempt in range(6):
        try:
            path.write_text(content, encoding="utf-8")
            stale_tmp = path.with_suffix(".tmp")
            if stale_tmp.exists():
                stale_tmp.unlink(missing_ok=True)
            return
        except OSError:
            if attempt == 5:
                raise
            time.sleep(0.025 * (attempt + 1))


def write_run_result(result: RunResult, experiment_dir: Path) -> None:
    experiment_dir.mkdir(parents=True, exist_ok=True)

    runs_csv = experiment_dir / "runs.csv"
    write_header = not runs_csv.exists()
    row = result.model_dump(exclude={"history", "best_solution"})
    serialized_row = {key: _serialize_csv_value(value) for key, value in row.items()}

    with runs_csv.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=serialized_row.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(serialized_row)

    convergence_dir = experiment_dir / "convergence"
    convergence_dir.mkdir(exist_ok=True)
    convergence_path = convergence_dir / f"{result.run_id}.csv"
    with convergence_path.open("w", newline="", encoding="utf-8") as handle:
        if result.history:
            writer = csv.DictWriter(handle, fieldnames=result.history[0].model_dump().keys())
            writer.writeheader()
            for record in result.history:
                writer.writerow(record.model_dump())

    if result.best_solution is not None:
        solutions_dir = experiment_dir / "solutions"
        solutions_dir.mkdir(exist_ok=True)
        solution_path = solutions_dir / f"{result.run_id}.json"
        solution_path.write_text(
            json.dumps(result.best_solution, indent=2),
            encoding="utf-8",
        )


def write_experiment_config(
    experiment_dir: Path,
    config_path: Path,
    config: ExperimentConfig,
) -> None:
    payload = {
        "source_config_path": str(config_path),
        "config": json.loads(config.model_dump_json()),
    }
    (experiment_dir / "experiment_config.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def write_environment(experiment_dir: Path) -> None:
    (experiment_dir / "environment.json").write_text(
        json.dumps(capture_environment(), indent=2),
        encoding="utf-8",
    )


def write_seeds_csv(
    experiment_dir: Path,
    config: ExperimentConfig,
    seeds: list[int],
) -> None:
    rows = build_seed_rows(config, seeds)
    path = experiment_dir / "seeds.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["run_id", "algorithm", "seed", "run_index"])
        writer.writeheader()
        writer.writerows(rows)


def write_summary_csv(experiment_dir: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path = experiment_dir / "summary.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_statistics_csv(experiment_dir: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path = experiment_dir / "statistics.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def finalize_experiment(
    experiment_dir: Path,
    results: list[RunResult],
    config: ExperimentConfig,
) -> None:
    summary_rows = build_summary_rows(results, config)
    statistics_rows = build_statistics_rows(results, config)
    write_summary_csv(experiment_dir, summary_rows)
    write_statistics_csv(experiment_dir, statistics_rows)

    logs_dir = experiment_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    completed = sum(1 for result in results if result.status.value == "completed")
    failed = len(results) - completed
    log_lines = [
        f"experiment={config.experiment_name}",
        f"domain={config.domain}",
        f"instance={config.instance}",
        f"algorithms={','.join(config.algorithms)}",
        f"runs={len(results)}",
        f"completed={completed}",
        f"failed={failed}",
    ]

    try:
        from optimize.visualization.charts import generate_experiment_charts

        chart_paths = generate_experiment_charts(experiment_dir, results, config)
        log_lines.append(f"charts={len(chart_paths)}")
        for chart_path in chart_paths:
            log_lines.append(f"chart={chart_path.relative_to(experiment_dir).as_posix()}")
    except ImportError:
        log_lines.append("charts=skipped (install matplotlib: pip install '.[viz]')")
    except Exception as exc:  # noqa: BLE001
        log_lines.append(f"charts=failed ({exc})")

    (logs_dir / "experiment.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
