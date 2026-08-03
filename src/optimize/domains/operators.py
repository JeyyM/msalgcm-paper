"""Shared neighborhood operator helpers."""

from __future__ import annotations

import numpy as np


def random_operator(operators: list[str], rng: np.random.Generator) -> str:
    return operators[int(rng.integers(0, len(operators)))]
