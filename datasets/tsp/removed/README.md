# Removed TSP instances (not in paper benchmark)

These TSPLIB instances were dropped from the **active six-instance** TSP benchmark to limit compute while keeping good coverage.

## Active benchmark (6 instances)

| Role | Instances |
|------|-----------|
| Tuning | eil51, berlin52, st70 |
| Final comparison | kroA100, ch130, rat195 |

See `old documentation/standard.md` and `../metadata.json`.

## Archived here

| Instance | Cities | Former role | Why removed |
|----------|--------|-------------|-------------|
| **kroB100** | 100 | Optional hold-out | Redundant with kroA100 (same size, similar clustered geometry) |
| **tsp225** | 225 | Optional hold-out | Incremental vs rat195 for size; not needed for minimum defensible coverage |

Files live under `removed/instances/`. Metadata: `removed/metadata.json`.

To restore an instance for a follow-up study, move its `.tsp` back to `../instances/` and add it to `../metadata.json`.
