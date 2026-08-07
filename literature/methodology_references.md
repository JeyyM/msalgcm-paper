# Methodology references — equal opportunity & calibration

This document maps **project protocol choices** to **published guidance**. It supports the TSP tuning described in [`tuning_documentation.md`](../old%20documentation/tuning_documentation.md) and [`standard.md`](../old%20documentation/standard.md).

---

## 1. Equal opportunity (fair comparison)

### What we do

| Protocol element | Our implementation |
|------------------|-------------------|
| Same evaluation budget | 100,000 objective evaluations per run (all algorithms) |
| Same problem instances per phase | Shared tuning set; shared comparison set |
| Same run count policy | 5 runs/config during tuning; 30 runs final comparison |
| Same tuning effort per algorithm | 4–6 configurations × 3 instances × 5 runs each |
| Separate tuning and scoring instances | eil51, berlin52, st70 → tune; kroA100, ch130, rat195 → score |
| Freeze before final benchmark | `selected_parameters.json` → comparison JSONs |

### Literature support

**Equal computational effort**

> Fairness is commonly defined as comparing algorithms under the **same amount of computational effort**, typically the **same number of objective function evaluations** (not necessarily the same wall-clock time or iteration count).

- Cohen, P. R. (2013). *Significance relations for the benchmarking of meta-heuristic algorithms.* arXiv:1311.1338.  
- IEEE CEC competition protocols (e.g. CEC 2017) specify a fixed maximum number of function evaluations per dimension for all entrants.

**Why equal parameter *effort*, not equal parameter *values***

> Algorithms need different parameter names and ranges; fairness requires **comparable tuning budget and methodology**, not identical numeric settings.

- Molina, D., et al. (2020). *Why tuning the control parameters of metaheuristic algorithms is so important for fair comparison.* MENDEL, 26(2). DOI: [10.13164/mendel.2020.2.009](https://doi.org/10.13164/mendel.2020.2.009)
- García, S., et al. (2021). *Fairness in bio-inspired optimization research: A prescription of methodological guidelines for comparing meta-heuristics.* Swarm and Evolutionary Computation, 69. DOI: [10.1016/j.swevo.2021.100973](https://doi.org/10.1016/j.swevo.2021.100973)

**Tuning set ≠ test set**

> **Offline** configuration must use training instances; final performance is reported on **held-out** instances to reduce overfitting to tuning cases.

- Birattari, M. (2009). *Tuning metaheuristics: A machine learning perspective.* Springer. (Iterated F-race / racing framework)
- López-Ibáñez, M., et al. (2016). *The irace package: Iterated racing for automatic algorithm configuration.* Operations Research Perspectives, 3, 43–58. DOI: [10.1016/j.orp.2016.09.002](https://doi.org/10.1016/j.orp.2016.09.002)

**No universal winner (limits of claims)**

> Performance rankings are **instance-dependent**; no algorithm dominates all problems.

- Wolpert, D. H., & Macready, W. G. (1997). *No free lunch theorems for optimization.* IEEE Transactions on Evolutionary Computation, 1(1), 67–82.

---

## 2. How calibration is documented in the field

### Baseline documented approaches (what “correct” looks like)

| Approach | Description | Used in this repo? |
|----------|-------------|------------------|
| **Manual grid / factorial search** | Small grids on training instances; pick best by aggregate metric | **Yes** (TSP v1/v2) |
| **Racing / F-Race / irace** | Sequential statistical elimination of configs; fixed evaluation budget | No (cited as gold standard) |
| **SMAC / ParamILS** | Model-based configurator | No |
| **Literature-default parameters** | Use “recommended” settings from source papers | Starting point only (Molina 2020 warns this is insufficient alone) |
| **Adaptive / online tuning during run** | e.g. adaptive SA temperature | Out of scope (offline freeze preferred for comparison) |

Our grid search is a **deliberate simplification** of offline tuning described by Birattari (2009) and López-Ibáñez et al. (2016): same separation of tuning vs production instances and fixed evaluation budget, but without iterative racing.

### Selection metric

We use **mean gap %** to known TSPLIB optima on tuning instances — standard for TSP when optima exist (Reinelt TSPLIB; Applegate et al. Concorde line of work).

Alternative metrics in literature:
- Raw tour length (instance-specific scale — poor for cross-instance aggregation)
- Relative rank across configs (Borda / Friedman-style — Cohen 2013)

---

## 3. Statistical analysis (planned, not all implemented yet)

Project spec (`metaheuristic_optimization_project_overview.md` §11) aligns with:

| Test | Use | Reference |
|------|-----|-----------|
| Friedman test | Multiple algorithms across instances | Friedman (1937); Demšar (2006) |
| Wilcoxon signed-rank | Pairwise post-hoc | Wilcoxon (1945); García et al. (2010) |
| Holm–Bonferroni / Hochberg | Multiple comparison correction | García et al. (2021) guidelines |

- García, S., et al. (2010). *Advanced nonparametric tests for multiple comparisons in the analysis of experimental data.* IEEE CEC 2010.
- Demšar, J. (2006). *Statistical comparisons of classifiers over multiple data sets.* JMLR, 7, 1–30.

---

## 4. TSP benchmark instances

| Source | Role in project |
|--------|-----------------|
| Reinelt (1991) — TSPLIB | Instance files in `datasets/tsp/instances/` |
| TSPLIB95 known optima | `datasets/tsp/metadata.json` gap calculation |

- Reinelt, G. (1991). *TSPLIB — A traveling salesman problem library.* ORSA Journal on Computing, 3(4), 376–384.

---

## 5. Mapping literature → our TSP tuning passes

| Design choice | Primary references | Our v1 / v2 / final |
|---------------|-------------------|---------------------|
| Equal configs per algorithm | García 2021; Molina 2020 | 4 (v1) / 4–6 (v2) each |
| Fixed eval budget | Cohen 2013; CEC rules | 100k |
| Hold-out instances | Birattari 2009; irace docs | Yes |
| NN vs random init sensitivity | Johnson & McGeoch TSP heuristic literature; Dréo 2006 | v1 NN; v2 random; **final NN** |
| SA cooling grid 0.995–0.9997 | Kirkpatrick 1983; Dréo 2006 (α ≈ 0.8–0.99) | Tested |
| TS tenure & candidate list | Glover 1989; Gendreau & Potvin | Tested |
| PSO swarm / inertia | Kennedy & Eberhart 1995; Shi & Eberhart 1998 | Tested; swarm 50–100 |

---

## 6. What to cite in the paper (minimal set)

**Methodology (fair comparison):**
1. García et al. (2021) — methodological guidelines  
2. Molina et al. (2020) — importance of tuning for fair comparison  
3. Birattari (2009) or López-Ibáñez et al. (2016) — offline tuning / train-test split  
4. Wolpert & Macready (1997) — scope of claims  

**Algorithms:**
5. Kirkpatrick et al. (1983) — SA  
6. Glover (1989) — Tabu Search  
7. Kennedy & Eberhart (1995) — PSO  

**Benchmark & stats:**
8. Reinelt (1991) — TSPLIB  
9. Demšar (2006) or García et al. (2010) — Friedman / Wilcoxon workflow  

---

## 7. Internal project documents (not literature)

These guided implementation but are **not** peer-reviewed sources:

- [`standard.md`](../old%20documentation/standard.md) — plain-language benchmark standard  
- [`tuning_documentation.md`](../old%20documentation/tuning_documentation.md) — what we actually ran  
- [`pipeline_definition.md`](../old%20documentation/pipeline_definition.md) §8 — separate tuning pipeline  
- [`config/decisions.yaml`](../config/decisions.yaml) D12 — locked TSP tuning decision  
- [`metaheuristic_optimization_project_overview.md`](../old%20documentation/metaheuristic_optimization_project_overview.md) — requirements spec  
