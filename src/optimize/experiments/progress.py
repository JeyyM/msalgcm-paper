"""Progress reporting for long-running experiments."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class RunProgress:
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    job_type: Literal["experiment", "study"] = "experiment"
    config_path: str = ""
    experiment_name: str = ""
    current_algorithm: str | None = None
    current_run_index: int = 0
    total_runs: int = 0
    completed_runs: int = 0
    current_run_id: str | None = None
    current_best_objective: float | None = None
    experiment_dir: str | None = None
    study_dir: str | None = None
    message: str = ""
    error: str | None = None
    log: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "status": self.status,
            "job_type": self.job_type,
            "config_path": self.config_path,
            "experiment_name": self.experiment_name,
            "current_algorithm": self.current_algorithm,
            "current_run_index": self.current_run_index,
            "total_runs": self.total_runs,
            "completed_runs": self.completed_runs,
            "current_run_id": self.current_run_id,
            "current_best_objective": self.current_best_objective,
            "experiment_dir": self.experiment_dir,
            "study_dir": self.study_dir,
            "message": self.message,
            "error": self.error,
            "log": self.log[-20:],
            "progress_percent": (
                round(100 * self.completed_runs / self.total_runs, 1)
                if self.total_runs > 0
                else 0.0
            ),
        }
        if self.experiment_dir and self.current_run_id:
            try:
                from optimize.api.services.results_reader import get_live_solution

                live = get_live_solution(self.experiment_dir, self.current_run_id)
                current = live.get("current") or {}
                payload["live_route"] = current.get("route")
                payload["live_distance"] = current.get("distance")
                payload["live_evaluations"] = live.get("objective_evaluations")
            except (FileNotFoundError, OSError, ValueError, TypeError, json.JSONDecodeError):
                pass
        return payload
