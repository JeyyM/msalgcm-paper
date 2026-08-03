"""Tests for evaluation budget."""

import pytest

from optimize.experiments.budget import EvaluationBudget


def test_budget_increments_and_stops():
    budget = EvaluationBudget(maximum=3)
    assert budget.remaining() == 3
    budget.increment()
    budget.increment()
    assert budget.remaining() == 1
    assert not budget.exhausted()
    budget.increment()
    assert budget.exhausted()
    assert budget.remaining() == 0


def test_budget_rejects_non_positive_maximum():
    with pytest.raises(ValueError):
        EvaluationBudget(maximum=0)
