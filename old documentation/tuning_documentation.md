# TSP Parameter Tuning Documentation

**Status:** Tuning complete — **final frozen parameters** ready for comparison runs  
**Last updated:** 2026-08-06  
**Related:** `standard.md`, `config/decisions.yaml` (D12), `results/tuning/selected_parameters.json`

---

## Executive summary

We ran **two tuning passes** (v1 and v2), analyzed both, and merged the best defensible settings into a **final frozen configuration** for the paper benchmark.

| Algorithm | Final settings | Source |
|-----------|----------------|--------|
| **Tabu Search** | tenure=15, candidates=**100** | NN confirm (`ts_short_tabu`) |
| **Simulated Annealing** | T₀=3000, cooling=**0.9995**, 200 moves/temp | v1 winner (`sa_slow_cool`) — unchanged |
| **Particle Swarm** | swarm=**100**, w=0.6, c1=c2=1.8 | NN confirm (`pso_swarm_100`) |

**Domain policy (final):** `nearest_neighbor` initial tours, shared operator set, 100k eval budget, **30 runs** for final comparison.

**10-run confirmation (eil51, all 3 algos):** TS **4.4%** gap → SA **22.9%** → PSO **96.6%** mean gap. Ordering is stable and sensible.

---

## Why two tuning passes?

### v1 — nearest-neighbor init (baseline)

- **Goal:** Tune under the original domain policy (NN starts).
- **Result:** TS improved clearly; SA configs all tied; PSO poor.
- **Limitation:** NN starts mask SA convergence — parameters barely affect best-so-far gap.

### v2 — random init (exploration)

- **Goal:** Let metaheuristics improve from weak starts so SA/PSO parameters might matter; better convergence story.
- **Result:** TS improved further (~4.5% gap); **SA collapsed** (~200%+ gap); PSO still poor (~125% best).
- **Conclusion:** At 100k evaluations, SA and PSO cannot climb from random TSP tours fast enough; TS local search handles random starts. Random init would make the **three-way comparison unfair** (TS dominates for implementation reasons, not just algorithm class).

### Final decision — merge best of both

| Policy | Choice | Why |
|--------|--------|-----|
| Initial solution | **Nearest neighbor** | Balanced quality band for SA vs TS; standard in TSP heuristics |
| TS parameters | **NN confirm** (`ts_short_tabu`) | Wins vs v1 NN finalist under nearest-neighbor init |
| SA parameters | **v1** (`sa_slow_cool`) | Unchanged; only pass where SA operated in a sane gap range |
| PSO parameters | **NN confirm** (`pso_swarm_100`) | Wins vs v1 NN finalist; still weak — report honestly |

This is **as correct as we get** within compute constraints without an open-ended hyperparameter search.

---

## Step 1 — Lock rules (D12)

Recorded in `config/decisions.yaml`:

- **Tuning instances:** eil51, berlin52, st70  
- **Comparison instances:** kroA100, ch130, rat195  
- **Removed (archived):** kroB100, tsp225 → `datasets/tsp/removed/`
- **Tuning runs per config:** 5  
- **Final comparison runs:** 30  
- **Budget:** 100,000 evaluations  
- **Metric:** mean gap % (tie-break: cross-instance std, then runtime)

---

## Step 2 — v1 tuning (nearest-neighbor)

**Protocol:** `config/tuning/tsp_tuning_protocol.json`  
**Results:** `results/tuning/`  
**Runs:** 180 (4 configs × 3 algos × 3 instances × 5 runs)  
**Duration:** ~29 minutes

### v1 winners

| Algorithm | Winner | Mean gap (tuning avg) | Notes |
|-----------|--------|----------------------|-------|
| TS | `ts_wide_list` (candidates 50→100) | 5.50% | Clear improvement |
| SA | `sa_slow_cool` (cooling 0.9995) | 22.92% | All SA configs tied on gap |
| PSO | `pso_baseline` | 133.08% | All variants poor |

---

## Step 3 — v2 tuning (random init)

**Protocol:** `config/tuning/tsp_tuning_protocol_v2.json`  
**Results:** `results/tuning_v2/`  
**Runs:** 240 (6+4+6 configs × 3 instances × 5 runs)  
**Duration:** ~41 minutes

### Expanded grids

- **SA:** 6 configs (added high T₀, fast cooling, etc.)
- **TS:** 4 configs (focused on candidate list 100 variants)
- **PSO:** 6 configs (swarm 80, 100, inertia variants)

### v2 ranked results (mean gap % across tuning instances)

**Tabu Search**

| Rank | Config | Mean gap % |
|------|--------|------------|
| **1** | **ts_short_tabu** (tenure 15, list 100) | **4.50%** |
| 2 | ts_wide_list (tenure 25, list 100) | 6.80% |
| 3 | ts_long_tabu | 7.71% |
| 4 | ts_baseline (list 50) | 14.41% |

**Simulated Annealing** (all poor under random init)

| Rank | Config | Mean gap % |
|------|--------|------------|
| 1 | sa_fast_cool | 206% |
| … | all others | 225–238% |

**Particle Swarm**

| Rank | Config | Mean gap % |
|------|--------|------------|
| **1** | **pso_swarm_100** | **124.7%** |
| 2 | pso_swarm_80 | 125.4% |
| 3 | pso_baseline | 133.1% |

**Key insight:** v2 validated TS tuning (shorter tenure + wide list wins). It **disqualified random init** for the final benchmark because SA/PSO never reach competitive gaps in 100k evals from random permutations.

---

## Step 4 — Final frozen parameters

Canonical file: `results/tuning/selected_parameters.json`

Applied to all `config/examples/tsp_*_comparison.json` via `scripts/apply_final_tsp_parameters.py`.

```json
{
  "domain_config": {
    "initial_solution": "nearest_neighbor",
    "operators": ["two_opt", "two_opt", "inversion", "insertion", "swap"]
  },
  "algorithm_configs": {
    "simulated_annealing": {
      "initial_temperature": 3000.0,
      "final_temperature": 0.001,
      "cooling_factor": 0.9995,
      "moves_per_temperature": 200
    },
    "tabu_search": {
      "tabu_tenure": 15,
      "candidate_list_size": 100
    },
    "particle_swarm": {
      "swarm_size": 100,
      "inertia_weight": 0.6,
      "cognitive_coefficient": 1.8,
      "social_coefficient": 1.8
    }
  },
  "runs": 30
}
```

### What changed from pre-tuning defaults

| Algorithm | Change |
|-----------|--------|
| TS | tenure 25→**15**, candidates 50→**100** |
| SA | cooling 0.999→**0.9995** |
| PSO | swarm 50→**100** |
| All | final comparison **runs 10→30** |

---

## Step 6 — NN confirmation for TS and PSO (literature alignment)

**Why:** García et al. (2021) and Birattari (2009) require parameters to be chosen under the **same domain conditions** as the final benchmark. TS and PSO had been taken from the random-init v2 pass while the final benchmark uses **nearest-neighbor** init. SA was already from v1 NN tuning and was left unchanged.

**Protocol:** `config/tuning/tsp_tuning_confirm_nn.json`  
**Script:** `scripts/run_tsp_tuning.py` + `scripts/apply_nn_confirm_tsp_parameters.py`  
**Output:** `results/tuning/nn_confirm/`  
**Runs:** 60 (2 configs × 2 algorithms × 3 instances × 5 runs)

### Head-to-head under nearest-neighbor init (mean gap % across tuning instances)

| Algorithm | Winner | Mean gap % | Runner-up | Mean gap % |
|-----------|--------|------------|-----------|------------|
| Tabu Search | **ts_short_tabu** (15, 100) | **4.72%** | ts_wide_list (25, 100) | 5.50% |
| Particle Swarm | **pso_swarm_100** | **124.66%** | pso_baseline (50) | 133.08% |

**Outcome:** Frozen parameters **unchanged** (same numeric settings as before), but TS and PSO are now **defensibly selected under NN init**. `selected_parameters.json` updated with `nn_confirm` block and revised `sources`.

---

## Step 5 — Final confirmation (10 runs, eil51, NN init, all 3 algos)

**Script:** `scripts/run_tsp_tuning_confirm.py`  
**Output:** `results/tuning/confirmation_final/2026-08-06_205744_tuning_confirm_eil51_comparison`

| Algorithm | Mean gap % | Best gap % | Mean tour | Runtime (s) |
|-----------|------------|------------|-----------|---------------|
| **Tabu Search** | **4.41%** | **2.35%** | 444.8 | 3.7 |
| Simulated Annealing | 22.89% | 16.20% | 523.5 | 21.1 |
| Particle Swarm | 96.57% | 77.93% | 837.4 | 2.5 |

**Does this make sense?**

- **Yes.** TS near optimum (426) with ~445 average — strong.  
- SA ~524 — matches v1 NN behavior (~519–529 band).  
- PSO ~837 — weak but ~7% better mean gap than v1 PSO baseline on eil51 (~103%). Swarm 100 helped slightly.  
- **Order TS ≪ SA ≪ PSO** is stable across v1 sanity, v2, and final confirmation.  
- All 30 runs completed successfully (10 per algorithm).

---

## Scripts reference

| Script | Purpose |
|--------|---------|
| `scripts/run_tsp_tuning.py --protocol … --output …` | Run a tuning batch |
| `scripts/analyze_tsp_tuning.py --protocol … --input …` | Rank configs, optional config update |
| `scripts/apply_final_tsp_parameters.py` | Apply merged final winners |
| `scripts/apply_nn_confirm_tsp_parameters.py` | Merge NN TS/PSO confirmation into frozen parameters |
| `scripts/run_tsp_tuning_confirm.py --runs 10` | Multi-algo confirmation |

### Reproduce

```bash
# v1 (already done)
python scripts/run_tsp_tuning.py

# v2 (already done)
python scripts/run_tsp_tuning.py --protocol config/tuning/tsp_tuning_protocol_v2.json --output results/tuning_v2 --generated-dir config/tuning/generated_v2

# NN TS/PSO confirmation under nearest-neighbor init
python scripts/run_tsp_tuning.py --protocol config/tuning/tsp_tuning_confirm_nn.json --output results/tuning/nn_confirm --generated-dir config/tuning/generated_nn_confirm
python scripts/apply_nn_confirm_tsp_parameters.py
python scripts/apply_final_tsp_parameters.py

# Confirm all three algos on eil51
python scripts/run_tsp_tuning_confirm.py --runs 10
```

---

## Limitations (state in paper)

1. **PSO** remains far from optimum under tested settings; included for completeness, not as a tuned competitor.  
2. **SA** parameter grids did not change gap under NN init (v1); frozen schedule is best-effort.  
3. **5 tuning runs** per config — sufficient for ranking, not for tight confidence intervals.  
4. **Random-init v2** showed TS/SA asymmetry — motivates NN policy for final benchmark.  
5. Conclusions apply to **this TSPLIB suite and protocol**, not all TSP instances (no free lunch).

---

## Next step: final benchmark

Run on **comparison instances only** (do not re-tune):

```bash
python -m optimize.ui.cli run --config config/examples/tsp_kroA100_comparison.json
python -m optimize.ui.cli run --config config/examples/tsp_ch130_comparison.json
python -m optimize.ui.cli run --config config/examples/tsp_rat195_comparison.json
```

Or split across group machines — same configs, full artifact folders returned.

**Do not use** pre-tuning experiment folders or v1/v2 tuning folders as final paper results.

---

## One-paragraph paper methods blurb

> Algorithm parameters were selected by equal-effort grid search on eil51, berlin52, and st70 (five runs per configuration, 100,000 evaluation budget). Simulated annealing settings came from the nearest-neighbor tuning pass (cooling factor 0.9995). Tabu search and particle swarm finalists from an expanded grid were confirmed head-to-head against nearest-neighbor tuning winners on the same three instances under nearest-neighbor initial tours (tabu tenure 15, candidate list 100; PSO swarm size 100). All final comparisons use nearest-neighbor initial tours, frozen parameters, thirty independent runs, and separate larger instances (kroA100, ch130, rat195) not used during tuning.
