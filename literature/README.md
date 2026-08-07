# Literature folder

This folder documents the **academic and methodological references** that support how this project defines:

- **Equal opportunity** in metaheuristic comparison  
- **Parameter calibration / tuning** for Simulated Annealing, Tabu Search, and Particle Swarm  
- **Experimental design choices** used in `old documentation/standard.md`, `old documentation/tuning_documentation.md`, and `config/tuning/`

## Important note on provenance

The TSP tuning protocol was **implemented as a structured grid search** (`scripts/run_tsp_tuning.py`), not by running automated configurators such as **irace** or **SMAC**. The references here explain **why** the protocol is shaped the way it is and what the field considers good practice.

The project’s internal specs (`old documentation/metaheuristic_optimization_project_overview.md`, `old documentation/pipeline_definition.md`, `old documentation/standard.md`) describe the intended methodology. **Current guide:** [`documentation v1.md`](../documentation%20v1.md).

## Files

| File | Purpose |
|------|---------|
| [`methodology_references.md`](methodology_references.md) | Narrative map: each protocol choice → supporting literature |
| [`references.bib`](references.bib) | BibTeX entries for LaTeX / paper bibliography |
| [`algorithm_parameter_literature.md`](algorithm_parameter_literature.md) | SA / TS / PSO parameter ranges and calibration notes |

## Quick reading order

1. **Fair comparison & equal effort** → García et al. (2021); Cohen (2013); Molina et al. (2020)  
2. **Tuning vs testing split** → Birattari (2009); López-Ibáñez et al. (2016)  
3. **No overclaiming** → Wolpert & Macready (1997)  
4. **Statistics** → García et al. (2010); Demšar (2006)  
5. **Algorithm-specific knobs** → Kirkpatrick et al. (1983); Glover (1989); Kennedy & Eberhart (1995)
