"""TSP neighborhood operators."""

from __future__ import annotations

import numpy as np


def apply_operator(route: list[int], operator: str, rng: np.random.Generator) -> list[int]:
    n = len(route)
    if n < 2:
        return route.copy()

    if operator == "swap":
        i, j = rng.choice(n, size=2, replace=False)
        neighbor = route.copy()
        neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
        return neighbor

    if operator == "insertion":
        i, j = rng.choice(n, size=2, replace=False)
        neighbor = route.copy()
        city = neighbor.pop(i)
        if j > i:
            j -= 1
        neighbor.insert(j, city)
        return neighbor

    if operator in {"inversion", "two_opt"}:
        i, j = sorted(rng.choice(n, size=2, replace=False))
        if i == j:
            j = min(j + 1, n - 1)
        neighbor = route.copy()
        neighbor[i : j + 1] = reversed(neighbor[i : j + 1])
        return neighbor

    raise ValueError(f"unsupported TSP operator: {operator}")


from optimize.domains.operators import random_operator
