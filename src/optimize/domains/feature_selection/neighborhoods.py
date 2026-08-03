"""Binary feature-selection neighborhood operators."""

from __future__ import annotations

import numpy as np

from optimize.domains.operators import random_operator


def apply_operator(mask: list[int], operator: str, rng: np.random.Generator) -> list[int]:
    n = len(mask)
    if n == 0:
        return mask.copy()

    if operator == "flip":
        index = int(rng.integers(0, n))
        neighbor = mask.copy()
        neighbor[index] = 1 - neighbor[index]
        return neighbor

    if operator == "swap":
        i, j = rng.choice(n, size=2, replace=False)
        neighbor = mask.copy()
        neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
        return neighbor

    raise ValueError(f"unsupported feature-selection operator: {operator}")


__all__ = ["apply_operator", "random_operator"]
