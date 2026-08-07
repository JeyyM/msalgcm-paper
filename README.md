# Metaheuristic Optimization Platform

Comparative platform for **Simulated Annealing**, **Tabu Search**, and **Particle Swarm Optimization** across TSP, job-shop scheduling, and feature selection.

## Start here

**[`documentation v1.md`](documentation%20v1.md)** — installation, running the website, current status, next steps.

Archived planning docs: [`old documentation/`](old%20documentation/)

## Quick start (website)

```bash
pip install -e ".[dev,web,ml,viz]"
npm install && npm install --prefix web/frontend
npm run dev
```

Open http://127.0.0.1:5173

## Quick start (CLI)

```bash
pip install -e ".[dev,ml]"
python -m optimize.ui.cli list
python -m optimize.ui.cli run --config config/examples/tsp_eil51_smoke.json
```

## Tests

```bash
pytest
```

## Layout

```text
documentation v1.md    Current guide
literature/            Paper references
config/                Decisions + experiment configs
datasets/              Benchmarks
results/               Experiment output (gitignored)
src/optimize/          Application code
web/frontend/          React dashboard
```
