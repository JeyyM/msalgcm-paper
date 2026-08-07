# Comparative Evaluation Analysis (Draft)

**Date:** 2026-08-07  
**Scope:** Sample tests for Simulated Annealing (SA), Tabu Search (TS), and Particle Swarm Optimization (PSO) across three problem domains.  
**Status:** TSP complete · JSP mostly complete (several partial batches) · Feature Selection PSO pending (excluded here).

Frozen parameters from tuning (`results/tuning/*_selected_parameters.json`) were applied to all comparison runs. Gap % = `(best_found − known_optimum) / known_optimum × 100` for TSP and JSP (lower is better).

---

## Research questions (from paper)

**Main RQ:** How do SA, TS, and PSO differ in effectiveness across route optimization, job scheduling, and feature selection?

**Supporting RQs:**

1. **TSP** — route quality, convergence, efficiency, scalability  
2. **JSP** — schedule quality (makespan), efficiency, convergence, scalability  
3. **FS** — predictive performance, feature reduction, cost, stability *(pending PSO)*  
4. Implementation requirements, parameter sensitivity, strengths/limitations  
5. Alignment of sample-test results with literature patterns  

---

## Experimental setup (comparison runs)

| Domain | Instances | Runs / algo | Eval budget | Selection metric (tuning) |
|--------|-----------|-------------|-------------|---------------------------|
| TSP | eil51, berlin52, st70, kroA100, ch130, rat195 | 30 | 100,000 | mean gap % |
| JSP | abz5, ta02, ta22, ta31, ta51 | 30 | 50,000 | mean gap % |
| FS | BreastEW, WineEW, LymphographyEW, SpectEW | 30 | 5,000 | mean best objective |

All three algorithms share the same operator sets per domain (swap, insertion, inversion; TSP adds two-opt). JSP uses longest-processing-time initial schedules; TSP uses random initial tours.

---

## TSP results (complete — 18/18 cells)

Known optima from TSPLIB metadata.

| Instance | Optimum | SA gap (best) | TS gap (best) | PSO gap (best) | Best algo |
|----------|---------|---------------|---------------|----------------|-----------|
| eil51 | 426 | 13.15% | **2.35%** | 65.73% | TS |
| berlin52 | 7542 | 8.46% | **0.33%** | 57.94% | TS |
| st70 | 675 | 18.96% | **3.85%** | 113.48% | TS |
| kroA100 | 21282 | 19.47% | **10.38%** | 211.84% | TS |
| ch130 | 6110 | 18.31% | **17.55%** | 264.45% | TS |
| rat195 | 2323 | 13.52% | **13.52%** | 222.47% | TS ≈ SA |

### TSP observations (RQ1, RQ5)

- **Tabu Search dominates solution quality** on every instance, often reaching within 0.3–4% of optimum on smaller instances and 10–18% on larger ones.
- **Simulated Annealing is consistently second**: gaps roughly 8–20% on best runs, with higher mean gaps (~20–27%) indicating variable seed quality.
- **PSO underperforms sharply** on permutation TSP under this encoding/budget: best gaps 58–264%, and mean gaps often exceed 100%. This matches literature noting PSO needs careful permutation operators and parameter tuning; random-key / swap-hybrid PSO variants often work better than naive position vectors.
- **Scalability:** TS’s advantage over SA **narrows** on ch130 and rat195 (TS ≈ SA at rat195 best gap). PSO’s gap **widens** with instance size — consistent with loss of diversity / weak neighborhood search on large permutations.
- **Efficiency:** TSP runs are fast (seconds per 100k evals on these sizes); runtime differences between algorithms are secondary to solution quality here.

**Literature alignment:** TS and SA as strong sequential search methods on routing; PSO mixed for discrete routing unless specialized — **supported**.

---

## JSP results (in progress — see dashboard for live counts)

Best known makespans (BKS) from Taillard / SchedulingLab metadata.

| Instance | BKS | SA gap (best) | TS gap (best) | PSO gap (best) | Status |
|----------|-----|---------------|---------------|----------------|--------|
| abz5 (10×10) | 1234 | 14.51% | **1.78%** | 3.16% | **Complete** |
| ta02 (15×15) | 1244 | 37.54%* | **8.28%** | 11.42% | SA partial (26/30) |
| ta22 (20×20) | 1600 | 56.69%* | **19.50%** | 22.94%* | SA/PSO partial |
| ta31 (30×15) | 1764 | 57.88% | **19.39%** | — | TS partial (23/30) |
| ta51 (50×15) | 2760 | 54.31% | 25.65%* | **30.91%** | TS partial (2/30) |

\*From best available batch at time of writing; re-run if not 30/30.

### JSP observations (RQ2, RQ5)

- **Tabu Search again leads on makespan** for all instances where comparison is available, with best gaps 1.8–19.5% vs BKS on completed batches.
- **On abz5, TS ≈ BKS (1.78%) and edges PSO (3.16%) and SA (14.51%)** — a clearer ranking than TSP because all three complete runs exist.
- **Simulated Annealing struggles on larger JSP instances** (ta22, ta31, ta51): best gaps 54–58%, suggesting insufficient intensification within 50k evals or weak escape from LPT starts.
- **PSO is competitive with TS on small JSP** (abz5) but falls behind on ta02/ta22 — middle ground between TS and SA, unlike TSP where PSO collapses.
- **Scalability:** gaps increase with jobs×machines for all algorithms; TS maintains the smallest gap where runs are complete.
- **Incomplete ta51 TS / ta31 TS / ta02–ta22 SA** — interrupted runs; dashboard shows live progress. Do not draw final conclusions on those cells until 30/30.

**Literature alignment:** TS widely reported strong on JSP; SA effective with enough cooling time; PSO used but often hybridized — **partially supported** (PSO better relative on JSP than TSP).

---

## Cross-domain patterns (Main RQ)

| Pattern | TSP | JSP |
|---------|-----|-----|
| Best overall quality | **TS** | **TS** (where complete) |
| Second | SA | PSO (small/medium) or SA |
| Weakest | PSO | SA on large instances |
| Stability (mean vs best gap) | TS tightest | TS tightest |
| Scalability stress | PSO degrades fastest | SA degrades on large ta |

**No single winner:** TS is the default choice when solution quality is paramount on these combinatorial structures. SA offers a simpler fallback with acceptable but noisier results. PSO is **domain-dependent**: relatively viable on JSP at small scale, **not competitive** on raw permutation TSP under this setup.

---

## Feature Selection (deferred)

SA and TS: **30/30 on all four comparison datasets** (BreastEW, WineEW, LymphographyEW, SpectEW).  
PSO: **not started** (assigned separately).  

FS has no known optimum; comparison uses weighted CV loss + feature-reduction objective in [0, 1]. Analysis for RQ3 will be added once PSO batches finish.

---

## Implementation & parameter notes (RQ4)

- **Equal evaluation budgets** enforce fair comparison (D10 design intent).
- **Tuning vs comparison instances** are disjoint per domain to reduce overtuning bias.
- **TS tenure / SA cooling / PSO swarm size** frozen from grid search on smaller tuning instances — algorithms are comparable but not globally re-tuned per instance size.
- **JSP LPT initialization** gives all algorithms the same starting makespan; improvements reflect search, not construction heuristics.
- **TSP random initialization** avoids NN bias (lesson from TSP v1 tuning).

---

## Limitations

1. Sample tests, not industrial-scale benchmarks.  
2. Single parameter set per algorithm per domain (no per-instance retuning).  
3. JSP cells incomplete at time of writing — treat partial rows as provisional.  
4. No statistical tests (Wilcoxon / Friedman) exported yet (D11 open).  
5. FS omitted until PSO complete.  
6. One machine, one codebase — external validity limited.

---

## Next steps

1. Finish JSP partial batches (ta02 SA, ta22 SA/PSO, ta31 TS, ta51 TS).  
2. Run FS PSO on four comparison datasets.  
3. Add FS section to dashboard and this document.  
4. Export run-level CSV for Wilcoxon / Friedman tests across seeds.  
5. Convergence plots: compare iteration-to-best curves (TS typically flat early; PSO TSP volatile).  
6. Integrate findings into Comparative Evaluation Framework section of the paper.

---

## Quick reference — gap to optimum (best of 30 seeds)

Values from `results/` best batch per instance × algorithm at draft time. Refresh via **Results Dashboard** (`/results`) or `GET /api/dashboard/comparison`.

**TSP:** TS wins all six instances on best gap.  
**JSP:** TS wins all five where TS batch has data; PSO second on abz5; SA weakest on instances ≥ ta22.

*This is a living document — update when new batches complete.*
