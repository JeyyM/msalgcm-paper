"""Background job execution for experiments and studies."""

from __future__ import annotations

import threading
import uuid
from pathlib import Path
from typing import Any

from optimize.config.loader import load_experiment_config
from optimize.experiments.progress import RunProgress
from optimize.experiments.runner import ExperimentRunner
from optimize.experiments.study import StudyRunner, load_study_config


class JobManager:
    """Runs experiments in background threads with progress tracking."""

    def __init__(self) -> None:
        self._jobs: dict[str, RunProgress] = {}
        self._lock = threading.Lock()

    def get(self, job_id: str) -> RunProgress | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self) -> list[dict[str, Any]]:
        with self._lock:
            return [{"job_id": job_id, **progress.to_dict()} for job_id, progress in self._jobs.items()]

    def start_experiment(self, config_path: str | Path) -> str:
        job_id = uuid.uuid4().hex[:12]
        config_path = Path(config_path)
        config = load_experiment_config(config_path)
        total_runs = len(config.algorithms) * config.runs

        progress = RunProgress(
            status="pending",
            job_type="experiment",
            config_path=str(config_path),
            experiment_name=config.experiment_name,
            total_runs=total_runs,
            message="Queued",
        )
        with self._lock:
            self._jobs[job_id] = progress

        thread = threading.Thread(target=self._run_experiment, args=(job_id, config_path), daemon=True)
        thread.start()
        return job_id

    def start_study(self, config_path: str | Path) -> str:
        job_id = uuid.uuid4().hex[:12]
        config_path = Path(config_path)
        study_config = load_study_config(config_path)

        progress = RunProgress(
            status="pending",
            job_type="study",
            config_path=str(config_path),
            experiment_name=study_config.study_name,
            total_runs=len(study_config.experiments),
            message="Queued",
        )
        with self._lock:
            self._jobs[job_id] = progress

        thread = threading.Thread(target=self._run_study, args=(job_id, config_path), daemon=True)
        thread.start()
        return job_id

    def _append_log(self, job_id: str, message: str) -> None:
        with self._lock:
            progress = self._jobs[job_id]
            progress.log.append(message)
            progress.message = message

    def _run_experiment(self, job_id: str, config_path: Path) -> None:
        with self._lock:
            self._jobs[job_id].status = "running"

        def callback(update: RunProgress) -> None:
            with self._lock:
                current = self._jobs[job_id]
                current.status = update.status
                current.current_algorithm = update.current_algorithm
                current.current_run_index = update.current_run_index
                current.total_runs = update.total_runs
                current.completed_runs = update.completed_runs
                current.current_run_id = update.current_run_id
                current.current_best_objective = update.current_best_objective
                current.experiment_dir = update.experiment_dir
                current.message = update.message
                if update.log:
                    current.log.extend(update.log)

        try:
            runner = ExperimentRunner()
            output_dir = runner.run(config_path, progress_callback=callback)
            with self._lock:
                progress = self._jobs[job_id]
                progress.status = "completed"
                progress.experiment_dir = output_dir.name
                progress.message = f"Completed: {output_dir.name}"
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                progress = self._jobs[job_id]
                progress.status = "failed"
                progress.error = str(exc)
                progress.message = f"Failed: {exc}"

    def _run_study(self, job_id: str, config_path: Path) -> None:
        with self._lock:
            self._jobs[job_id].status = "running"

        completed = 0

        def study_progress(instance: str, experiment_dir: Path, total: int) -> None:
            nonlocal completed
            completed += 1
            with self._lock:
                progress = self._jobs[job_id]
                progress.completed_runs = completed
                progress.total_runs = total
                progress.current_run_id = instance
                progress.experiment_dir = experiment_dir.name
                progress.message = f"Finished {instance} ({completed}/{total})"

        try:
            runner = StudyRunner()
            study_dir = runner.run(config_path, progress_callback=study_progress)
            with self._lock:
                progress = self._jobs[job_id]
                progress.status = "completed"
                progress.study_dir = study_dir.name
                progress.message = f"Study completed: {study_dir.name}"
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                progress = self._jobs[job_id]
                progress.status = "failed"
                progress.error = str(exc)
                progress.message = f"Failed: {exc}"


job_manager = JobManager()
