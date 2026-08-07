# Algorithm parameter literature — SA, TS, PSO (TSP context)

Notes on **commonly documented parameters** and **typical calibration ranges** from the literature. These informed the grids in `config/tuning/tsp_tuning_protocol.json` and `tsp_tuning_protocol_v2.json`.

---

## Simulated Annealing

### Canonical parameters

| Parameter | Meaning | Literature guidance |
|-----------|---------|---------------------|
| Initial temperature `T₀` | Acceptance of uphill moves early | Set so initial acceptance rate ≈ 0.5–0.8 (Kirkpatrick et al., 1983; Dréo et al., 2006) |
| Final temperature `T_f` | Stop / negligible acceptance | Small ε > 0 |
| Cooling factor `α` | Geometric schedule `T ← αT` | Often **0.8–0.99**; slower cooling (α→1) usually better quality, more evals (Dréo 2006; TSP SA surveys) |
| Moves / plateau length | Steps at each temperature | Problem-specific; affects effective cooling speed |

### Key references

- Kirkpatrick, S., Gelatt, C. D., & Vecchi, M. P. (1983). Optimization by simulated annealing. *Science*, 220(4598), 671–680.
- Dréo, J., Pétrowski, A., Siarry, P., & Taillard, E. (2006). *Metaheuristics for hard optimization.* Springer. (Practical α, T₀ estimation)
- Johnson, D. S., & McGeoch, L. A. (1997). The traveling salesman problem: A case study in local optimization. In *Local search in combinatorial optimization*, Wiley.

### Our grids

- v1: `T₀ ∈ {1000, 3000}`, `α ∈ {0.999, 0.9995}`, moves/temp `{100, 200}`
- v2: added `T₀=5000`, `α=0.995`, `α=0.9997`

**Finding:** Under **nearest-neighbor** starts, schedules barely changed gap (v1). Under **random** starts, faster cooling (`α=0.995`) won on average but all gaps remained high — motivates NN for final benchmark.

---

## Tabu Search

### Canonical parameters

| Parameter | Meaning | Literature guidance |
|-----------|---------|---------------------|
| Tabu tenure | Memory length (steps) | Often fixed or randomly varied in `[τ_min, τ_max]`; typical values problem-dependent (Glover 1989; Gendreau & Potvin 2010) |
| Candidate list size | Neighbors evaluated per step | Larger list → more local search effort per iteration; common in TSP tabu implementations |

### Key references

- Glover, F. (1989). Tabu search — part I. *ORSA Journal on Computing*, 1(3), 190–206.
- Glover, F. (1990). Tabu search — part II. *ORSA Journal on Computing*, 2(1), 4–32.
- Gendreau, M., & Potvin, J.-Y. (Eds.). (2010). *Handbook of metaheuristics.* Springer. (Tabu search chapter)

### Our grids

- Candidate list: **50 vs 100**
- Tenure: **15, 25, 40**

**Finding:** **List size 100** consistently helped; v2 winner **tenure 15** with list 100 (`ts_short_tabu`).

---

## Particle Swarm Optimization (discrete / TSP)

### Canonical parameters

| Parameter | Meaning | Literature guidance |
|-----------|---------|---------------------|
| Swarm size `n` | Particles per generation | Common range **20–50** in early PSO; larger swarms cost more evals per “generation” |
| Inertia `w` | Momentum | Shi & Eberhart (1998): **w ≈ 0.4–0.9**; often decreased over time |
| Cognitive `c₁`, social `c₂` | Attraction to personal / global best | Frequently **c₁, c₂ ≈ 1.5–2.0** (Kennedy & Eberhart 1995; Eberhart & Shi 2000) |

### Key references

- Kennedy, J., & Eberhart, R. (1995). Particle swarm optimization. *IEEE ICNN*, 1942–1948.
- Shi, Y., & Eberhart, R. (1998). A modified particle swarm optimizer. *IEEE CEC*, 69–73.
- Eberhart, R. C., & Shi, Y. (2000). Comparing inertia weights and constriction factors in particle swarm optimization. *CEC 2000*.

### Our grids

- Swarm: **30, 50, 80, 100**
- `w ∈ {0.5, 0.6, 0.7}`, `c₁,c₂ ∈ {1.5, 1.8, 2.0}`

**Finding:** All configs remained **far from optimum** on TSP with our random-key/discrete encoding. **Swarm 100** was least bad (v2). Literature PSO tuning (Molina 2020) shows even “recommended” settings vary widely by problem — supports honest inclusion with limitation note.

---

---

## Job-Shop Scheduling (SA / TS / PSO applied to JSP, makespan objective)

The algorithm *mechanisms* (SA acceptance rule, TS memory/candidate list, PSO velocity update) are unchanged from the TSP sections above — only the neighborhood (operation-sequence moves: swap/insertion/inversion) and objective (makespan via serial schedule decode) differ. Parameter *ranges* below are recalibrated from the JSP-specific literature rather than reused blindly from the TSP grids, because published tabu tenure values for JSP are markedly smaller than for TSP.

### Simulated Annealing

| Parameter | Literature guidance for JSP |
|-----------|------------------------------|
| Cooling schedule | Van Laarhoven, Aarts & Lenstra (1992) use a 3-parameter schedule (initial/final control parameter + a "distance parameter" governing decrement speed); Markov chain length set to neighborhood size |
| Relative competitiveness | Watson et al. (2006) and van Laarhoven et al. note SA can reach high-quality JSP solutions but tabu search generally matches or beats it in far less runtime — informs the honest "PSO/SA weaker than TS" expectation carried over from TSP |

### Key references

- van Laarhoven, P. J. M., Aarts, E. H. L., & Lenstra, J. K. (1992). Job shop scheduling by simulated annealing. *Operations Research*, 40(1), 113–125.
- Watson, J.-P., Beck, J. C., Howe, A. E., & Whitley, L. D. (2006). Problem difficulty for tabu search in job-shop scheduling. *Artificial Intelligence*, 143(2), 189–217.

### Tabu Search

| Parameter | Literature guidance for JSP |
|-----------|------------------------------|
| Tabu tenure | Nowicki & Smutnicki's TSAB/i-TSAB (1996; Watson et al. 2006 deconstruction) uses a **fixed, small tenure ≈ 8** (empirical range 6–10) on standard benchmark sizes — much smaller than TSP's 15–40, because the critical-block neighborhood is far more restrictive |
| Candidate/neighborhood | Built from the critical-path / critical-block structure in the classic formulation; our simplified operator-based neighborhood uses a fixed candidate list size analogous to TSP's, varied for calibration |

### Key references

- Nowicki, E., & Smutnicki, C. (1996). A fast taboo search algorithm for the job shop problem. *Management Science*, 42(6), 797–813.
- Watson, J.-P., Whitley, L. D., & Howe, A. E. (2006). Deconstructing Nowicki and Smutnicki's i-TSAB tabu search algorithm for the job-shop scheduling problem. *Computers & Operations Research* (draft/technical report).

### Particle Swarm Optimization

No JSP-specific PSO tuning literature is as canonical as Nowicki/Smutnicki for TS; the general PSO parameter guidance (Kennedy & Eberhart 1995; Shi & Eberhart 1998) is reused, consistent with how PSO is applied to JSP via random-key decoding in the wider metaheuristics-for-scheduling literature (Xue et al. survey below, §PSO for combinatorial encodings).

### Our JSP grid (equal effort: 4 configs × 3 algorithms)

- SA: cooling factor `{0.995, 0.999, 0.9995}`, initial temperature `{3000, 8000}` (baseline retained + 3 variants)
- TS: tenure `{8, 20, 30}` (8 = literature-aligned TSAB value; 20 = prior default; 30 = long), candidate list `{40, 80}`
- PSO: swarm `{20, 40}`, inertia `{0.5, 0.6, 0.7}`, cognitive/social coefficients `{1.5, 1.8, 2.0}`

See `config/tuning/jsp_tuning_protocol.json` for the exact grid.

---

## Feature Selection (SA / TS / PSO wrapper, k-NN classifier)

Wrapper feature selection uses a metaheuristic to search the space of feature subsets, scoring each candidate subset by retraining/cross-validating a classifier (here, k-NN) — the "wrapper" concept originates with Kohavi & John (1997). Because SA/TS/PSO are the same general-purpose algorithms as in the TSP/JSP sections, their canonical parameters (cooling schedule, tabu tenure/candidate list, swarm/inertia/coefficients) carry over conceptually; the ranges below are recalibrated for wrapper-FS scale (5,000-evaluation budget, feature counts 13–500 in our EW benchmark suite, objective bounded in \[0, 1\] rather than an unbounded tour length or makespan).

### Key references

- Kohavi, R., & John, G. H. (1997). Wrappers for feature subset selection. *Artificial Intelligence*, 97(1-2), 273–324. (Founding wrapper-FS reference; motivates our CV-loss + feature-ratio weighted objective)
- Xue, B., Zhang, M., & Browne, W. N. (2016). Particle swarm optimisation for feature selection in classification: A multi-objective approach. *IEEE Transactions on Cybernetics*, 43(6), 1656–1671. (PSO swarm/inertia guidance transferred to binary/rank-decoded feature masks)
- Ma, B., et al. (2023). A multistart tabu search-based method for feature selection in medical applications. *Scientific Reports*, 13, 17755. Tested tabu tenure `∈ {n/2, n, 2n, 5n}` (n = #features) and diversification parameter `α ∈ {0, 0.1, 0.5, 0.9, 0.99, 1}` on medical wrapper-FS datasets of comparable scale to our EW suite; found **tenure ≈ n/2** and high `α` (persistence) performed best.
- Hall, M. A., & Holmes, G. (2003). Benchmarking attribute selection techniques for discrete class data mining. *IEEE TKDE*, 15(6), 1437–1447. (Source of the equal-width discretization protocol already used to build our EW datasets — see `datasets/feature_selection/metadata.json`.)

### Our FS grid (equal effort: 4 configs × 3 algorithms)

- SA: cooling factor `{0.99, 0.995, 0.998}`, initial temperature `{1.0, 2.0}` (objective is bounded in [0,1], so absolute temperature is far smaller than the TSP/JSP grids — consistent with Kirkpatrick's "acceptance ≈ 0.5–0.8" guidance applied to a bounded objective)
- TS: tenure `{8, 15, 30}` — brackets the Ma et al. (2023) "≈ n/2" finding across our tuning datasets' feature counts (16–60), candidate list `{30, 50}`
- PSO: swarm `{15, 30}`, inertia `{0.5, 0.6, 0.7}`, cognitive/social coefficients `{1.2, 1.5, 1.8}` — same structure as Xue et al. (2016) recommended ranges

**Limitation (disclosed, not fixed):** Ma et al. (2023) scale tabu tenure *relative to* feature count per-dataset; we use fixed absolute values across all tuning datasets for implementation simplicity, matching how the TSP/JSP grids also use fixed absolute values despite instance-size variation. This is a known simplification, not an oversight — see `audit_checklist.md`.

See `config/tuning/fs_tuning_protocol.json` for the exact grid.

---

## Automatic tuning tools (not used, but standard reference)

If the project moves beyond manual grids:

- **irace** — López-Ibáñez et al. (2016), DOI 10.1016/j.orp.2016.09.002  
- **F-Race** — Birattari et al. (2002), *Metaheuristics* 3, 325–332  
- **Survey** — Huang, C., Li, Y., & Yao, X. (2020). A survey of automatic parameter tuning methods for metaheuristics. *IEEE TEVC*, 24(1), 201–216.

Huang et al. (2020) classify methods as **parameter tuning** (offline, before run) vs **parameter control** (online, during run). This project uses **offline tuning + freeze**, matching comparison-study best practice.
