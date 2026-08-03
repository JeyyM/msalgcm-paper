# Metaheuristic Optimization Platform

Comparative platform for **Simulated Annealing**, **Tabu Search**, and **Particle Swarm Optimization** across TSP, job-shop scheduling, and feature selection.

## Status

| Phase | Status |
|-------|--------|
| Phase 0 — Scaffold | Done |
| Phase 1 — Core framework | Done (mock domain) |
| Phase 2 — TSP | Next |
| Phase 3 — Scheduling | Planned |
| Phase 4 — Feature selection | Planned |

## Setup

```bash
pip install -e ".[dev]"
```

## CLI

```bash
# List registered domains and algorithms
optimize list

# Validate an experiment config
optimize validate --config config/examples/mock_smoke_test.json

# Run an experiment
optimize run --config config/examples/mock_smoke_test.json
```

## Tests

```bash
pytest
```

## Project layout

```text
config/           Decision registry + example experiment JSON
datasets/         Benchmark instances (TSP, JSP, feature selection)
scripts/          Dataset download utilities
src/optimize/     Application code
tests/            Unit and integration tests
results/          Generated experiment output (gitignored)
```

## Documentation

- `metaheuristic_optimization_project_overview.md` — full requirements
- `pipeline_definition.md` — runtime flow and build phases
- `config/decisions.yaml` — locked research decisions

## Datasets

Download benchmarks:

```bash
python scripts/download_datasets.py
```

See `datasets/README.md` for sources and layout.
