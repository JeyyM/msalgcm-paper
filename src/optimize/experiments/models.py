"""Experiment and run result data models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from optimize.types import RunStatus, StopReason


class SeedPolicy(BaseModel):
    base_seed: int = 1000


class OutputSettings(BaseModel):
    directory: str = "results"


class ExperimentConfig(BaseModel):
    experiment_name: str
    domain: str
    instance: str
    algorithms: list[str]
    runs: int = Field(gt=0)
    evaluation_budget: int = Field(gt=0)
    seed_policy: SeedPolicy = Field(default_factory=SeedPolicy)
    instance_path: str | None = None
    domain_config: dict[str, Any] = Field(default_factory=dict)
    algorithm_configs: dict[str, dict[str, Any]] = Field(default_factory=dict)
    output: OutputSettings = Field(default_factory=OutputSettings)
    runtime_budget_seconds: float | None = None

    @field_validator("algorithms")
    @classmethod
    def at_least_one_algorithm(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("at least one algorithm must be selected")
        return value


class HistoryRecord(BaseModel):
    objective_evaluations: int
    best_objective: float
    current_objective: float | None = None
    iteration: int | None = None


class RunResult(BaseModel):
    experiment_name: str
    run_id: str
    algorithm: str
    domain: str
    instance: str
    seed: int
    status: RunStatus
    stop_reason: StopReason
    initial_objective: float
    best_objective: float
    final_objective: float
    runtime_seconds: float
    objective_evaluations: int
    iterations: int
    parameters: dict[str, Any] = Field(default_factory=dict)
    best_solution: Any = None
    history: list[HistoryRecord] = Field(default_factory=list)
    error_message: str | None = None
