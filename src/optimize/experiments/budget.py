"""Evaluation budget — single source of truth for objective calls."""

from __future__ import annotations


class EvaluationBudget:
    """Tracks objective-function evaluations against a maximum budget."""

    def __init__(self, maximum: int) -> None:
        if maximum <= 0:
            raise ValueError("evaluation budget must be positive")
        self.maximum = maximum
        self.count = 0

    def increment(self) -> None:
        self.count += 1

    def remaining(self) -> int:
        return max(0, self.maximum - self.count)

    def exhausted(self) -> bool:
        return self.count >= self.maximum

    def __repr__(self) -> str:
        return f"EvaluationBudget(count={self.count}, maximum={self.maximum})"
