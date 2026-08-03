"""TSP distance calculations."""

from __future__ import annotations

import math

import numpy as np


def tsplib_distance(a: tuple[float, float], b: tuple[float, float]) -> int:
    """TSPLIB EUC_2D rounded Euclidean distance."""
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return int(math.sqrt(dx * dx + dy * dy) + 0.5)


def build_distance_matrix(coordinates: list[tuple[float, float]]) -> np.ndarray:
    n = len(coordinates)
    matrix = np.zeros((n, n), dtype=np.int32)
    for i in range(n):
        for j in range(i + 1, n):
            dist = tsplib_distance(coordinates[i], coordinates[j])
            matrix[i, j] = dist
            matrix[j, i] = dist
    return matrix


def tour_length(route: list[int], distance_matrix: np.ndarray) -> int:
    total = 0
    n = len(route)
    for i in range(n):
        total += int(distance_matrix[route[i], route[(i + 1) % n]])
    return total


def nearest_neighbor_route(
    distance_matrix: np.ndarray,
    rng: np.random.Generator,
) -> list[int]:
    """Greedy nearest-neighbor construction with a random start city."""
    n = distance_matrix.shape[0]
    start = int(rng.integers(0, n))
    unvisited = set(range(n))
    route = [start]
    unvisited.remove(start)
    current = start

    while unvisited:
        next_city = min(unvisited, key=lambda city: int(distance_matrix[current, city]))
        route.append(next_city)
        unvisited.remove(next_city)
        current = next_city

    return route
