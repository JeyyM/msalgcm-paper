# MSALGCM Optimization Platform — Documentation v1

**Last updated:** 2026-08-06  
**Audience:** Group members running experiments, writing the paper, or extending the codebase.

This is the **single current guide** for what the project is, how to run it, what has been done, and what comes next. Older specs live in [`old documentation/`](old%20documentation/).

---

## 1. What this project is

A comparative research platform for three metaheuristics:

| Algorithm | Abbreviation |
|-----------|--------------|
| Simulated Annealing | SA |
| Tabu Search | TS |
| Particle Swarm Optimization | PSO |

Applied to three problem domains:

| Domain | Objective | Benchmark source |
|--------|-----------|------------------|
| **TSP** | Minimize tour distance | TSPLIB (6 active instances) |
| **Job-shop scheduling (JSP)** | Minimize makespan | Taillard / OR-Library via SchedulingLab |
| **Feature selection (FS)** | Minimize CV loss + subset penalty | EW datasets (Hall & Holmes style) |

**Research question (summary):** Under a fixed, fair protocol, how do SA, TS, and PSO compare on solution quality, convergence, and runtime within each domain?

We do **not** claim any algorithm is universally best (no free lunch).

---

## 2. Current status (what is done vs not)

### TSP — **benchmark complete**

| Item | Status |
|------|--------|
| Parameter tuning (equal-effort grid + NN confirm for TS/PSO) | Done |
| Frozen parameters | `results/tuning/selected_parameters.json` |
| Final comparison runs (30 runs × 3 algos × 3 instances) | Done |
| Web UI (instance × algorithm, live route + convergence) | Done |

**Paper result folders (use these):**

| Instance | Folder |
|----------|--------|
| kroA100 | `results/2026-08-06_214444_tsp_kroA100_comparison` |
| ch130 | `results/2026-08-06_220149_tsp_ch130_comparison` |
| rat195 | `results/2026-08-06_215320_tsp_rat195_comparison` |

Each folder has 90 completed runs (30 per algorithm). Do **not** use pre-tuning or smoke folders as paper results.

**Findings (high level):** TS ≪ SA ≪ PSO on gap % under this protocol. SA tuning barely changed rankings under nearest-neighbor init; PSO remains weak despite tuning.

### JSP — **UI ready, tuning not started**

| Item | Status |
|------|--------|
| 7 instances on disk (ft10 → ta71) | Done |
| Web UI (instance × algorithm, live Gantt + convergence) | Done |
| Parameter tuning protocol | Not started |
| Final 30-run comparison benchmark | Not started |

Suggested split (not locked in decisions yet): tune on ft10, ta01, ta21; compare on ta31, ta51, ta71.

### Feature selection — **UI ready, tuning not started**

| Item | Status |
|------|--------|
| 8 EW datasets on disk | Done |
| Web UI (dataset × algorithm, live feature grid + convergence) | Done |
| ML design locked in `config/decisions.yaml` (D9) | Done |
| Parameter tuning protocol | Not started |
| Final 30-run comparison benchmark | Not started |

**FS design (locked):** Binary wrapper subset search; k-NN (k=5); stratified 5-fold CV on **train only**; objective `0.9 × CV_loss + 0.1 × feature_ratio`; 30% test holdout for reporting only.

---

## 3. Installation

### Requirements

- **Python 3.11+**
- **Node.js 18+** (for the web dashboard)
- Windows, macOS, or Linux

### Python environment

From the project root:

```bash
pip install -e ".[dev,web,ml,viz]"
```

| Extra | Purpose |
|-------|---------|
| `dev` | pytest, ruff |
| `web` | FastAPI, uvicorn |
| `ml` | scikit-learn, pandas (feature selection) |
| `viz` | matplotlib (post-run charts) |

### Node dependencies (first time only)

```bash
npm install
cd web/frontend && npm install && cd ../..
```

### Datasets (if missing)

```bash
python scripts/download_datasets.py
```

See `datasets/README.md` for sources.

---

## 4. Running the website (recommended)

### One command (dev mode)

From the project root:

```bash
npm run dev
```

This starts:

| Service | URL | Notes |
|---------|-----|-------|
| **React UI** | http://127.0.0.1:5173 | Vite dev server |
| **FastAPI** | http://127.0.0.1:8002 | Proxied via `/api` from the UI |

Press `Ctrl+C` once to stop both.

If ports are stuck from a previous session:

```bash
npm run dev:clean
npm run dev
```

### What you can do in the UI

| Route | Purpose |
|-------|---------|
| `/` | Home — links to each domain |
| `/domains/tsp` | TSP experiments (all 6 instances, 3 algorithms, 30-run batches) |
| `/domains/scheduling` | JSP experiments (7 instances) |
| `/domains/feature-selection` | FS experiments (8 EW datasets) |
| `/results` | Results dashboard |
| `/experiments/{id}` | Detail view for one result folder |

Each domain page: pick **instance/dataset + algorithm** → **Run experiment** (30 seeds). Rerun replaces prior results for that pair. While running: live progress, domain-specific visualization, convergence chart.

| Domain | Live visualization |
|--------|-------------------|
| TSP | Tour map |
| JSP | Gantt chart |
| FS | Feature grid (squares light up when selected) |

### Production build (optional)

```bash
npm run serve
```

Opens API + built frontend at http://127.0.0.1:8000 (see `optimize serve --with-frontend`).

---

## 5. Running from the CLI (without UI)

Set Python path if not using editable install:

```bash
# Windows PowerShell
$env:PYTHONPATH = "src"

# Linux/macOS
export PYTHONPATH=src
```

### List domains and algorithms

```bash
python -m optimize.ui.cli list
```

### Run a single experiment config

```bash
python -m optimize.ui.cli run --config config/examples/tsp_kroA100_comparison.json
```

### TSP tuning (already executed — for reproduction)

```bash
python scripts/run_tsp_tuning.py
python scripts/run_tsp_tuning.py --protocol config/tuning/tsp_tuning_protocol_v2.json --output results/tuning_v2 --generated-dir config/tuning/generated_v2
python scripts/run_tsp_tuning.py --protocol config/tuning/tsp_tuning_confirm_nn.json --output results/tuning/nn_confirm --generated-dir config/tuning/generated_nn_confirm
python scripts/apply_nn_confirm_tsp_parameters.py
python scripts/apply_final_tsp_parameters.py
```

### Resume an interrupted experiment folder

```bash
python scripts/resume_experiment.py --experiment-dir results/2026-08-06_220149_tsp_ch130_comparison --from-run-id particle_swarm_run_011
```

### Tests

```bash
pytest
```

---

## 6. Project layout

```text
documentation v1.md          ← this file (current guide)
old documentation/             ← archived specs (overview, pipeline, standard, tuning log)
literature/                    ← citations + methodology references (BibTeX)
config/
  decisions.yaml               ← locked research decisions (D1–D12)
  examples/                    ← experiment JSON templates
  tuning/                      ← TSP tuning protocols
datasets/                      ← TSP, JSP, feature-selection benchmarks
results/                       ← experiment output (gitignored)
scripts/                       ← tuning, download, dev API, resume helpers
src/optimize/                  ← Python application
web/frontend/                  ← React dashboard
```

---

## 7. Benchmark standards (summary)

### Fair comparison rules (all domains)

1. **Same evaluation budget** per run (TSP: 100k evals; JSP: 50k; FS: 5k).
2. **Equal tuning effort** per algorithm (grid search, same instances, same runs per config).
3. **Tune on set A, score on set B** — never report tuning instances as final results.
4. **Freeze parameters** before final comparison runs.
5. **Same domain settings** for all algorithms (init, operators, ML pipeline for FS).
6. Report honestly; no universal-winner claims.

Detailed TSP tuning history: [`old documentation/tuning_documentation.md`](old%20documentation/tuning_documentation.md).  
Literature support: [`literature/methodology_references.md`](literature/methodology_references.md).

### TSP instance split (6 active)

| Role | Instances |
|------|-----------|
| Tuning | eil51, berlin52, st70 |
| Comparison (paper) | kroA100, ch130, rat195 |
| Archived | kroB100, tsp225 → `datasets/tsp/removed/` |

### TSP frozen parameters (final)

| Algorithm | Settings |
|-----------|----------|
| SA | T₀=3000, cooling=0.9995, 200 moves/temp |
| TS | tabu tenure=15, candidate list=100 |
| PSO | swarm=100, w=0.6, c1=c2=1.8 |
| Domain | nearest-neighbor init, 30 runs, 100k evals |

Sources: SA from v1 NN tuning; TS/PSO from NN confirmation (`results/tuning/nn_confirm/`).

---

## 8. Key files and artifacts

| Path | Purpose |
|------|---------|
| `results/tuning/selected_parameters.json` | Frozen TSP parameters |
| `config/decisions.yaml` | Decision registry |
| `literature/references.bib` | Paper bibliography |
| `config/examples/tsp_*_comparison.json` | TSP comparison configs (updated with frozen params) |
| `src/optimize/api/services/tsp_catalog.py` | TSP UI catalog + dynamic configs |
| `src/optimize/api/services/jsp_catalog.py` | JSP UI catalog |
| `src/optimize/api/services/fs_catalog.py` | FS UI catalog |

---

## 9. Next steps (recommended order)

### Immediate (TSP — analysis, not more runs)

0. **Run the audit checklist** — [`audit_checklist.md`](audit_checklist.md) (P0 items first; evidence required for each check).
1. **Aggregate TSP results** from the three canonical comparison folders (gap %, runtime, convergence).
2. **Inferential statistics** — Friedman across algorithms per instance; pairwise Wilcoxon with correction (spec in literature folder; not fully automated yet).
3. **Write TSP results section** using frozen protocol + `literature/references.bib`.

### JSP (next domain to calibrate)

1. Lock instance split (tuning vs comparison) in `config/decisions.yaml`.
2. Create `config/tuning/jsp_tuning_protocol.json` (mirror TSP equal-effort grid).
3. Run tuning → freeze → 30-run comparison on held-out instances.
4. Optional: document in `standard_jsp.md` or extend this file to v2.

### Feature selection

1. Lock tuning/comparison dataset split (e.g. tune on ZooEW, BreastEW, SonarEW; compare on held-out EW sets).
2. Create `config/tuning/fs_tuning_protocol.json`.
3. Run tuning → freeze → final benchmark.
4. Consider post-run **feature frequency** charts across 30 runs.

### Platform / paper

1. Machine disclosure if results are merged from multiple computers (same configs required).
2. Keep `documentation v1.md` updated when JSP/FS benchmarks complete (→ v2).
3. Optional: hold-out re-run on archived TSP instances only if a reviewer asks.

---

## 10. Troubleshooting

| Problem | Fix |
|---------|-----|
| UI shows “Could not load instances” | Restart `npm run dev` after API changes |
| API connection errors on page load | `wait_for_api.py` waits for port 8002; ensure `dev:api` is running |
| Port already in use | `npm run dev:clean` |
| Feature selection fails | Install ML extras: `pip install -e ".[ml]"` |
| sklearn import error | Same as above |

---

## 11. Where to look for more detail

| Topic | Location |
|-------|----------|
| Full original requirements | `old documentation/metaheuristic_optimization_project_overview.md` |
| Pipeline / phases | `old documentation/pipeline_definition.md` |
| TSP fair-comparison standard | `old documentation/standard.md` |
| TSP tuning log (v1, v2, NN confirm) | `old documentation/tuning_documentation.md` |
| Citations | `literature/` |
| Locked decisions | `config/decisions.yaml` |
| Dataset provenance | `datasets/README.md` |

---

*Documentation v1 — reflects project state after TSP benchmark completion and unified web UI for all three domains.*
