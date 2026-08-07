"""Random-key encoding helpers for discrete PSO."""

from __future__ import annotations

import numpy as np


def encode_permutation_by_item(solution: list[int], dimension: int) -> np.ndarray:
    """Encode a permutation where solution[rank] is the item visited at rank.

    decode via argsort(keys) must recover the same visit order.
    """
    keys = np.zeros(dimension, dtype=float)
    scale = max(dimension, 1)
    for rank, item in enumerate(solution):
        keys[item] = rank / scale + (item + 1) * 1e-9
    return keys


def encode_labeled_sequence(
    solution: list[int],
    labels: list[int],
) -> np.ndarray:
    """Encode a fixed-label sequence (e.g. JSP operation slots)."""
    if len(solution) != len(labels):
        raise ValueError("solution length must match labels length")

    keys = np.zeros(len(labels), dtype=float)
    scale = max(len(labels), 1)
    used: set[int] = set()
    for rank, job in enumerate(solution):
        slot = next(
            index
            for index, label in enumerate(labels)
            if index not in used and label == job
        )
        used.add(slot)
        keys[slot] = rank / scale + (slot + 1) * 1e-9
    return keys


def encode_binary_mask(mask: list[int]) -> np.ndarray:
    """Encode a binary feature mask for threshold decoding."""
    return np.array([0.75 if value else 0.25 for value in mask], dtype=float)


def perturb_keys(keys: np.ndarray, rng: np.random.Generator, sigma: float = 0.05) -> np.ndarray:
    return np.clip(keys + rng.normal(0.0, sigma, size=keys.shape), 0.0, 1.0)
