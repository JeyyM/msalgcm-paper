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

## Automatic tuning tools (not used, but standard reference)

If the project moves beyond manual grids:

- **irace** — López-Ibáñez et al. (2016), DOI 10.1016/j.orp.2016.09.002  
- **F-Race** — Birattari et al. (2002), *Metaheuristics* 3, 325–332  
- **Survey** — Huang, C., Li, Y., & Yao, X. (2020). A survey of automatic parameter tuning methods for metaheuristics. *IEEE TEVC*, 24(1), 201–216.

Huang et al. (2020) classify methods as **parameter tuning** (offline, before run) vs **parameter control** (online, during run). This project uses **offline tuning + freeze**, matching comparison-study best practice.
