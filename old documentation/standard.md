# TSP Benchmark Standard (Plain Language)

This document explains **how we compare Simulated Annealing, Tabu Search, and Particle Swarm on TSP** in a way that is fair, honest, and good enough for a research paper.

It does **not** claim any algorithm is “the best in the world.” It defines **how we measure them** so others can trust the results.

---

## The main idea

We want to answer:

> On our chosen TSP instances, with the same rules for everyone, how do SA, TS, and PSO compare?

That is different from:

> Which algorithm is universally best?

The second question has no honest answer. Different problems favor different methods. That idea is often called **“no free lunch”**: you cannot win everywhere with one fixed approach.

So our goal is **not** to crown a permanent winner. Our goal is to run a **clear, repeatable test** and report what happened **on our benchmark**.

---

## Why calibration matters

Algorithms like simulated annealing have settings that strongly affect results (temperature, cooling rate, etc.). In many papers, an algorithm looks bad with default settings and much better after careful tuning.

That is normal. It is **not cheating** to tune parameters — as long as:

1. We **write down the tuning rules before** the final comparison.
2. **Every algorithm gets the same chance** to tune (same effort, not same numbers).
3. We **do not tune on the same instances we use for the final score**.

If we only tune SA and leave TS/PSO at defaults, the comparison is unfair.  
If we tune on eil51 and then only report eil51, the comparison is misleading.

---

## Three sets of instances (do not mix them)

Split instances into roles:

| Role | What it is for | Counts in final paper tables? |
|------|----------------|-------------------------------|
| **Tuning set** | Try parameter settings and pick the best | No |
| **Comparison set** | Run the real head-to-head experiment | Yes — main results |
| **Removed / archived** | Former hold-out instances kept on disk but not scored | No |

**Active split (6 TSPLIB instances):**

- **Tuning:** eil51, berlin52, st70 (smaller, faster)
- **Comparison:** kroA100, ch130, rat195

**Archived** (not in the benchmark): kroB100, tsp225 — see `datasets/tsp/removed/`.

Once parameters are chosen on the tuning set, **freeze them**. Do not change them because comparison results look bad.

---

## What “objective measurement” means here

“Objective” does **not** mean “each algorithm at its absolute peak performance.”

It means:

- Same **evaluation budget** for every run (100,000 objective evaluations).
- Same **number of independent runs** (30 per algorithm per instance).
- Same **seeds policy** so comparisons are paired fairly.
- Same **rules for stopping** (budget exhausted).
- Same **reported metrics** for everyone.
- Parameters chosen by a **fixed tuning rule** that was decided in advance.

Then we report:

> Under protocol P, on benchmark B, with frozen parameters from tuning rule R, here is how SA, TS, and PSO compare.

That is a defensible, objective statement.

---

## Fair tuning: same opportunity, not same settings

SA, TS, and PSO need **different** parameter names and ranges. That is expected.

Fairness means **equal tuning effort**, for example:

- Same number of parameter combinations tried per algorithm.
- Same tuning instances.
- Same number of runs per combination during tuning.
- Same rule for picking the winner (e.g. lowest **mean gap %** on tuning instances).

After tuning, **write down the final parameters** for each algorithm and use only those in the comparison runs.

Optionally, also report a **default-settings baseline** so readers can see how much tuning helped.

---

## What we measure

### Primary (solution quality)

- **Best tour cost** (distance)
- **Gap %** vs known optimum: `(found − optimum) / optimum × 100`
- Distribution over 30 runs (mean, median, best, spread)

### Secondary (effort and speed)

- **Runtime** (seconds)
- **Evaluations used**
- **Convergence** (best-so-far vs evaluation count)
- **Tuning cost** (how many configs and runs it took to pick parameters)

Reporting both quality and cost avoids pretending the fastest or easiest algorithm “won” without context.

---

## Domain settings are part of the benchmark too

These apply to **all** algorithms on a given experiment:

- **Initial tour:** nearest neighbor (or random — pick one and stick to it)
- **Neighborhood operators:** swap, insertion, inversion, two-opt, etc.
- **Instance files:** TSPLIB EUC_2D

Do not give one algorithm a better initialization or operator mix unless that difference is **part of the study design** and clearly stated.

Algorithm-specific settings (temperature, tabu tenure, swarm size) belong in **algorithm configs** and may be tuned under the equal-effort rule above.

---

## How to talk about results (no overclaiming)

### OK to say

- “On instances X, Y, Z, under our protocol, algorithm A had significantly lower gap than B.”
- “Results vary by instance; no algorithm wins on every case.”
- “SA improved a lot after equal tuning effort; defaults were weak.”

### Avoid saying

- “SA is the best algorithm for TSP.”
- “After we tuned it, SA wins” (without equal tuning for TS/PSO and without a separate comparison set)
- Reporting only the instance where your favorite algorithm looked best

---

## Minimal workflow for this project

1. **Write tuning ranges** for SA, TS, and PSO (document in config or decisions file).
2. **Tune on the tuning set** only; pick best config per algorithm by a fixed rule.
3. **Freeze parameters.**
4. **Run final comparison** on the comparison set: 3 algorithms × 30 runs × shared seeds × 100k evaluations.
5. **Aggregate:** gap, runtime, convergence, success rate.
6. **Statistics:** compare algorithms per instance; use proper tests (e.g. Friedman + pairwise tests) and report effect sizes, not only p-values.
7. **Discuss no free lunch:** conclusions apply to **this benchmark and protocol**, not all optimization problems.

---

## What we benchmark (reference)

**Algorithms:** Simulated Annealing, Tabu Search, Particle Swarm  

**Instances (TSPLIB, active):** eil51, berlin52, st70, kroA100, ch130, rat195  
**Archived:** kroB100, tsp225 (`datasets/tsp/removed/`)

**Protocol defaults in code today:**

- 100,000 evaluations per run  
- 30 runs (TSP dashboard) or 10 runs (comparison JSON configs — align these for the paper)  
- Base seed 1000  
- Nearest-neighbor initial tour  
- Gap vs known optima from `datasets/tsp/metadata.json`

---

## One-sentence summary

**Tune fairly on small instances, freeze settings, score on separate instances with identical budgets and runs, report gaps and runtimes honestly, and do not claim any algorithm is universally best.**
