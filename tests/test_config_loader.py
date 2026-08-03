"""Tests for experiment config loading."""

from pathlib import Path

from optimize.config.loader import load_experiment_config


def test_load_mock_smoke_config():
    config_path = Path("config/examples/mock_smoke_test.json")
    config = load_experiment_config(config_path)
    assert config.experiment_name == "mock_smoke_test"
    assert config.domain == "mock"
    assert config.evaluation_budget == 500
