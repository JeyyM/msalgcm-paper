"""JSP domain catalog, completion status, and dynamic experiment configs."""

from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from optimize.experiments.models import ExperimentConfig

JSP_RUNS = 30
JSP_EVALUATION_BUDGET = 50_000
JSP_BASE_SEED = 2000

JSP_ALGORITHMS = [
    "simulated_annealing",
    "tabu_search",
    "particle_swarm",
]

ALGORITHM_LABELS = {
    "simulated_annealing": "Simulated Annealing",
    "tabu_search": "Tabu Search",
    "particle_swarm": "Particle Swarm",
}


@dataclass(frozen=True)
class JspBatchSummary:
    experiment_id: str
    completed_runs: int
    total_runs: int
    done: bool

    @property
    def can_launch(self) -> bool:
        return True


def _clear_managed_experiments(root: Path, instance: str, algorithm: str) -> None:
    for summary in _iter_managed_experiments(root, instance, algorithm):
        shutil.rmtree(root / summary.experiment_id, ignore_errors=True)


def prepare_jsp_launch(instance: str, algorithm: str, results_dir: Path | None = None) -> None:
    """Remove any existing batch for this pair so a rerun replaces prior results."""
    from optimize.api.services.results_reader import results_root

    root = results_dir or results_root()
    _clear_managed_experiments(root, instance, algorithm)


def _project_root() -> Path:
    return Path.cwd()


def _metadata_path() -> Path:
    return _project_root() / "datasets" / "scheduling" / "jsp" / "metadata.json"


def _base_template_path() -> Path:
    return _project_root() / "config" / "examples" / "jsp_ft10_comparison.json"


def load_jsp_instances() -> list[dict[str, Any]]:
    metadata = json.loads(_metadata_path().read_text(encoding="utf-8"))
    instances: list[dict[str, Any]] = []
    for item in metadata.get("instances", []):
        entry = dict(item)
        bks = entry.get("best_known_makespan")
        if bks is not None:
            entry["known_optimum"] = bks
        instances.append(entry)
    return instances


def build_jsp_config(instance: str, algorithm: str) -> ExperimentConfig:
    if algorithm not in JSP_ALGORITHMS:
        raise ValueError(f"unsupported JSP algorithm: {algorithm}")

    instances = {item["name"]: item for item in load_jsp_instances()}
    if instance not in instances:
        raise ValueError(f"unknown JSP instance: {instance}")

    template = json.loads(_base_template_path().read_text(encoding="utf-8"))
    template["experiment_name"] = f"jsp_{instance}_{algorithm}"
    template["instance"] = instance
    template["instance_path"] = f"datasets/scheduling/jsp/{instances[instance]['file']}"
    template["algorithms"] = [algorithm]
    template["runs"] = JSP_RUNS
    template["evaluation_budget"] = JSP_EVALUATION_BUDGET
    template["seed_policy"] = {"base_seed": JSP_BASE_SEED}
    return ExperimentConfig.model_validate(template)


def _experiment_stats(experiment_dir: Path) -> tuple[int, int]:
    runs_path = experiment_dir / "runs.csv"
    if not runs_path.exists():
        return 0, 0
    with runs_path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return 0, 0
    completed = sum(1 for row in rows if row.get("status") == "completed")
    return completed, len(rows)


def _is_managed_jsp_experiment(experiment_dir: Path, instance: str, algorithm: str) -> bool:
    expected_name = f"jsp_{instance}_{algorithm}"
    config_path = experiment_dir / "experiment_config.json"
    if config_path.exists():
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        config = payload.get("config", {})
        if config.get("domain") == "scheduling" and config.get("experiment_name") == expected_name:
            return config.get("algorithms") == [algorithm]
    return experiment_dir.name.endswith(f"_{expected_name}")


def _iter_managed_experiments(
    root: Path,
    instance: str,
    algorithm: str,
) -> list[JspBatchSummary]:
    summaries: list[JspBatchSummary] = []
    if not root.exists():
        return summaries

    for experiment_dir in root.iterdir():
        if not experiment_dir.is_dir():
            continue
        if not _is_managed_jsp_experiment(experiment_dir, instance, algorithm):
            continue
        completed, total = _experiment_stats(experiment_dir)
        if total == 0:
            continue
        summaries.append(
            JspBatchSummary(
                experiment_id=experiment_dir.name,
                completed_runs=completed,
                total_runs=total,
                done=completed >= JSP_RUNS,
            )
        )
    return summaries


def _pick_canonical_batch(summaries: list[JspBatchSummary]) -> JspBatchSummary | None:
    if not summaries:
        return None
    complete = [item for item in summaries if item.done]
    pool = complete if complete else summaries
    return max(pool, key=lambda item: item.experiment_id)


def get_jsp_batch(instance: str, algorithm: str, results_dir: Path | None = None) -> JspBatchSummary | None:
    from optimize.api.services.results_reader import results_root

    root = results_dir or results_root()
    return _pick_canonical_batch(_iter_managed_experiments(root, instance, algorithm))


def _batch_stats(experiment_dir: Path) -> dict[str, float | int | None]:
    summary_path = experiment_dir / "summary.csv"
    if summary_path.exists():
        with summary_path.open(encoding="utf-8") as handle:
            row = next(csv.DictReader(handle), None)
        if row:
            return {
                "successful_runs": int(row.get("successful_runs") or 0),
                "failed_runs": int(row.get("failed_runs") or 0),
                "best_objective": float(row["min_objective"]) if row.get("min_objective") else None,
                "mean_objective": float(row["mean_objective"]) if row.get("mean_objective") else None,
                "best_gap_percentage": float(row["best_gap_percentage"])
                if row.get("best_gap_percentage")
                else None,
            }

    runs_path = experiment_dir / "runs.csv"
    if not runs_path.exists():
        return {
            "successful_runs": 0,
            "failed_runs": 0,
            "best_objective": None,
            "mean_objective": None,
            "best_gap_percentage": None,
        }

    objectives: list[float] = []
    successful = 0
    failed = 0
    with runs_path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("status") == "completed":
                successful += 1
                value = row.get("best_objective")
                if value:
                    objectives.append(float(value))
            else:
                failed += 1

    return {
        "successful_runs": successful,
        "failed_runs": failed,
        "best_objective": min(objectives) if objectives else None,
        "mean_objective": sum(objectives) / len(objectives) if objectives else None,
        "best_gap_percentage": None,
    }


def _completion_entry(batch: JspBatchSummary | None, results_dir: Path) -> dict[str, Any]:
    if batch is None:
        return {
            "experiment_id": None,
            "completed_runs": 0,
            "target_runs": JSP_RUNS,
            "done": False,
            "can_launch": True,
            "best_objective": None,
            "mean_objective": None,
            "successful_runs": 0,
            "failed_runs": 0,
        }

    stats = _batch_stats(results_dir / batch.experiment_id)
    return {
        "experiment_id": batch.experiment_id,
        "completed_runs": batch.completed_runs,
        "target_runs": JSP_RUNS,
        "done": batch.done,
        "can_launch": batch.can_launch,
        **stats,
    }


def jsp_completion_status(results_dir: Path | None = None) -> dict[str, Any]:
    from optimize.api.services.results_reader import results_root

    root = results_dir or results_root()
    completion: dict[str, dict[str, dict[str, Any]]] = {}
    for instance_item in load_jsp_instances():
        name = instance_item["name"]
        completion[name] = {}
        for algorithm in JSP_ALGORITHMS:
            batch = _pick_canonical_batch(_iter_managed_experiments(root, name, algorithm))
            completion[name][algorithm] = _completion_entry(batch, root)

    return {
        "runs_per_experiment": JSP_RUNS,
        "algorithms": [
            {"id": algorithm, "label": ALGORITHM_LABELS[algorithm]}
            for algorithm in JSP_ALGORITHMS
        ],
        "instances": load_jsp_instances(),
        "completion": completion,
    }


def list_jsp_runs(
    instance: str,
    algorithm: str,
    results_dir: Path | None = None,
) -> list[dict[str, Any]]:
    from optimize.api.services.results_reader import results_root

    batch = get_jsp_batch(instance, algorithm, results_dir=results_dir)
    if batch is None:
        return []

    root = results_dir or results_root()
    runs_path = root / batch.experiment_id / "runs.csv"
    if not runs_path.exists():
        return []

    rows: list[dict[str, Any]] = []
    with runs_path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "experiment_id": batch.experiment_id,
                    "run_id": row.get("run_id"),
                    "seed": row.get("seed"),
                    "status": row.get("status"),
                    "best_objective": float(row["best_objective"]) if row.get("best_objective") else None,
                    "runtime_seconds": float(row["runtime_seconds"]) if row.get("runtime_seconds") else None,
                },
            )

    rows.sort(key=lambda item: item["run_id"] or "")
    return rows


def write_jsp_config_file(instance: str, algorithm: str) -> Path:
    config = build_jsp_config(instance, algorithm)
    temp_dir = _project_root() / "config" / ".generated"
    temp_dir.mkdir(parents=True, exist_ok=True)
    path = temp_dir / f"jsp_{instance}_{algorithm}.json"
    path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
    return path
