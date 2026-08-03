"""Job-shop neighborhood operators on operation sequences."""

from __future__ import annotations

import numpy as np

from optimize.domains.operators import random_operator


def apply_operator(sequence: list[int], operator: str, rng: np.random.Generator) -> list[int]:
    n = len(sequence)
    if n < 2:
        return sequence.copy()

    if operator == "swap":
        i, j = rng.choice(n, size=2, replace=False)
        neighbor = sequence.copy()
        neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
        return neighbor

    if operator == "insertion":
        i, j = rng.choice(n, size=2, replace=False)
        neighbor = sequence.copy()
        value = neighbor.pop(i)
        if j > i:
            j -= 1
        neighbor.insert(j, value)
        return neighbor

    if operator == "inversion":
        i, j = sorted(rng.choice(n, size=2, replace=False))
        if i == j:
            j = min(j + 1, n - 1)
        neighbor = sequence.copy()
        neighbor[i : j + 1] = reversed(neighbor[i : j + 1])
        return neighbor

    raise ValueError(f"unsupported scheduling operator: {operator}")


__all__ = ["apply_operator", "random_operator"]
