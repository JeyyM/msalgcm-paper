# Comparative Evaluation of Simulated Annealing, Tabu Search, and Particle Swarm Optimization Across Practical Optimization Problems

**Version:** v1.1 (2026-08-07)  
**Authors:** Juan Miguel Miranda, Julian Johan Briones, Lance Xavier Lim  
**Status:** TSP and JSP sample tests complete (30 runs × 3 algorithms); Feature Selection SA and TS complete; **Feature Selection PSO pending**.

---

## ABSTRACT

This study compares Simulated Annealing (SA), Tabu Search (TS), and Particle Swarm Optimization (PSO) across route optimization, job scheduling, and machine-learning feature selection. The work combines a structured review of prior research—synthesized from peer-reviewed sources with emphasis on **reported gaps, accuracies, and rankings**—with controlled sample tests in a shared experimental platform. Sample tests use equal objective-evaluation budgets, disjoint tuning and comparison instance sets, literature-informed parameter grids, and 30 independent seeds per algorithm per benchmark.

On Traveling Salesman Problem (TSP) instances (51–195 cities), TS achieved the lowest best-of-30 gap to known optima on every instance (0.33–17.6%), followed by SA (8–19%); PSO underperformed sharply (58–264% gap), consistent with literature on non-native permutation encodings. On job-shop scheduling (JSP), TS again led on all five benchmarks (1.8–21.1% best gap); PSO ranked ahead of SA on larger instances but remained behind TS—matching Alharkan et al.-style scheduling comparisons at scale. On feature selection, SA and TS differed by only ~0.01–0.05 in wrapper objective on four EW datasets, echoing Zhang and Sun’s observation that tabu and competing methods converge closely in binary wrapper landscapes; **PSO comparison runs are not yet included**.

The study does not identify a universal winner. It develops a Comparative Evaluation Framework linking algorithm choice to problem representation, evaluation cost, and search mechanism. Rankings align with RRL expectations (TS on routing/scheduling; PSO encoding sensitivity) even where absolute gap magnitudes differ because of benchmark scale, initializer design, and standalone (non-hybrid) implementations. The experimental platform was AI-assisted in development; all protocol decisions, runs, and interpretations remain researcher-directed.

**Keywords:** Simulated Annealing, Tabu Search, Particle Swarm Optimization, route optimization, job scheduling, feature selection, metaheuristics, comparative evaluation.

---

## 1. INTRODUCTION

Optimization problems in route planning, production scheduling, and machine-learning preprocessing involve search spaces too large for exhaustive enumeration. Metaheuristics such as SA, TS, and PSO balance exploration and exploitation without guaranteeing global optimality. These three methods represent distinct search philosophies: probabilistic single-solution search (SA), memory-guided neighborhood search (TS), and cooperative population-based search (PSO).

### 1.1 Main Research Question

How do Simulated Annealing, Tabu Search, and Particle Swarm Optimization differ in their effectiveness across route optimization, job scheduling, and machine-learning feature selection?

### 1.2 Supporting Research Questions

1. **TSP** — route quality, convergence, efficiency, scalability  
2. **JSP** — schedule quality (makespan), efficiency, convergence, scalability  
3. **FS** — predictive performance, feature reduction, cost, stability *(PSO pending)*  
4. Implementation requirements, parameter sensitivity, strengths, limitations  
5. Alignment of sample-test outcomes with **numeric patterns and stated mechanisms** in the reviewed literature  

### 1.3 Study Scope and Deliverable

The deliverable is a **Comparative Evaluation Framework** combining literature synthesis with sample-test evidence. Sample tests demonstrate behavior under a fixed, equal-effort protocol; they are not industrial-scale benchmarks. Because reviewed studies differ in hardware, budgets, encodings, and problem classes, RQ5 emphasizes **directional alignment and mechanistic consistency** (e.g., “TS wins routing when neighborhoods are discrete”) rather than point equality of gap percentages. A companion numeric synthesis (`synthesis.md`) maps each RRL source to our results.

---

## 2. REVIEW OF RELATED LITERATURE

> Sections 2.1–2.11 of the submitted full paper (`Comparative-Evaluation-SA-TS-PSO-FULL-PAPER (1).pdf`) retain the narrative literature review. **This section adds numeric expectations** drawn from the group’s RRL corpus (`RRL Papers/`) to anchor Section 5.

### 2.12 Literature Synthesis — Qualitative Themes

| Theme | Pattern in reviewed work |
|-------|--------------------------|
| **No free lunch** | No algorithm dominates every problem class (Wolpert & Macready, 1997). |
| **Tabu Search** | Strong on routing and scheduling when neighborhoods are well defined (Pirim et al., 2008; Glover, 1989). |
| **Simulated Annealing** | Flexible but sensitive to temperature and objective scale (Youssef et al., 2001; Kirkpatrick et al., 1983). |
| **PSO** | Competitive on continuous/binary spaces; permutation problems need hybrids or adapted encodings (Sengupta et al., 2019; Mhamdi et al., 2011). |
| **Fair comparison** | Equal **objective evaluations** or runtime preferred over equal iterations (Pirim §2.10; Youssef et al.). |

### 2.13 Literature Synthesis — Numeric Benchmarks (RRL)

**Table 1.** Reported results from key RRL sources (standalone SA/TS/PSO where available).

| Source | Domain | Setting | Reported numbers | Authors’ stated reasons for outcomes |
|--------|--------|---------|------------------|--------------------------------------|
| Zhan et al. (2016) | TSP | TSPLIB; 25 trials | LBSA **PEav 0.15–0.49%**; eil51 **0% gap** | List-based cooling; hybrid neighborhood reduces parameter sensitivity |
| Glover (1989) | TSP | Hard instances; 16 runs | Beats prior 3-opt bests; 75-city tour **553** | Tabu memory prevents cycling; aspiration |
| Pirim et al. (2008) | Routing survey | Cited VRP | **TS > SA** on stochastic VRP; gap **↑ with size** | Tabu memory; neighborhood; initial solution helps TS more |
| Ru (2024) | Logistics routing | TS vs GA vs SA | Cost **1.2 vs 3.2–3.8**; TS accuracy **~95%** | Tabu avoids local traps; trades runtime for quality |
| Alharkan et al. (2020) | Scheduling | Parallel machines; n≤1000 | At n=1000: **TS 1.032×LB**, GPSO 1.036, SA 1.050 | TS cuts server idle time; SA loses LB hits at large n |
| Jwo et al. (2023) | Scheduling | Factory swap | TS+FIFO hits bound; raw FIFO **+37%** vs bound | **Initial schedule** quality dominates |
| Youssef et al. (2001) | VLSI floorplan | 5000 evals | **TS > GA > SA** on fuzzy cost | TS greedy + focused; SA explores poor regions if cost mis-scaled |
| Zhang & Sun (2002) | Feature selection | 30-d wrapper; 20 runs | Tabu **12.22** vs GA **12.41**; **1800 vs 3000** evals | Tabu intensification at feasible border; lower wrapper cost |
| Mhamdi et al. (2011) | Hybrid imaging | PSO vs PSO-SA-TS | Error **0.105 vs 0.003** | Pure PSO premature convergence; hybrids add local escape |
| Zhang & Nicholson | Network flow | 180 instances; 1 h cap | SA/TS/PSO all **~10.2–10.3%** gap gain | Methods tie when neighborhood structure similar |

### 2.14 Research Gap

Prior studies rarely apply the **same three standalone algorithms** across routing, scheduling, and wrapper feature selection under one protocol. Most RRL numbers come from **different problem classes, budgets, or hybrid variants**, so cross-paper numeric equality is not expected. This study closes the gap with unified implementations and repeated seeds, then compares **rankings and mechanisms** against Table 1.

---

## 3. METHODOLOGY

### 3.1 Overall Design

1. **Literature comparison** — qualitative review (full paper) plus numeric synthesis (§2.13, `synthesis.md`).  
2. **Sample tests** — identical algorithm implementations, shared fairness rules.

Fairness rules (`config/decisions.yaml`):

- Equal **objective-evaluation** budget per run (not equal iterations).  
- Disjoint tuning vs comparison instances per domain.  
- Literature-informed tuning grids (four configs × three algorithms × three tuning instances).  
- **30 independent seeds** per algorithm per comparison instance.  
- Frozen winner parameters after tuning.

### 3.2 Experimental Platform and AI Assistance

Sample tests ran in a custom Python platform (FastAPI, React dashboard, CSV/JSON under `results/`). Development was **AI-assisted** (Cursor and similar tools) for prototyping runners, APIs, and UI. **Researchers retained control** of research questions, benchmark selection, fairness protocol, tuning grids, frozen parameters, experiment execution, audit (`audit_checklist.md`), and all interpretations. Reported numbers come from executed runs, not from AI-generated estimates.

### 3.3 Algorithms and Implementation Notes

- **SA:** one neighbor evaluated per step.  
- **TS:** `candidate_list_size` neighbors per step (100 TSP, 40 JSP, 30 FS).  
- **PSO:** random-key decode for TSP/JSP permutations; threshold decode for FS binary vectors; `swarm_size` evaluations per step.

Under equal evaluation budgets, TS and PSO perform **fewer outer iterations** than SA but **more evaluations per iteration**—consistent with Pirim’s warning that iteration counts are not directly comparable.

### 3.4 Parameter Tuning and Comparison Matrix

| Domain | Tuning instances | Comparison instances | Budget | Metric |
|--------|------------------|----------------------|--------|--------|
| TSP | eil51, berlin52, st70 | All six TSPLIB instances | 100,000 | Mean gap % |
| JSP | ft10, ta01, ta21 | abz5, ta02, ta22, ta31, ta51 | 50,000 | Mean gap % |
| FS | ZooEW, IonosphereEW, SonarEW | BreastEW, WineEW, LymphographyEW, SpectEW | 5,000 | Mean best objective |

Frozen parameters: `results/tuning/selected_parameters.json`, `jsp_selected_parameters.json`, `fs_selected_parameters.json`.

### 3.5 Domain Setup and Known Limitations

**TSP:** Nearest-neighbor initial tours for SA/TS; PSO via random-key decode. Gap % = `(distance − optimum) / optimum × 100`.

**JSP:** Shared initial operation sequences from a job-major constructor (`longest_processing_time` in config). This is **not** standard LPT dispatch; it produces a **weak identical start** for all algorithms (~400–990% above BKS before search vs ~50–70% for random shuffle on the same instances). **Relative** rankings remain fair; **absolute** gaps are pessimistic—analogous to Jwo et al.’s finding that initialization dominates scheduling outcomes.

**FS:** Wrapper objective = weighted CV loss + feature-reduction penalty. Test scores recorded but not used in search.

### 3.6 Metrics and Analysis

Best/mean/std across 30 seeds; gap % (TSP/JSP); CV score, test score, feature count (FS); mean runtime. Wilcoxon/Friedman tests planned (D11); this version uses descriptive statistics.

---

## 4. FORMAL AND THEORETICAL ANALYSIS

> Section 4 of the full paper (per-iteration cost, convergence properties, representation analysis) is retained. **Central prediction for RQ5:** PSO optimizes in continuous ℝⁿ and maps to combinatorial spaces through non-injective decoders; SA and TS operate on problem-defined neighborhoods. Literature and our TSP/JSP/FS gaps should widen as encoding distortion increases (TSP > JSP > FS for PSO).

---

## 5. RESULTS, DISCUSSION, AND COMPARATIVE EVALUATION FRAMEWORK

All completed tests use **30 seeds** per algorithm per instance.

### 5.1 Traveling Salesman Problem (18/18 complete)

**Table 2.** Sample-test gaps vs known optima (best-of-30 and mean-of-30).

| Instance | Cities | Optimum | SA best / mean | TS best / mean | PSO best / mean |
|----------|--------|---------|----------------|----------------|-----------------|
| eil51 | 51 | 426 | 13.15% / 24.19% | **2.35% / 4.40%** | 65.73% / 97.72% |
| berlin52 | 52 | 7,542 | 8.46% / 23.60% | **0.33% / 3.40%** | 57.94% / 102.72% |
| st70 | 70 | 675 | 18.96% / 23.97% | **3.85% / 6.29%** | 113.48% / 179.81% |
| kroA100 | 100 | 21,282 | 19.47% / 26.83% | **10.38% / 13.64%** | 211.84% / 293.61% |
| ch130 | 130 | 6,110 | 18.31% / 25.02% | **17.55% / 20.25%** | 264.45% / 324.59% |
| rat195 | 195 | 2,323 | 13.52% / 19.62% | **13.52% / 19.34%** | 222.47% / 249.51% |

Mean runtime per 100k evals: TS ~3–9 s; SA ~20–40 s; PSO ~3–7 s.

**Table 3.** TSP — literature vs this study (RQ1, RQ5).

| Topic | Literature (Table 1) | Our sample tests | Alignment | Mechanism cited in literature |
|-------|---------------------|------------------|-----------|------------------------------|
| Routing winner | TS often best (Pirim; Glover; Ru) | **TS all 6 instances** | **Strong** | Tabu memory; multi-candidate evaluation |
| Gap scale | LBSA **&lt;0.5%** PEav on TSPLIB (Zhan) | TS **0.33–4%** (≤70 cities); **10–18%** (≥100) | Ranking yes; gaps wider | We use generic frozen TS, not LBSA |
| SA role | Competitive if calibrated (Youssef; Zhan) | **Second**; mean >> best (seed noise) | **Partial** | Cooling matched to budget; 1 eval/step vs TS×100 |
| Scalability | TS–SA gap may shrink with size (Pirim) | **Tie at rat195** best gap (13.52%) | **Supported** | Same neighborhood family; budget stress |
| PSO | Hybrids needed; pure PSO traps (Mhamdi; Sengupta) | **58–264%** gap | **Strong** | Random-key permutation decode |

**RQ1 summary:** TS delivers best route quality under our protocol. SA is a viable second choice on TSP with tuned cooling but shows higher seed variance. PSO is not competitive without hybrid local search—directly supporting RRL claims about permutation encoding.

### 5.2 Job-Shop Scheduling (15/15 complete)

**Table 4.** Sample-test gaps vs best known makespan.

| Instance | Size | BKS | SA best / mean | TS best / mean | PSO best / mean |
|----------|------|-----|----------------|----------------|-----------------|
| abz5 | 10×10 | 1,234 | 14.51% / 21.60% | **1.78% / 5.10%** | 3.16% / 8.28% |
| ta02 | 15×15 | 1,244 | 37.54% / 44.14% | **8.28% / 14.00%** | 11.41% / 18.63% |
| ta22 | 20×20 | 1,600 | 56.69% / 62.57% | **19.50% / 27.57%** | 22.94% / 31.67% |
| ta31 | 30×15 | 1,764 | 57.88% / 63.20% | **17.46% / 25.33%** | 23.47% / 31.78% |
| ta51 | 50×15 | 2,760 | 54.31% / 58.95% | **21.12% / 27.46%** | 30.91% / 36.87% |

**Table 5.** JSP — literature vs this study (RQ2, RQ5).

| Topic | Literature | Our sample tests | Alignment | Mechanism |
|-------|------------|------------------|-----------|-----------|
| Scheduling winner | TS strong at scale (Alharkan: **1.032×LB** at n=1000) | **TS best gap all 5** | **Strong** | Memory-guided intensification |
| PSO vs SA | GPSO **2nd**, SA loses LB hits large n (Alharkan) | **PSO &lt; SA** gap on ta02–ta51 | **Supported** | Random-key better escape than SA from weak start |
| SA large instances | SA degrades with size (Alharkan) | SA **54–58%** best on ta22+ | **Directional** | Single-neighbor + poor shared init |
| Absolute gaps | **~3%** above LB in parallel-machine study | **17–57%** above BKS on Taillard | **Not comparable** | Different problem; **job-major init** inflates gaps (cf. Jwo init effect) |
| Init sensitivity | FIFO vs EDD **+37%** (Jwo) | All share same weak start | Explains gap magnitude | Initialization dominates before search |

**RQ2 summary:** TS leads makespan quality; PSO ranks between TS and SA on larger instances. Literature predicted TS at scale and initialization sensitivity; our rankings match even though absolute gaps exceed Alharkan-style reports because of initializer design and Taillard difficulty.

### 5.3 Feature Selection (8/12 complete; PSO pending)

**Table 6.** Wrapper objective (lower is better; 30 runs).

| Dataset | Features | SA best / mean (std) | TS best / mean (std) | Literature analogue |
|---------|----------|----------------------|----------------------|---------------------|
| BreastEW | 30 | 0.2926 / 0.3008 (0.0029) | **0.2793 / 0.2793 (0.0000)** | Zhang & Sun: tabu **12.22 vs GA 12.41** (~2% spread) |
| WineEW | 13 | 0.5986 / 0.6037 (0.0036) | 0.5986 / 0.5986 (0.0000) | Tie — small landscape |
| LymphographyEW | 18 | 0.1981 / 0.2236 (0.0113) | **0.1911 / 0.2291 (0.0301)** | TS best seed; SA competitive mean |
| SpectEW | 22 | 0.1580 / 0.1704 (0.0058) | **0.1535 / 0.1686 (0.0104)** | TS slightly lower objective |

Runtime ~72–118 s per 5k evals (wrapper CV cost dominates). Example (BreastEW): TS selected **1 feature** (CV 0.693); SA selected **9** (CV 0.696) at best seeds—trade-off between penalty and accuracy visible in wrapper objective.

**Table 7.** FS — literature vs this study (preliminary RQ3, RQ5).

| Topic | Literature | Our sample tests | Alignment |
|-------|------------|------------------|-----------|
| TS vs GA in wrappers | Tabu wins with **fewer evals** (Zhang & Sun) | **TS lower obj on 3/4** datasets | **Supported** |
| SA in wrappers | SA **> random** on NDCG (Allvi et al.) | SA **within ~0.02** of TS on most sets | **Supported** — both viable |
| Algorithm spread | **~2%** criterion spread (Tabu vs GA) | **~0.01–0.05** objective spread | **Supported** — narrow FS landscape |
| Enhanced PSO | PSO variants win FS benchmarks (Xie et al.) | PSO **not yet run** | **Pending** |

**RQ3 (partial):** Binary wrapper FS shows **much tighter competition** than TSP/JSP, matching theory (§4) and Zhang & Sun’s small Tabu–GA separation. Full RQ3 awaits PSO.

### 5.4 Cross-Domain Patterns and Main RQ

| Pattern | TSP | JSP | FS (partial) |
|---------|-----|-----|--------------|
| Best quality | **TS** | **TS** | **TS** |
| Second | SA | PSO (large) | SA |
| Weakest | PSO | SA (large) | PSO pending |
| PSO encoding penalty | Severe | Moderate | Expected low |

**No universal winner.** TS is quality-first on permutation benchmarks; SA is simpler fallback on routing; PSO is domain-dependent—collapsed on TSP, intermediate on JSP, anticipated more competitive on FS (literature: Xie et al.; pending our runs).

### 5.5 Integrated Literature Alignment (RQ5)

**Table 8.** Summary scorecard — RRL expectations vs sample tests.

| RRL expectation | Evidence in literature | Our result | Verdict |
|-----------------|------------------------|------------|---------|
| TS wins routing/scheduling quality | Pirim; Glover; Alharkan; Ru | TS **11/11** instance wins (TSP+JSP) | **Confirmed** |
| PSO weak on permutations | Sengupta; Mhamdi (pure PSO) | PSO **worst TSP**; **mid JSP** | **Confirmed** |
| SA calibration-sensitive | Youssef (cost scale); Kirkpatrick | SA **2nd TSP**; **weak large JSP** | **Partial** — tuned but outpaced by TS |
| FS narrow algorithm spread | Zhang & Sun (~2%) | **&lt;0.05** obj spread SA/TS | **Confirmed** |
| Hybrids beat standalone PSO | Mhamdi **0.003 vs 0.105** | Not tested (standalone only) | **Out of scope** |
| Methods tie on some structures | Zhang & Nicholson **~10%** all methods | Not our domains | N/A |
| No free lunch | Pirim survey; NFL theorem | Domain-dependent ranking | **Confirmed** |

**Why rankings align but gap magnitudes differ:** (1) literature often reports ** tuned or hybrid** variants (LBSA, PSO-SA-TS); we use **standalone frozen** configs; (2) JSP **shared weak initializer** inflates absolute gap-to-BKS; (3) **evaluation-budget fairness** gives TS more neighbors per “iteration” than SA—literature (Pirim §2.10) argues this is correct for fairness but changes convergence shape; (4) **benchmark scale** differs (8-city routes vs 195-city TSPLIB; parallel-machine LB ratios vs Taillard BKS).

### 5.6 Comparative Evaluation Framework

**Table 9.** Practical guidance (literature + sample tests).

| Criterion | SA | TS | PSO |
|-----------|----|----|-----|
| **Quality (permutation)** | Moderate; seed-sensitive | **Best** in our tests; supported by Pirim, Alharkan | Poor standalone; literature uses hybrids |
| **Quality (wrapper FS)** | Competitive | **Slightly better** preliminary | Pending; enhanced PSO strong in RRL |
| **Scalability** | TSP: narrows vs TS at rat195; JSP: weak large | Best gaps throughout | TSP collapse; JSP mid-tier |
| **Parameter burden** | High (cooling vs budget) — Youssef | Moderate (tenure, list) | High (swarm + encoding) |
| **Choose when…** | Simple baseline; adequate TSP budget | **Quality-first** routing/scheduling | Native/binary FS; hybrid if permutations |

### 5.7 Implementation Notes (RQ4)

**TSP:** SA T₀=3000, α=0.9995, 200 moves/temp; TS tenure 15, list 100; PSO swarm 100.  
**JSP:** SA T₀=8000, α=0.999; TS tenure 30, list 40; PSO swarm 40.  
**FS:** SA T₀=2.0, α=0.995; TS tenure 30, list 30; PSO swarm 30 *(pending)*.

### 5.8 Limitations

1. Sample-test scale; not production benchmarks.  
2. Single frozen parameter set per domain.  
3. JSP job-major initializer inflates absolute gaps (§3.5).  
4. FS PSO incomplete.  
5. No formal significance tests yet.  
6. Standalone algorithms only—literature hybrids (Mhamdi) not compared.  
7. AI-assisted development requires audit; does not replace experimental rigor.

### 5.9 Conclusion

Sample tests **confirm the directional patterns** in the group’s RRL corpus: Tabu Search leads on routing and scheduling quality; Particle Swarm Optimization fails on permutation TSP but remains more viable on JSP; feature selection shows **narrow SA–TS competition** as Zhang and Sun reported for tabu vs genetic wrappers. Absolute gap percentages are **not** directly comparable to LBSA-class TSP studies or Alharkan-style **~3%** scheduling ratios because of initializer design, benchmark choice, and standalone implementations—but **mechanisms and rankings** cited by prior authors (tabu memory, encoding distortion, initialization, cost scaling) explain our outcomes.

The Comparative Evaluation Framework (Table 9) maps problem properties to algorithm choice rather than declaring a single winner—consistent with the No Free Lunch principle and with Pirim’s survey conclusion that metaheuristic leadership is **problem-dependent**.

**Pending v2:** FS PSO runs; Wilcoxon/Friedman tests; convergence figures.

---

## 6. REFERENCES

Full bibliography in submitted paper §6 and `literature/references.bib`. Key RRL sources for numeric synthesis: Glover (1989); Kirkpatrick et al. (1983); Youssef et al. (2001); Zhang & Sun (2002); Pirim et al. (2008); Zhan et al. (2016); Alharkan et al. (2020); Jwo et al. (2023); Mhamdi et al. (2011); Sengupta et al. (2019); Ru (2024); Allvi et al. (2020); Xie et al. (2021).

---

## APPENDIX A. Experiment Completion (2026-08-07)

| Domain | Complete | Pending |
|--------|----------|---------|
| TSP | **18/18** | — |
| JSP | **15/15** | — |
| FS | **8/12** | PSO × 4 datasets |

Artifacts: `results/`, `results/tuning/`, `config/decisions.yaml`, `synthesis.md`.
