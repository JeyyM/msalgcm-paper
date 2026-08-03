"""Deterministic seed generation for repeated runs."""

from __future__ import annotations


class SeedManager:
    """Generates reproducible run seeds from a base seed."""

    def __init__(self, base_seed: int) -> None:
        self.base_seed = base_seed

    def generate(self, num_runs: int) -> list[int]:
        if num_runs <= 0:
            raise ValueError("num_runs must be positive")
        return [self.base_seed + i for i in range(num_runs)]
