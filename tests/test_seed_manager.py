"""Tests for seed manager."""

import pytest

from optimize.experiments.seed_manager import SeedManager


def test_seed_manager_generates_sequential_seeds():
    seeds = SeedManager(base_seed=1000).generate(4)
    assert seeds == [1000, 1001, 1002, 1003]


def test_seed_manager_rejects_zero_runs():
    with pytest.raises(ValueError):
        SeedManager(base_seed=1).generate(0)
