"""Feature-selection domain catalog, completion status, and dynamic experiment configs."""

from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from optimize.experiments.models import ExperimentConfig

FS_RUNS = 30
FS_EVALUATION_BUDGET = 5000
FS_BASE_SEED = 4000

FS_ALGORITHMS = [
    "simulated_annealing",
    "tabu_search",
    "particle_swarm",
]

# Final comparison datasets shown in the dashboard and launchable via the API.
# Tuning-only sets (ZooEW, IonosphereEW, SonarEW) and MadelonEW are excluded —
# see config/decisions.yaml D14.
FS_COMPARISON_DATASETS = [
    "BreastEW",
    "WineEW",
    "LymphographyEW",
    "SpectEW",
]

ALGORITHM_LABELS = {
    "simulated_annealing": "Simulated Annealing",
    "tabu_search": "Tabu Search",
    "particle_swarm": "Particle Swarm",
}


@dataclass(frozen=True)
class FsBatchSummary:
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


def prepare_fs_launch(instance: str, algorithm: str, results_dir: Path | None = None) -> None:
    from optimize.api.services.results_reader import results_root

    root = results_dir or results_root()
    _clear_managed_experiments(root, instance, algorithm)


def _project_root() -> Path:
    return Path.cwd()


def _metadata_path() -> Path:
    return _project_root() / "datasets" / "feature_selection" / "metadata.json"


def _base_template_path() -> Path:
    return _project_root() / "config" / "examples" / "fs_breastew_comparison.json"


def _load_fs_all_instances() -> list[dict[str, Any]]:
    metadata = json.loads(_metadata_path().read_text(encoding="utf-8"))
    instances: list[dict[str, Any]] = []
    for item in metadata.get("ew_benchmarks", {}).get("datasets", []):
        name = item["dataset"]
        file_name = Path(str(item["file"])).name
        instances.append(
            {
                "name": name,
                "file": f"ew/{file_name}",
                "num_samples": item.get("instances"),
                "num_features": item.get("features"),
                "discretization": item.get("discretization"),
            }
        )
    return instances


def load_fs_instances() -> list[dict[str, Any]]:
    """Return only the held-out comparison datasets exposed in the dashboard."""
    allowed = set(FS_COMPARISON_DATASETS)
    return [item for item in _load_fs_all_instances() if item["name"] in allowed]


def build_fs_config(instance: str, algorithm: str) -> ExperimentConfig:
    if algorithm not in FS_ALGORITHMS:
        raise ValueError(f"unsupported feature-selection algorithm: {algorithm}")

    instances = {item["name"]: item for item in load_fs_instances()}
    if instance not in instances:
        if instance in {item["name"] for item in _load_fs_all_instances()}:
            raise ValueError(
                f"dataset {instance} is not in the final comparison set "
                f"({', '.join(FS_COMPARISON_DATASETS)})"
            )
        raise ValueError(f"unknown feature-selection dataset: {instance}")

    template = json.loads(_base_template_path().read_text(encoding="utf-8"))
    template["experiment_name"] = f"fs_{instance.lower()}_{algorithm}"
    template["instance"] = instance
    template["instance_path"] = f"datasets/feature_selection/{instances[instance]['file']}"
    template["algorithms"] = [algorithm]
    template["runs"] = FS_RUNS
    template["evaluation_budget"] = FS_EVALUATION_BUDGET
    template["seed_policy"] = {"base_seed": FS_BASE_SEED}
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


def _is_managed_fs_experiment(experiment_dir: Path, instance: str, algorithm: str) -> bool:
    expected_name = f"fs_{instance.lower()}_{algorithm}"
    config_path = experiment_dir / "experiment_config.json"
    if config_path.exists():
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        config = payload.get("config", {})
        if config.get("domain") == "feature_selection" and config.get("experiment_name") == expected_name:
            return config.get("algorithms") == [algorithm]
    return experiment_dir.name.endswith(f"_{expected_name}")


def _iter_managed_experiments(
    root: Path,
    instance: str,
    algorithm: str,
) -> list[FsBatchSummary]:
    summaries: list[FsBatchSummary] = []
    if not root.exists():
        return summaries

    for experiment_dir in root.iterdir():
        if not experiment_dir.is_dir():
            continue
        if not _is_managed_fs_experiment(experiment_dir, instance, algorithm):
            continue
        completed, total = _experiment_stats(experiment_dir)
        if total == 0:
            continue
        summaries.append(
            FsBatchSummary(
                experiment_id=experiment_dir.name,
                completed_runs=completed,
                total_runs=total,
                done=completed >= FS_RUNS,
            )
        )
    return summaries


def _pick_canonical_batch(summaries: list[FsBatchSummary]) -> FsBatchSummary | None:
    if not summaries:
        return None
    complete = [item for item in summaries if item.done]
    pool = complete if complete else summaries
    return max(pool, key=lambda item: item.experiment_id)


def get_fs_batch(instance: str, algorithm: str, results_dir: Path | None = None) -> FsBatchSummary | None:
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
                "best_gap_percentage": None,
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


def _completion_entry(batch: FsBatchSummary | None, results_dir: Path) -> dict[str, Any]:
    if batch is None:
        return {
            "experiment_id": None,
            "completed_runs": 0,
            "target_runs": FS_RUNS,
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
        "target_runs": FS_RUNS,
        "done": batch.done,
        "can_launch": batch.can_launch,
        **stats,
    }


def fs_completion_status(results_dir: Path | None = None) -> dict[str, Any]:
    from optimize.api.services.results_reader import results_root

    root = results_dir or results_root()
    completion: dict[str, dict[str, dict[str, Any]]] = {}
    for instance_item in load_fs_instances():
        name = instance_item["name"]
        completion[name] = {}
        for algorithm in FS_ALGORITHMS:
            batch = _pick_canonical_batch(_iter_managed_experiments(root, name, algorithm))
            completion[name][algorithm] = _completion_entry(batch, root)

    return {
        "runs_per_experiment": FS_RUNS,
        "algorithms": [
            {"id": algorithm, "label": ALGORITHM_LABELS[algorithm]}
            for algorithm in FS_ALGORITHMS
        ],
        "instances": load_fs_instances(),
        "completion": completion,
    }


def list_fs_runs(
    instance: str,
    algorithm: str,
    results_dir: Path | None = None,
) -> list[dict[str, Any]]:
    from optimize.api.services.results_reader import results_root

    batch = get_fs_batch(instance, algorithm, results_dir=results_dir)
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


def get_fs_live_status(instance: str, algorithm: str, results_dir: Path | None = None) -> dict[str, Any] | None:
    """Read a live-ish progress snapshot straight off disk.

    Mirrors the shape of RunProgress.to_dict() so the frontend's job-polling UI
    (progress bar, live convergence, live feature mask) works even for batches
    started outside the API — e.g. by a standalone script — where there is no
    in-memory job to poll. Returns None if there's nothing in-progress to show.
    """
    from optimize.api.services.results_reader import results_root

    root = results_dir or results_root()
    batch = get_fs_batch(instance, algorithm, results_dir=root)
    if batch is None or batch.done:
        return None

    experiment_dir = root / batch.experiment_id
    current_run_index = batch.completed_runs + 1
    current_run_id = f"{algorithm}_run_{current_run_index:03d}"

    current_best_objective: float | None = None
    convergence_path = experiment_dir / "convergence" / f"{current_run_id}.csv"
    if convergence_path.exists():
        try:
            with convergence_path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            if rows:
                value = rows[-1].get("best_objective")
                if value:
                    current_best_objective = float(value)
        except (OSError, ValueError):
            pass

    return {
        "job_id": "external",
        "status": "running",
        "job_type": "experiment",
        "experiment_name": f"fs_{instance.lower()}_{algorithm}",
        "current_algorithm": algorithm,
        "current_run_index": current_run_index,
        "total_runs": FS_RUNS,
        "completed_runs": batch.completed_runs,
        "current_run_id": current_run_id,
        "current_best_objective": current_best_objective,
        "experiment_dir": batch.experiment_id,
        "message": f"Running {current_run_id} (started outside the dashboard)",
        "error": None,
        "log": [],
        "progress_percent": round(100 * batch.completed_runs / FS_RUNS, 1),
    }


def write_fs_config_file(instance: str, algorithm: str) -> Path:
    config = build_fs_config(instance, algorithm)
    temp_dir = _project_root() / "config" / ".generated"
    temp_dir.mkdir(parents=True, exist_ok=True)
    path = temp_dir / f"fs_{instance.lower()}_{algorithm}.json"
    path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
    return path
