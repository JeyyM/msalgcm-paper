"""Multi-instance experiment study orchestration."""

from __future__ import annotations

import csv
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from optimize.config.loader import load_experiment_config
from optimize.experiments.runner import ExperimentRunner


@dataclass(frozen=True)
class StudyExperiment:
    config_path: Path
    instance: str
    problem_size: int


@dataclass(frozen=True)
class StudyConfig:
    study_name: str
    output_directory: str
    experiments: list[StudyExperiment]


def load_study_config(path: str | Path) -> StudyConfig:
    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    base_dir = config_path.parent

    experiments: list[StudyExperiment] = []
    for entry in raw["experiments"]:
        experiment_config = entry["config"]
        config_file = Path(experiment_config)
        if not config_file.is_absolute():
            config_file = (Path.cwd() / config_file).resolve()
            if not config_file.exists():
                config_file = (base_dir / experiment_config).resolve()

        problem_size = entry.get("problem_size")
        if problem_size is None:
            experiment = load_experiment_config(config_file)
            if experiment.instance_path:
                if experiment.domain == "scheduling":
                    from optimize.domains.scheduling.jsp.loader import load_jsp

                    instance = load_jsp(experiment.instance_path)
                    problem_size = instance.num_operations
                elif experiment.domain == "feature_selection":
                    from optimize.domains.feature_selection.loader import load_ew_dataset

                    dataset = load_ew_dataset(experiment.instance_path)
                    problem_size = dataset.num_features
                else:
                    from optimize.domains.tsp.loader import load_tsplib

                    instance = load_tsplib(experiment.instance_path)
                    problem_size = instance.num_cities
            else:
                raise ValueError(f"problem_size required for study entry: {entry}")

        experiments.append(
            StudyExperiment(
                config_path=config_file,
                instance=entry.get("instance", load_experiment_config(config_file).instance),
                problem_size=int(problem_size),
            )
        )

    return StudyConfig(
        study_name=raw["study_name"],
        output_directory=raw.get("output_directory", "results"),
        experiments=experiments,
    )


def _read_summary_rows(experiment_dir: Path) -> list[dict[str, Any]]:
    summary_path = experiment_dir / "summary.csv"
    with summary_path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_scalability_summary(
    study_config: StudyConfig,
    experiment_dirs: list[tuple[StudyExperiment, Path]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for experiment, experiment_dir in experiment_dirs:
        for summary in _read_summary_rows(experiment_dir):
            rows.append(
                {
                    "study_name": study_config.study_name,
                    "instance": experiment.instance,
                    "problem_size": experiment.problem_size,
                    "algorithm": summary["algorithm"],
                    "runs": int(summary["runs"]),
                    "successful_runs": int(summary["successful_runs"]),
                    "mean_objective": float(summary["mean_objective"]),
                    "min_objective": float(summary["min_objective"]),
                    "max_objective": float(summary["max_objective"]),
                    "std_objective": float(summary["std_objective"]),
                    "mean_gap_percentage": (
                        float(summary["mean_gap_percentage"])
                        if summary.get("mean_gap_percentage") not in {None, ""}
                        else None
                    ),
                    "best_gap_percentage": (
                        float(summary["best_gap_percentage"])
                        if summary.get("best_gap_percentage") not in {None, ""}
                        else None
                    ),
                    "mean_runtime_seconds": float(summary["mean_runtime_seconds"]),
                    "experiment_dir": experiment_dir.name,
                }
            )
    rows.sort(key=lambda row: (row["problem_size"], row["algorithm"]))
    return rows


def write_scalability_summary(study_dir: Path, rows: list[dict[str, Any]]) -> Path:
    output_path = study_dir / "scalability_summary.csv"
    if not rows:
        return output_path
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return output_path


class StudyRunner:
    """Run a sequence of experiment configs and aggregate scalability results."""

    def __init__(self, experiment_runner: ExperimentRunner | None = None) -> None:
        self.experiment_runner = experiment_runner or ExperimentRunner()

    def run(
        self,
        study_config_path: str | Path,
        progress_callback: Callable[[str, Path, int], None] | None = None,
    ) -> Path:
        study_config = load_study_config(study_config_path)
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H%M%S")
        study_dir = Path(study_config.output_directory) / f"{timestamp}_{study_config.study_name}"
        study_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "study_name": study_config.study_name,
            "source_config_path": str(Path(study_config_path).resolve()),
            "started_at_utc": datetime.now(UTC).isoformat(),
            "experiments": [],
        }

        experiment_dirs: list[tuple[StudyExperiment, Path]] = []
        total = len(study_config.experiments)
        for experiment in study_config.experiments:
            experiment_dir = self.experiment_runner.run(experiment.config_path)
            experiment_dirs.append((experiment, experiment_dir))
            manifest["experiments"].append(
                {
                    "instance": experiment.instance,
                    "problem_size": experiment.problem_size,
                    "config_path": str(experiment.config_path),
                    "experiment_dir": experiment_dir.name,
                }
            )
            if progress_callback:
                progress_callback(experiment.instance, experiment_dir, total)

        scalability_rows = build_scalability_summary(study_config, experiment_dirs)
        write_scalability_summary(study_dir, scalability_rows)

        try:
            from optimize.visualization.scalability import generate_scalability_charts

            chart_paths = generate_scalability_charts(study_dir, scalability_rows)
            manifest["charts"] = [path.name for path in chart_paths]
        except ImportError:
            manifest["charts"] = []
            manifest["chart_note"] = "install matplotlib: pip install '.[viz]'"
        except Exception as exc:  # noqa: BLE001
            manifest["charts"] = []
            manifest["chart_error"] = str(exc)

        manifest["completed_at_utc"] = datetime.now(UTC).isoformat()
        (study_dir / "study_manifest.json").write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )

        return study_dir
