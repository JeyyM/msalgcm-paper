# Key Protocol Fixes & Paper Update Checklist

**Date:** 2026-08-07  
**Status:** Experiments complete for TSP PSO (6×30) and FS v2 (3 datasets × 3 algos × 15). JSP and TSP SA/TS unchanged.

This document records what was broken, what was fixed in code, what was re-run, which result folders to use, and which paper sections must be updated.

---

## 1. Critical bugs fixed

### 1.1 TSP/JSP PSO — shared initializer ignored (D15)

**Problem:** PSO used random-key positions for all particles. `initial_solution: nearest_neighbor` in config was ignored. On eil51, initial gap was ~**234%** vs ~**23%** for SA/TS.

**Fix:** `src/optimize/algorithms/particle_swarm.py` — particle 0 (and ~25% perturbed copies) seeded from `create_initial_solution()` → `encode_for_pso()`. Helpers in `src/optimize/algorithms/pso_encoding.py`.

**Validation:** Post-fix init gap on eil51 ≈ **15–23%** (not 234%). Final PSO gaps on held-out instances are now in the same ballpark as SA/TS (~17–22% mean on eil51/berlin52/rat195).

**Re-run required:** All **6 TSP PSO** instances (30 seeds each). JSP PSO was already using a working initializer — **no JSP rerun**.

### 1.2 FS wrapper objective — protocol v2 (D9, D14)

**Problem (audit):**
- No per-fold feature standardization (train/test leakage risk).
- Weights α=0.9 / β=0.1 (too little accuracy emphasis).
- PSO crashed on FS (`dimension` not exposed) — fixed earlier in `problem.py`.

**Fix:** `src/optimize/domains/feature_selection/evaluator.py` — `StandardScaler` fit per CV fold; default `standardize_features: true`. Weights **α=0.99 / β=0.01** in all FS configs via `scripts/update_fs_protocol_configs.py`.

**Re-run required:** All FS comparison jobs under the new protocol. **Survival scope:** 3 datasets (WineEW, LymphographyEW, SpectEW), **15 seeds** (not 30). **BreastEW excluded** for compute.

### 1.3 FS PSO initializer

Same PSO seeding fix as TSP; FS PSO runs now complete (15/15 on all three datasets).

---

## 2. Canonical result folders (use these)

### TSP PSO (30/30 each — protocol v2 init)

| Instance | Folder |
|----------|--------|
| eil51 | `results/2026-08-07_115905_tsp_eil51_particle_swarm` |
| berlin52 | `results/2026-08-07_115905_tsp_berlin52_particle_swarm` |
| rat195 | `results/2026-08-07_115905_tsp_rat195_particle_swarm` |
| st70 | `results/2026-08-07_105830_tsp_st70_particle_swarm` |
| kroA100 | `results/2026-08-07_105830_tsp_kroA100_particle_swarm` |
| ch130 | `results/2026-08-07_105830_tsp_ch130_particle_swarm` |

**Do not use** older PSO folders where eil51/berlin52/rat195 show init gap ~234–792% (e.g. `105955`, `110207`, `105536` pre-fix batches).

### FS v2 (15/15 each)

| Dataset | SA | TS | PSO |
|---------|----|----|-----|
| WineEW | `2026-08-07_110128_fs_wineew_simulated_annealing` | `..._tabu_search` | `..._particle_swarm` |
| LymphographyEW | `2026-08-07_111413_fs_lymphographyew_*` | same prefix | same prefix |
| SpectEW | `2026-08-07_112041_fs_spectew_simulated_annealing` | `2026-08-07_113859_fs_spectew_tabu_search` | `2026-08-07_113904_fs_spectew_particle_swarm` |

**Do not use** pre-fix FS folders (30-run batches without `standardize_features` / 0.99 weights, e.g. `043315`, `043320`, `065536`).

### Unchanged (still valid)

- **TSP SA/TS** — all 6 instances × 30 seeds (pre-fix batches).
- **JSP** — all 5 comparison instances × 3 algos × 30 seeds.

---

## 3. Graphs regenerated (2026-08-07)

Run: `python scripts/export_paper_graphs.py`

Output: `Paper Setup/graphs/` + `manifest.json`

| Figure | File | Notes |
|--------|------|-------|
| 1–2 | `tsp_gap_*.png` | Includes **fixed PSO** (newest batch per instance) |
| 3 | `tsp_kroA100_convergence_combined.png` | PSO line updated |
| 4–5 | `jsp_gap_*.png` | Unchanged data |
| 6 | `jsp_ta22_convergence_combined.png` | Unchanged |
| 7 | `fs_best_objective_by_dataset.png` | **3 datasets only**, protocol v2 |
| 8 | `fs_wineew_convergence_combined.png` | **Replaces BreastEW** figure |
| 9–10 | TSP route / JSP gantt | Unchanged (TS best runs) |
| 11 | `fs_features_wineew_ts.png` | **Replaces BreastEW** |
| 12 | `tsp_kroA100_boxplot.png` | Unchanged |
| 13 | `fs_wineew_boxplot.png` | **Replaces BreastEW**, 15 seeds |

**Next step:** Re-embed figures in Word/PDF:
```powershell
python scripts/generate_comparative_evaluation_v2_docx.py
python scripts/generate_comparative_evaluation_v2_pdf.py
```
Update docx generator if it still references `fs_breastew_*` filenames.

---

## 4. Paper sections to adjust

### Abstract (§ front)

- [ ] Remove language that **invalidates PSO TSP** or marks gaps 58–264% as unreliable — PSO TSP is now valid after rerun.
- [ ] Update TSP PSO ranking/gap narrative with **new Table 4/5 numbers**.
- [ ] FS: state **15 independent runs** (not 30) for the three reported datasets; note **BreastEW omitted** in survival pass.
- [ ] FS: replace “raw features / α=0.9” limitation text with **protocol v2** (standardized folds, α=0.99/β=0.01).

### §3.4 Parameter tuning

- [ ] Clarify TSP tuning instances (eil51, berlin52, st70) vs **held-out comparison** (kroA100, ch130, rat195) — not “all six used for both.”

### §3.5 Domain setup / limitations

- [ ] Document **D15 PSO initializer fix** (brief — NN seed + perturbed copies).
- [ ] Document **FS protocol v2** (standardization, weights).
- [ ] Note FS comparison set for this draft: **WineEW, LymphographyEW, SpectEW** only.

### §5.1 TSP (Table 4, Table 5)

- [ ] **Recompute** all PSO rows from canonical folders above.
- [ ] Update discussion: PSO should no longer be dismissed as broken; compare fairly to SA/TS on held-out set.
- [ ] Revisit claim that TS wins **every** instance — verify against new PSO numbers.

### §5.2 JSP (Table 6, Table 7)

- [ ] **No rerun** — spot-check claims only:
  - PSO beats SA on **all 5** comparison instances (not “large only”).
  - TS leads on all five held-out benchmarks.

### §5.3 Feature selection (Table 8, Table 8b)

- [ ] Replace **30 runs** → **15 runs** in caption and text.
- [ ] Drop **BreastEW row** (or mark “not re-run in v2”) — table covers **3 datasets**.
- [ ] Recompute all objectives from v2 folders (values will differ from pre-fix).
- [ ] TS “lowest mean on 3/4” → revise to **2/3** or recompute after new numbers.
- [ ] Update Figure 7, 8, 11, 13 references (WineEW not BreastEW).

### §5.4–5.8 Cross-domain / limitations

- [ ] Remove “PSO TSP unresolved” limitation.
- [ ] Add: FS 15-run budget; BreastEW excluded; optional future extend to 30.
- [ ] Soften over-strong stability claims for TS on FS if not supported by 15-run stats.

### Appendix A

- [ ] Update completion matrix: TSP PSO **re-run complete**; FS **9/9 at 15/15** (not 12/12 at 30).

---

## 5. Writing / claim corrections (from audit — still apply)

| Claim | Correction |
|-------|------------|
| PSO beats SA on JSP “large instances only” | **All 5** comparison JSP instances |
| TS lowest FS mean on **3/4** datasets | Recompute; likely **2/4** pre-fix, **check 2/3** post-fix |
| TS “most stable” on FS | Do not overstate; cite variance / Wilcoxon if used |
| TSP tuning → held-out degradation for TS | TS **6.3×** vs SA **1.3×** — keep if numbers still hold |
| PSO TSP gaps 58–264% | **Replace** with post-fix gaps (~17–22% on held-out) |

---

## 6. Scripts reference

| Task | Command |
|------|---------|
| TSP PSO rerun | `python scripts/rerun_protocol_fix_experiments.py --tsp-only` |
| FS 15-run | `python scripts/rerun_protocol_fix_experiments.py --fs-only` |
| FS extend to 30 | `python scripts/rerun_protocol_fix_experiments.py --fs-only --fs-extend-to 30` |
| Export graphs | `python scripts/export_paper_graphs.py` |
| Regenerate Word | `python scripts/generate_comparative_evaluation_v2_docx.py` |

---

## 7. Quick sanity checks

**TSP PSO init gap (should be < 80%):**
```powershell
# eil51 latest folder — init gap ~23%, not ~234%
```

**FS config check:**
```json
"standardize_features": true,
"performance_weight": 0.99,
"reduction_weight": 0.01
```

**FS runs per batch:** `runs.csv` has **15** completed rows (not 30, unless extended later).
