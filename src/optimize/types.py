"""Shared types and enums."""

from __future__ import annotations

from enum import StrEnum


class StopReason(StrEnum):
    EVALUATION_BUDGET = "evaluation_budget_exhausted"
    RUNTIME_LIMIT = "runtime_limit_reached"
    NO_IMPROVEMENT = "no_improvement_threshold"
    MAX_ITERATIONS = "algorithm_max_iterations"
    CANCELLED = "cancelled"
    ERROR = "error"
    COMPLETED = "completed"


class RunStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
