"""Algorithm registry."""

from __future__ import annotations

from optimize.algorithms.base import OptimizationAlgorithm
from optimize.algorithms.mock_algorithm import MockRandomSearch
from optimize.algorithms.particle_swarm import ParticleSwarmOptimization
from optimize.algorithms.simulated_annealing import SimulatedAnnealing
from optimize.algorithms.tabu_search import TabuSearch

_REGISTRY: dict[str, type[OptimizationAlgorithm]] = {
    MockRandomSearch.name: MockRandomSearch,
    SimulatedAnnealing.name: SimulatedAnnealing,
    TabuSearch.name: TabuSearch,
    ParticleSwarmOptimization.name: ParticleSwarmOptimization,
}


def register_algorithm(cls: type[OptimizationAlgorithm]) -> type[OptimizationAlgorithm]:
    _REGISTRY[cls.name] = cls
    return cls


def get_algorithm(name: str) -> OptimizationAlgorithm:
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise KeyError(f"unknown algorithm '{name}'. Available: {available}")
    return _REGISTRY[name]()


def list_algorithms() -> list[str]:
    return sorted(_REGISTRY)
