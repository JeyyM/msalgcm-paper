# Benchmark audit checklist

**Purpose:** Adversarial QA — every way this project could be wrong, unfair, or paper-killing.  
**Use:** Work top-to-bottom by priority. Check off only with **evidence** (file path, command output, recomputed number).  
**Related:** [`documentation v1.md`](documentation%20v1.md), [`config/decisions.yaml`](config/decisions.yaml)

---

## Audit run log — 2026-08-07

Mechanical checks executed via [`scripts/audit_tsp_results.py`](scripts/audit_tsp_results.py) against the three
canonical comparison folders, plus manual verification of tuning protocol, TSPLIB references, operator code,
and feature-selection data leakage. Full pytest suite: **55/55 passed**.

**Verdict (TSP): no reruns required.** All P0 items on the three canonical TSP folders pass. Findings below are
documentation/framing gaps and hygiene issues, not correctness bugs.

**Update (same day, later pass): JSP and FS tuning protocols built and run.** Following the TSP audit, JSP and FS
were confirmed to have **no tuning protocol at all** (P0-15, P1-14) — algorithm parameters were hand-typed
defaults, never grid-searched. Built `config/tuning/jsp_tuning_protocol.json` and `fs_tuning_protocol.json`
(literature-grounded, equal-effort 4-configs-×-3-algorithms grids — see
[`literature/algorithm_parameter_literature.md`](literature/algorithm_parameter_literature.md)), plus generalized
`scripts/run_tuning.py` / `scripts/analyze_tuning.py` (domain-aware supersets of the TSP-only tuning scripts).
While building the FS grid, discovered and fixed a **real, previously-undiscovered P1 bug**: 4 of 8 EW datasets
(`ZooEW`, `LymphographyEW`, `SonarEW`, `IonosphereEW`) have string class labels that crashed the loader — see
finding 6 below. No prior results existed for those 4 datasets, so nothing needed a rerun because of this fix.
While *running* the FS tuning batch, also discovered and fixed a **second, more serious P0 bug**: PSO had never
worked at all on feature_selection, for any dataset — see finding 7 below. Both JSP and FS tuning batches have
since completed, been analyzed, and frozen: `results/tuning/jsp_selected_parameters.json` and
`results/tuning/fs_selected_parameters.json` are written and applied to
`config/examples/jsp_ft10_comparison.json` / `config/examples/fs_breastew_comparison.json`. Full suite: **56/56
passed** (grew from 55 after adding a PSO×FS regression test). JSP and FS are now genuinely ready for a
groupmate to run the final 30-run comparisons — not just "UI works," but tuned-and-frozen like TSP.

### What was checked (evidence-based, not just read-through)

| Check type | Scope | Result |
|---|---|---|
| Completeness, budget, seeds, status | 270 runs (3 folders × 90) | 100% pass |
| Gap % recomputation from raw distance | 270 solutions | 100% match, 0 mismatches |
| Tour validity + distance recompute from coordinates | 270 solutions | 100% valid permutations, 0 mismatches |
| Convergence CSV monotonicity + linkage to runs.csv | 270 files | 100% pass |
| Frozen params match configs | 3 canonical folders | 100% match |
| Known optima vs TSPLIB95 reference | 6 instances | 100% match |
| Full pytest suite | 55 tests | 55/55 pass |
| FS test-set leakage into optimizer | code trace | none found |
| FS objective weights silent-default risk | code trace | none — explicit required |

### New findings from this audit (not previously tracked)

1. **Two complete duplicate result folders** existed (kroA100, ch130) — confirmed byte-identical to canonical
   folders, moved to `results/superseded/` (not deleted).
2. **`"two_opt"` and `"inversion"` are code-identical operators** (both do segment reversal) — the 5-slot
   operator list only samples 3 distinct moves, with reversal weighted 3×. Correct math, needs precise wording
   in the paper's methods section.
3. **Stale `.live.json` snapshot files** never cleaned up post-run (doubles file count in `solutions/`).
4. **Duplicate JSP metadata files** (`datasets/scheduling/metadata.json` vs `.../jsp/metadata.json`) that could
   drift out of sync — currently identical, so no active bug.
5. **`validate_tsp_output.py` is stale**; superseded by the new general-purpose `scripts/audit_tsp_results.py`.
6. **FS loader crashed on 4/8 EW datasets** — `ZooEW` (`"mammal"`), `LymphographyEW` (`"malign_lymph"`),
   `SonarEW` (`"Rock"`), `IonosphereEW` (`"g"`) store the original OpenML string class name in their `class`
   column instead of a numeric code, unlike `BreastEW`/`WineEW`/`SpectEW`/`MadelonEW`. `load_ew_dataset` only
   handled numeric labels (`int(float(value))`), so any experiment on these 4 datasets raised
   `ValueError: could not convert string to float`. **Fixed** in
   `src/optimize/domains/feature_selection/loader.py` with a deterministic sorted-string label encoder
   (`_encode_labels`); verified all 8 datasets now load with the correct class count (Zoo=7, Lymphography=4,
   Sonar/Ionosphere=2). `FeatureSubsetEvaluator._default_metric`'s existing `num_classes > 2` check already
   handles macro-F1 correctly for the now-fixed multiclass sets, no further change needed there.
7. **PSO never worked on feature_selection — for any dataset, ever (P0-severity).** While running the newly-built
   FS tuning protocol, all 60 PSO tuning runs (across all 3 tuning datasets × 4 configs × 5 seeds) came back with
   `status: failed`, `best_objective: inf`, `error_message: "unable to infer PSO dimension from problem"`.
   Root cause: `ParticleSwarmOptimization._infer_dimension` (`src/optimize/algorithms/particle_swarm.py`) only
   knows how to size the swarm via `problem.instance.num_cities/num_operations` (TSP/JSP) or a generic
   `problem.dimension` fallback — `FeatureSelectionProblem` had neither, so PSO+FS raised on the very first
   evaluation of every single run, with no result ever silently or partially produced. **Verified this affected
   zero prior results**: `Glob`-searched `results/` for any PSO×feature_selection folder — none existed anywhere
   in the repo, meaning nobody had run this combination successfully before this session; there was nothing to
   invalidate or rerun beyond the tuning batch itself. **Fixed** by adding a `dimension` property to
   `FeatureSelectionProblem` (`src/optimize/domains/feature_selection/problem.py`, returns `dataset.num_features`).
   **Root cause of why this was undetected for so long:** `tests/test_feature_selection.py` had a `simulated_annealing`
   smoke test (`test_fs_sa_smoke`) but no equivalent PSO smoke test — added `test_fs_pso_smoke` as a permanent
   regression guard. Deleted and reran all 12 affected PSO tuning experiment folders after the fix; full suite is
   now 56/56 passing (was 55/55 before this test was added). This is the most serious bug found in the entire
   audit — worse than the FS loader bug, because it silently produced no misleading numbers (it just errored), but
   it means "PSO vs SA vs TS on feature selection" as a research question had literally never been answerable
   until today.

### Tools produced

- [`scripts/audit_tsp_results.py`](scripts/audit_tsp_results.py) — reusable audit script; run any time with
  `python scripts/audit_tsp_results.py --all-canonical` or point it at any other folder name(s).
- [`scripts/run_tuning.py`](scripts/run_tuning.py) / [`scripts/analyze_tuning.py`](scripts/analyze_tuning.py) —
  domain-aware tuning runner/analyzer (TSP, JSP, FS) superseding the TSP-only `run_tsp_tuning.py` /
  `analyze_tsp_tuning.py` for new work.

---

## How to use this list

| Priority | Meaning |
|----------|---------|
| **P0 — Fatal** | Invalidates paper claims or benchmark fairness if wrong |
| **P1 — Embarrassing** | Reviewer or replication attempt likely catches it |
| **P2 — Important** | Weakens credibility; fix before submission |
| **P3 — Hygiene** | Consistency, maintainability, future-you sanity |

**Verification types:** `RUN` (execute), `READ` (inspect files), `RECOMPUTE` (manual math/code), `SCRIPT` (automate), `ASK` (external expert/reviewer simulation)

---

## P0 — Fatal (paper-killing)

### TSP protocol & fairness

- [x] **P0-01 — Comparison runs used frozen params, not defaults**  
  Verify `config/examples/tsp_*_comparison.json` and UI template `tsp_eil51_comparison.json` match `results/tuning/selected_parameters.json` (SA/TS/PSO params + NN init + operators).  
  **Verify:** `READ` diff selected_parameters vs examples; `SCRIPT` sync test.  
  **RESULT: PASS.** All three canonical `experiment_config.json` files have `algorithm_configs` and `domain_config.initial_solution=nearest_neighbor` byte-identical to `results/tuning/selected_parameters.json` winners. Verified by `scripts/audit_tsp_results.py`.

- [x] **P0-02 — Final results are from comparison instances only**  
  Paper folders must be kroA100, ch130, rat195 — not eil51/berlin52/st70 (tuning set).  
  **Verify:** `READ` `experiment_config.json` in each canonical results folder.  
  **RESULT: PASS.** Confirmed `instance` field in all 3 canonical folders is kroA100/ch130/rat195, matching `metadata.json` `role: comparison`.

- [x] **P0-03 — Canonical result folders are complete (90/90 each)**  
  30 runs × 3 algorithms; all `status=completed`; `stop_reason=evaluation_budget_exhausted`.  
  **Verify:** `RUN` count rows in `runs.csv` per folder.  
  **Folders:**  
  - `results/2026-08-06_214444_tsp_kroA100_comparison`  
  - `results/2026-08-06_220149_tsp_ch130_comparison`  
  - `results/2026-08-06_215320_tsp_rat195_comparison`  
  **RESULT: PASS.** All 3 folders: exactly 90 rows, 30 per algorithm, all `status=completed`, zero `error_message`.

- [x] **P0-04 — Same seeds across algorithms within each instance**  
  For paired comparison, seeds 1000–1029 must be reused for SA, TS, PSO in the **same** experiment batch (or provably identical across merged batches).  
  **Verify:** `READ` `seeds.csv` + `runs.csv` seed column per algorithm.  
  **RESULT: PASS.** All 3 folders: identical 30 seeds (1000–1029) reused across all 3 algorithms (paired design confirmed).

- [x] **P0-05 — Evaluation budget is exactly 100,000 per TSP run**  
  **Verify:** `READ` `objective_evaluations` column; no run stops early without documented reason.  
  **RESULT: PASS.** All 270 runs (90 × 3 folders) used exactly 100,000 evaluations; `stop_reason=evaluation_budget_exhausted` for 100% of runs (no early SA temperature-floor stops).

- [x] **P0-06 — Gap % formula is correct**  
  `gap = (distance - known_optimum) / known_optimum × 100` using values from `datasets/tsp/metadata.json`.  
  **Verify:** `RECOMPUTE` on 5 random solutions per instance; compare to `runs.csv` / solution JSON.  
  **RESULT: PASS.** Recomputed for all 90 solutions per folder (270 total), not just a sample — 0 mismatches (tolerance 0.01).

- [x] **P0-07 — Tour validity**  
  Each route is a permutation of `0..n-1`; stored `distance` matches recomputed tour length from coordinates.  
  **Verify:** `SCRIPT` extend `scripts/validate_tsp_output.py` for all 3 comparison folders.  
  **RESULT: PASS.** All 270 routes are valid permutations; all stored distances match recomputed tour length from raw `.tsp` coordinates; all solution distances match `runs.csv best_objective`. Superseded the stale `validate_tsp_output.py` (P1-08) with `scripts/audit_tsp_results.py`, which generalizes across folders/instances.

- [x] **P0-08 — Known optima are correct TSPLIB values**  
  Cross-check eil51=426, berlin52=7542, st70=675, kroA100=21282, ch130=6110, rat195=2323 against TSPLIB95 literature.  
  **Verify:** `READ` metadata + external source.  
  **RESULT: PASS.** All 6 values confirmed against TSPLIB95 official reference (comopt.ifi.uni-heidelberg.de/software/TSPLIB95) — exact match, zero discrepancy.

- [x] **P0-09 — Tuning vs comparison init mismatch is documented and defensible**  
  D12 notes v2 **random** init for exploration; **final** comparison uses **nearest_neighbor** (`selected_parameters.json`). SA tuned under NN; TS/PSO confirmed under NN (`nn_confirm`). Paper must state this clearly — not look like hidden switching.  
  **Verify:** `READ` `old documentation/tuning_documentation.md`, D12, paper draft.  
  **RESULT: DOCUMENTED, needs paper-methods paragraph.** The chain is real and defensible (v1 NN → v2 random exploration → NN confirm for TS/PSO → freeze) but is spread across 3 protocol files + decisions.yaml. Recommend a single explicit paragraph in the paper's methods section stating: "SA parameters selected under v1 nearest-neighbor-init tuning; TS/PSO parameters selected under v2 random-init exploration then reconfirmed under nearest-neighbor init (`nn_confirm`) to match final comparison conditions." No code/data issue — a writing task.

- [x] **P0-10 — No duplicate / superseded TSP result folders in paper tables**  
  Pre-tuning, smoke (10-run), or abandoned folders must not be cited.  
  **Verify:** `READ` results/ naming; `RUN` `prune_duplicate_tsp_experiments` logic; manual inventory.  
  **RESULT: FINDING (non-fatal).** Found two extra **complete, byte-identical duplicate** folders: `2026-08-06_212033_tsp_kroA100_comparison` and `2026-08-06_213601_tsp_ch130_comparison`. Diffed against canonical folders — `experiment_config.json` identical, and all 90 `best_objective` values identical per folder pair (confirms full determinism: same seed → same result, byte-for-byte). Not a correctness issue, but risk of citing the wrong folder by accident. **Recommend:** archive/delete the two duplicates now that this is confirmed safe (done below).

- [x] **P0-11 — ch130 PSO runs 011–030 are valid post-resume**  
  Interrupted batch was resumed; regenerated runs must match protocol (same config, seeds, budget).  
  **Verify:** `READ` run timestamps/parameters; compare PSO 001–010 vs 011–030 distributions for sanity.  
  **RESULT: PASS.** `scripts/audit_tsp_results.py` validates all 90 ch130 rows including PSO 011–030 — same budget, same route validity, same gap-formula correctness, no discontinuity. Additionally, the resumed 220149 folder is byte-identical to the earlier complete 213601 attempt across all 90 runs, confirming the resume didn't introduce drift.

### Feature selection (if used in paper before re-tuning)

- [ ] **P0-12 — Test set never enters optimizer objective**  
  `evaluate()` must use CV on train only; test only in `serialize_solution` / reporting.  
  **Verify:** `READ` `src/optimize/domains/feature_selection/problem.py` + `evaluator.py`; trace one run.

- [ ] **P0-13 — FS objective weights explicit in every config**  
  No silent defaults (`performance_weight`, `reduction_weight` required).  
  **Verify:** `READ` all `fs_*` configs and `fs_catalog` template.

- [ ] **P0-14 — MadelonEW never optimizes on official test labels**  
  **Verify:** `READ` loader/split logic for Madelon special case (D9).

### Cross-domain fairness (if comparing across domains in one narrative)

- [x] **P0-15 — Do not compare TSP (tuned) vs JSP/FS (defaults) as equal rigor**  
  JSP/FS algorithm params are **not** frozen via tuning protocol yet.  
  **Verify:** `READ` `jsp_ft10_comparison.json`, `fs_breastew_comparison.json` — document as exploratory only until tuned.  
  **RESULT: CONFIRMED — no equivalent freeze file exists.** `Glob` for `config/tuning/*jsp*` and `config/tuning/*fs*` returned **0 files** each; `results/tuning/` contains only TSP artifacts (`selected_parameters.json`, `tuning_run_manifest.json`). JSP/FS comparison templates carry hand-picked default parameters, never validated by a grid search. Confirmed no JSP or FS "final comparison" result folders exist yet either — only single-algorithm smoke batches (e.g. `jsp_ft10_simulated_annealing`, `fs_breastew_simulated_annealing`). **This is exactly why the answer to "does anything need rerunning" is TSP-only: there's nothing paper-final on JSP/FS to rerun — it hasn't been run once yet in final form.**  
  **FOLLOW-UP (same day):** Built and ran `config/tuning/jsp_tuning_protocol.json` / `fs_tuning_protocol.json` to close this gap.  
  **CLOSED (2026-08-07):** Both tuning batches completed, analyzed, and frozen. `results/tuning/jsp_selected_parameters.json` and `results/tuning/fs_selected_parameters.json` written; winning parameters applied to `config/examples/jsp_ft10_comparison.json` and `config/examples/fs_breastew_comparison.json`. All three domains (TSP, JSP, FS) now carry equal tuning rigor. See finding 7 below for a second, more serious bug (PSO×FS was completely non-functional) discovered while running this tuning batch.

---

## P1 — Embarrassing (reviewer likely catches)

### TSP tuning methodology

- [x] **P1-01 — Equal tuning effort claim**  
  Count configs per algorithm in each protocol:  
  - v1: SA=4, TS=4, PSO=4 ✓  
  - v2: SA=6, TS=4, PSO=6 ⚠️ TS grid smaller  
  Final merge: SA from v1, TS/PSO from NN confirm — document honestly; don't claim v2 alone was equal-effort for all three.  
  **Verify:** `READ` `config/tuning/tsp_tuning_protocol*.json`.  
  **RESULT: CONFIRMED, needs honest framing.** Verified by grep-counting `"id":` entries: v1 = SA 4 / TS 4 / PSO 4 (equal). v2 = SA 6 / TS 4 / PSO 6 (TS **not** expanded — unequal within v2 alone). `nn_confirm` = TS 2 / PSO 2 head-to-head (SA explicitly excluded per its own description field). Counting **distinct** configs ever tested end-to-end (nn_confirm configs overlap with v1/v2, so not additive): SA=10, TS=8, PSO=10. **Recommend:** paper states effort as "10/8/10 distinct configurations across two rounds," not "equal grid" — still defensible, just not perfectly symmetric.

- [x] **P1-02 — PSO structural disadvantage under shared eval budget**  
  PSO burns `swarm_size` evaluations per iteration vs SA/TS ~1 per step. Rankings may reflect encoding + budget interaction, not pure algorithm quality.  
  **Verify:** `READ` `particle_swarm.py`; decide narrative (fair same budget vs unfair — pick one and defend).  
  **RESULT: CONFIRMED BY CODE, standard practice — needs one sentence in methods.** `particle_swarm.py` calls `problem.evaluate()` once per particle per iteration (swarm_size=100 → 100 evals/iteration → ~1000 iterations at 100k budget), vs SA/TS ~1 eval/step (~100k steps). This is the standard "equal function-evaluation budget" convention in metaheuristic benchmarking (not a bug), but PSO's much lower iteration count is a legitimate explanation for its weaker gap% and should be stated explicitly rather than left for a reviewer to notice.

- [x] **P1-03 — PSO random-key decoding vs permutation-native operators**  
  TS/SA operate on permutations; PSO uses continuous random keys → decode. Cross-algorithm fairness argument needed.  
  **Verify:** `READ` `decode_for_pso` in TSP/JSP/FS domains.  
  **RESULT: CONFIRMED BY CODE.** `TSPProblem`/JSP/FS all implement `decode_for_pso` separately from `get_neighbors` (used by SA/TS). This is the standard way to adapt continuous PSO to combinatorial domains — defensible, but same as P1-02: state it explicitly as a methodological choice in the paper rather than letting it look unexamined.

- [x] **P1-04 — Duplicate `two_opt` in operators list**  
  `domain_config.operators`: `["two_opt", "two_opt", "inversion", "insertion", "swap"]` — doubles two-opt selection weight. Intentional or bug? Must be consistent in tuning and comparison.  
  **Verify:** `READ` configs; `READ` `random_operator` behavior.  
  **RESULT: FINDING — deeper than expected, still not fatal.** Read `src/optimize/domains/tsp/neighborhoods.py::apply_operator`: the `"inversion"` and `"two_opt"` branches execute **identical code** (`neighbor[i:j+1] = reversed(...)`) — this is mathematically correct (classic 2-opt *is* segment reversal), but it means the 5-slot operator list `["two_opt","two_opt","inversion","insertion","swap"]` actually samples only **3 distinct moves**: reversal (60%, via 3 of 5 slots), insertion (20%), swap (20%). Same list is used consistently in tuning and final comparison (verified — no drift). **Recommend:** paper's operator description should say "reversal-type moves (2-opt) weighted 3× relative to insertion/swap," not "4 operators" — otherwise a reviewer who reads the code will find an apparent inconsistency between the paper text and implementation. PSO is unaffected (uses `decode_for_pso`, never calls `get_neighbors`/this operator list).

- [x] **P1-05 — NN initial tour gives SA/TS head start vs random-init tuning narrative**  
  Under NN init, SA barely changed from v1; PSO still weak (~125% mean gap on tuning set in `selected_parameters.json`). Don't overclaim PSO tuning success.  
  **Verify:** `READ` nn_confirm aggregates.  
  **RESULT: CONFIRMED.** `results/tuning/selected_parameters.json` → `nn_confirm.particle_swarm.aggregate_mean_gap_percentage = 124.66%` on the tuning set itself (eil51/berlin52/st70), vs TS at `4.72%`. This is the tuning-set number, before even reaching the harder comparison instances. The existing documentation already states this honestly ("PSO weak but fairly tuned") — no change needed, just confirming the number is real and not a docs overclaim.

### Results integrity

- [ ] **P1-06 — UI launch vs CLI batch structure mismatch**  
  - CLI comparison: one folder, `tsp_kroA100_comparison`, 90 runs, all algos.  
  - UI launch: one folder per `(instance, algorithm)`, 30 runs each (`tsp_kroA100_simulated_annealing`, etc.).  
  Paper uses CLI-style folders; UI reruns must not accidentally replace/fragment canonical sets.  
  **Verify:** `READ` `tsp_catalog.build_tsp_config` experiment naming; inventory results/.

- [ ] **P1-07 — `selected_parameters.json` not loaded dynamically by UI**  
  Catalog copies static template (`tsp_eil51_comparison.json`). If JSON updated without re-running `apply_final_tsp_parameters.py`, UI drifts.  
  **Verify:** `SCRIPT` assert catalog output == selected_parameters.

- [x] **P1-08 — `validate_tsp_output.py` is stale**  
  Hardcoded to old 10-run eil51 folder and `EXPECTED_RUNS=10`. Cannot trust it for 30-run comparison audit without update.  
  **Verify:** `READ` script lines 13–18; **fix before use**.  
  **RESULT: CONFIRMED STALE — superseded, not fixed in place.** Left `validate_tsp_output.py` untouched (still useful as a historical/smoke check) and instead wrote `scripts/audit_tsp_results.py`, which generalizes to any folder, any instance, any run count, and additionally checks frozen-parameter matching (P0-01) and stop-reason distribution (P2-08) that the old script didn't cover. Use the new script going forward.

- [x] **P1-09 — Convergence CSV consistency**  
  Monotonic eval counts; non-increasing `best_objective`; matches `runs.csv` final values.  
  **Verify:** `SCRIPT` per comparison folder.  
  **RESULT: PASS.** All 270 convergence CSVs (90 × 3 folders): eval counts monotonic, `best_objective` non-increasing, final value matches `runs.csv`, first value matches `initial_objective`, final eval count never exceeds budget.

- [ ] **P1-10 — Initial objective consistency across algorithms (same seed)**  
  Under same seed + same init policy, SA/TS/PSO may differ in initial objective (expected for PSO vs others). Document if comparing "time to beat initial" — otherwise OK.  
  **Verify:** `READ` seed groups in runs.csv.

### Statistics & paper claims

- [ ] **P1-11 — No Friedman / Wilcoxon yet (D11 open)**  
  Claiming "significant" differences without tests is weak.  
  **Verify:** `READ` `config/decisions.yaml` D11; export + run external or implement tests.

- [ ] **P1-12 — No free lunch / overclaiming**  
  Avoid "TS is best metaheuristic." Scope claims to instances, budget, encoding.  
  **Verify:** `ASK` reviewer simulation on discussion section.

- [ ] **P1-13 — Runtime comparisons fair?**  
  Different eval patterns → runtime not apples-to-apples for "efficiency" claims unless normalized by evaluations used.  
  **Verify:** `READ` runtime_seconds vs objective_evaluations.

### JSP (before publishing JSP results)

- [x] **P1-14 — Instance split not locked in decisions.yaml**  
  Recommended tune/compare split exists in docs but not D4-style lock for JSP.  
  **Verify:** `READ` D6/D7; add tuning_instances / comparison_instances when ready.  
  **RESULT: CONFIRMED OPEN, then RESOLVED same day.** Split locked in `config/decisions.yaml` D7/D13: tuning = `[ft10, ta01, ta21]`, comparison = `[ta31, ta51, ta71]`, `ta41` excluded (see P1-15). Matches `config/tuning/jsp_tuning_protocol.json`.

- [x] **P1-15 — ta41 has null BKS**  
  Gap reporting impossible; exclude from gap tables or cite external upper bound.  
  **Verify:** `READ` jsp metadata.  
  **RESULT: CONFIRMED.** `datasets/scheduling/jsp/metadata.json` and its duplicate `datasets/scheduling/metadata.json` both have `"best_known_makespan": null` for ta41. Excluded from the formal tune/compare split (`config/decisions.yaml` D7); still runnable ad hoc via the UI/CLI catalog for anyone curious, just outside the paper-final comparison.

- [x] **P1-16 — ta21 dimensions vs literature (D6 note)**  
  Confirm 20×20 matches SchedulingLab / Taillard spec.  
  **Verify:** `READ` instance file header + literature.  
  **RESULT: CONFIRMED.** `Select-String` on `datasets/scheduling/jsp/instances/ta21.txt` line 1 reads `"20\t20"` (jobs × machines), matching `datasets/scheduling/jsp/metadata.json`'s `jobs: 20, machines: 20` and the SchedulingLab/Taillard reference. Updated `config/decisions.yaml` D6 to mark this verified.

- [x] **P1-17 — JSP decoder correctness**  
  SSGS from operation sequence produces valid schedule; makespan matches serialized value.  
  **Verify:** `RUN` `tests/test_scheduling.py` + manual spot check on ft10.  
  **RESULT: PASS (mechanical).** `tests/test_scheduling.py` passes (part of the 55/55 pytest run). Spot-checked one completed ft10 SA smoke batch (30 runs): all `status=completed`, `stop_reason=evaluation_budget_exhausted`, `objective_evaluations=50000`. Full gap-correctness audit (JSP equivalent of `audit_tsp_results.py`) not yet built — recommend before JSP becomes paper-final. **New finding:** `JSPProblem._load_known_optimum` falls back to a *different* file (`datasets/scheduling/metadata.json`) than the catalog's source of truth (`datasets/scheduling/jsp/metadata.json`) if `known_optimum` isn't explicitly passed in config. The two files currently have identical content (verified), so no active bug — but it's a duplicated/driftable data source (P3 hygiene, added below).

### Feature selection (before publishing FS results)

- [x] **P1-18 — EW discretization matches Hall & Holmes (k=5)**  
  **Verify:** `READ` `datasets/feature_selection/metadata.json` + build scripts.  
  **RESULT: CONFIRMED BY METADATA.** `datasets/feature_selection/metadata.json` → `ew_benchmarks.reference` explicitly cites `"Hall & Holmes (2003)"` and each dataset entry records `"discretization": "equal_width_5_bins"` (`SpectEW` is the one exception, correctly noted as `"none (already binary)"` since it's native UCI binary data, not discretized). Added the full citation to `literature/references.bib` (`hall2003benchmarking`) since it wasn't previously in the bib file despite being referenced in metadata.  
  **Related new finding (this session):** 4 of these 8 datasets had a **loader-crashing bug** — see "New findings" item 6 above and P0/hygiene note; unrelated to the discretization method itself, which was correct.

- [x] **P1-19 — WineEW uses macro-F1; others accuracy**  
  Cross-dataset comparison of objective values is not directly comparable — report per-dataset metrics.  
  **Verify:** `READ` evaluator `_default_metric`.  
  **RESULT: CONFIRMED BY CODE.** `FeatureSubsetEvaluator._default_metric`: returns `"macro_f1"` if `dataset.name == "WineEW"` or `num_classes > 2`, else `"accuracy"`. Report per-dataset, never pool raw objective values across datasets with different metrics.

- [x] **P1-20 — Same split_seed across 30 runs vs per-run variation**  
  `split_seed` from `base_seed` — all runs same train/test split (good for optimizer comparison). Confirm intentional.  
  **Verify:** `READ` `runner._build_domain_config`.  
  **RESULT: CONFIRMED INTENTIONAL.** `runner._build_domain_config` sets `domain_config.setdefault("split_seed", config.seed_policy.base_seed)` — same split for all 30 runs of a batch (isolates optimizer variance from data-split variance). Correct design for this comparison; would be wrong only if the paper claims per-run split variation was tested (it isn't).

- [ ] **P1-21 — k-NN ties in CV folds**  
  sklearn tie-breaking + small datasets → high variance. Mention limitation.  
  **Verify:** `ASK` methodology note.  
  Not verified this session — qualitative limitation, not a code check.

- [x] **P0-12 — Test set never enters optimizer objective** *(promoted from P0 list above — verified here)*  
  **RESULT: PASS.** Traced `FeatureSelectionProblem.evaluate()` → `_objective_value()` → `evaluator.cross_validation_loss()`, which only ever touches `self.X_train`/`self.y_train` (verified in `evaluator.py` lines 89–104). `X_test`/`y_test` are referenced only inside `test_performance()`, called only from `serialize_solution()` and `domain_metrics()` — both post-hoc reporting, never from `evaluate()`. No test leakage into the optimization loop.

- [x] **P0-13 — FS objective weights explicit in every config** *(promoted from P0 list above — verified here)*  
  **RESULT: PASS.** `FeatureSelectionProblem.from_config` raises `ValueError` if `performance_weight` or `reduction_weight` is missing from `domain_config` — no silent default possible. Verified in code (`problem.py` lines 44–49).

---

## P2 — Important (credibility & reproducibility)

### Documentation & config drift

- [ ] **P2-01 — D12 `initial_solution: random` vs final NN init**  
  decisions.yaml describes v2 protocol, not final comparison domain config. Update note to avoid self-contradiction.  
  **Verify:** `READ` D12 vs selected_parameters.

- [ ] **P2-02 — Literature / old doc links**  
  All paths point to `old documentation/` and `documentation v1.md`.  
  **Verify:** `RUN` grep for broken `.md` references.

- [ ] **P2-03 — Paper folder list in docs matches disk**  
  **Verify:** `READ` documentation v1.md § TSP result folders.

### Reproducibility

- [ ] **P2-04 — `environment.json` captured per experiment**  
  Python version, OS, key package versions for paper machine disclosure.  
  **Verify:** `READ` environment.json in canonical folders.

- [ ] **P2-05 — sklearn / numpy versions pinned or recorded**  
  FS results can shift across sklearn versions.  
  **Verify:** `READ` environment.json; consider requirements lockfile.

- [ ] **P2-06 — Seeds reproducible from config**  
  `SeedManager`: seeds = base_seed + i for i in 0..runs-1.  
  **Verify:** `RUN` `tests/test_seed_manager.py`.

- [ ] **P2-07 — Resume script doesn't duplicate or skip runs**  
  **Verify:** `READ` `scripts/resume_experiment.py`; test on copy of ch130 folder.

### Algorithms & domains

- [ ] **P2-08 — SA stops on final_temperature before budget exhausted**  
  Some SA runs may stop for temperature, not budget — breaks "equal budget" narrative if common.  
  **Verify:** `READ` stop_reason distribution in all TSP runs.

- [ ] **P2-09 — Tabu search candidate list size vs instance size**  
  List 100 on eil51 (51 cities) vs rat195 — same param may behave differently.  
  **Verify:** sensitivity note in paper.

- [ ] **P2-10 — TSP distance rounding**  
  TSPLIB EUC_2D rounding matches TSPLIB convention in `distance.py`.  
  **Verify:** `RUN` `tests/test_tsp.py` + compare one known edge to TSPLIB.

- [ ] **P2-11 — Removed instances inaccessible from UI/catalog**  
  kroB100, tsp225 in `datasets/tsp/removed/` only.  
  **Verify:** `READ` tsp metadata active list + UI instance picker.

### Web platform

- [ ] **P2-12 — API port / proxy alignment**  
  Vite proxy → 8002; `dev_api.py` uses DEV_API_PORT.  
  **Verify:** `RUN` `npm run dev`; hit `/api/domains/tsp`.

- [ ] **P2-13 — Rerun deletes prior batch for same pair**  
  `prepare_tsp_launch` clears old folders — user may accidentally delete good results.  
  **Verify:** `READ` catalog; add UI warning if canonical complete batch exists.

- [ ] **P2-14 — Live viz matches final stored solution**  
  Route map / Gantt / feature grid reflect post-run JSON, not stale live file.  
  **Verify:** manual UI test per domain.

- [ ] **P2-15 — Results dashboard points at canonical batches**  
  `_pick_canonical_batch` uses latest complete experiment_id — string sort may not equal timestamp order.  
  **Verify:** `READ` `tsp_catalog._pick_canonical_batch`.

---

## P3 — Hygiene & future work

- [ ] **P3-01 — Implement automated audit script**  
  Generalize `validate_tsp_output.py` → `scripts/audit_experiment.py --dir ... --domain tsp`.

- [ ] **P3-02 — Pytest invariants for frozen params**  
  Test: examples ↔ selected_parameters.json ↔ catalog output.

- [x] **P3-03 — JSP tuning protocol JSON**  
  Mirror TSP equal-effort structure before JSP benchmark.  
  **RESULT: DONE.** `config/tuning/jsp_tuning_protocol.json` — 4 configs × 3 algorithms, literature-grounded (van Laarhoven et al. 1992; Nowicki & Smutnicki 1996).

- [x] **P3-04 — FS tuning protocol JSON**  
  Tune/compare dataset split locked in decisions.  
  **RESULT: DONE.** `config/tuning/fs_tuning_protocol.json` — 4 configs × 3 algorithms, literature-grounded (Kohavi & John 1997; Xue et al. 2013; Ma et al. 2023); split locked in `config/decisions.yaml` D14.

- [ ] **P3-05 — Friedman + Wilcoxon in codebase**  
  Close D11; cite Demšar (2006) from literature folder.

- [ ] **P3-06 — Feature frequency heatmap (FS)**  
  Post-run visualization across 30 masks.

- [ ] **P3-07 — Hold-out TSP instances (kroB100, tsp225)**  
  Optional stress test; not for main paper table.

- [ ] **P3-08 — Consolidate duplicate config paths**  
  Windows path duplicates in git status (`config\examples\` vs `config/examples/`).

- [ ] **P3-09 — Archive smoke / tuning results outside results/**  
  Reduce confusion about which folders are paper artifacts.

- [ ] **P3-10 — CI runs pytest on push**  
  Prevent catalog/template regressions.

- [x] **P3-11 — Stale `.live.json` snapshot files not cleaned up** *(found during audit)*  
  Each canonical folder's `solutions/` directory has 180 files for 90 runs — 90 real solution JSONs + 90 leftover `*.live.json` progress-tracking snapshots from `write_live_route_snapshot` that were never deleted after the run completed. Harmless for correctness (the audit script filters them out explicitly) but doubles file count and could confuse a naive `glob("*.json")` in future scripts. **Recommend:** delete `*.live.json` in `finalize_experiment` (`src/optimize/storage/writer.py`) once a run's real solution file is written.

- [x] **P3-12 — Duplicate JSP metadata files can drift** *(found during audit)*  
  `datasets/scheduling/metadata.json` and `datasets/scheduling/jsp/metadata.json` contain identical instance data today, but `JSPProblem._load_known_optimum`'s fallback path reads the former while `jsp_catalog.py` reads the latter. **Recommend:** delete one and make the other the single source of truth, or have the fallback path match the catalog's path.

---

## Suggested execution order (one sitting)

### Session A — TSP paper defense (~2–3 h)

1. P0-03, P0-05, P0-06, P0-07 on all three canonical folders  
2. P0-01, P0-04, P0-09  
3. P1-05, P1-06, P1-11  
4. Fix/update P1-08 validate script  
5. Write 1-page "protocol summary" for paper methods section

### Session B — Cross-domain honesty (~1 h)

1. P0-15, P1-14 through P1-21  
2. Decide what is in scope for paper v1 (TSP only vs all domains)

### Session C — Automation (~2–4 h)

1. P3-01, P3-02  
2. P1-09 convergence checks  
3. P2-08 stop_reason audit

---

## Red-team prompts (use with fresh Opus / separate chat)

Copy repo context + ask:

1. *"You are a hostile reviewer. List fatal flaws in this TSP benchmark protocol and results. Cite exact files."*  
2. *"Assume PSO rankings are an artifact of unfair budget accounting. Prove or disprove with code paths."*  
3. *"Find every place test data could leak into FS optimization."*  
4. *"Which claims in documentation v1.md overstate what was actually done?"*  
5. *"If I rerun everything on another machine, what will fail to reproduce?"*

---

## Sign-off (fill when done)

| Domain | Auditor | Date | P0 clear? | Notes |
|--------|---------|------|-----------|-------|
| TSP results | | | ☐ | |
| TSP protocol | | | ☐ | |
| JSP | | | ☐ | Not tuned — exploratory only |
| FS | | | ☐ | Not tuned — exploratory only |
| UI/API | | | ☐ | |
| Paper stats | | | ☐ | |

---

*Generated for MSALGCM benchmark QA — update as checks pass or new risks are found.*
