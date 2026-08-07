# Benchmark Datasets

Established benchmark instances for the metaheuristic optimization platform.

## Layout

```text
datasets/
├── tsp/
│   ├── instances/          # Active TSPLIB .tsp files (6 benchmark instances)
│   ├── removed/            # Archived instances not in the paper benchmark
│   │   ├── instances/
│   │   ├── metadata.json
│   │   └── README.md
│   └── metadata.json       # Known optima + roles (tuning vs comparison)
├── scheduling/
│   └── jsp/
│       ├── instances/      # Taillard / OR-Library JSP files
│       └── metadata.json   # Best-known makespans
├── feature_selection/
│   ├── raw/                # Original UCI downloads
│   ├── ew/                 # Literature-aligned EW benchmark CSVs
│   └── metadata.json
├── download_report.json    # Last download run summary
└── README.md
```

## Sources

| Domain | Source | Instances |
|--------|--------|-----------|
| TSP | [TSPLIB95](https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/) via [mastqe/tsplib](https://github.com/mastqe/tsplib) | **Active:** eil51, berlin52, st70, kroA100, ch130, rat195. **Archived:** kroB100, tsp225 (`tsp/removed/`) |
| JSP | [SchedulingLab/jsp-instances](https://github.com/SchedulingLab/jsp-instances) | ft10, ta01, ta21, ta31, ta41, ta51, ta71 |
| Feature selection (raw) | [UCI ML Repository](https://archive.ics.uci.edu/) | zoo, wine, wdbc, ionosphere, sonar, spect, spectf, lymphography, madelon |
| Feature selection (EW) | OpenML + equal-width discretization (k=5); SPECT native binary | BreastEW, WineEW, SonarEW, IonosphereEW, ZooEW, LymphographyEW, SpectEW, MadelonEW |

## Re-download

```bash
python scripts/download_datasets.py
```

## Notes

- The official TSPLIB Heidelberg server was unreachable during setup; GitHub mirrors were used instead.
- EW CSV files match the **instance and feature counts** used in metaheuristic feature-selection papers. Continuous datasets were discretized with equal-width binning (k=5), following the common Hall & Holmes (2003) methodology.
- `SpectEW` uses the native 22-binary-feature UCI SPECT train+test merge (no discretization needed).
