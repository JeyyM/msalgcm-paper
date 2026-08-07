"""Download benchmark datasets for the metaheuristic optimization platform."""

from __future__ import annotations

import json
import shutil
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ROOT / "datasets"

TSP_ACTIVE_INSTANCES = [
    "eil51",
    "berlin52",
    "st70",
    "kroA100",
    "ch130",
    "rat195",
]

TSP_REMOVED_INSTANCES = [
    "kroB100",
    "tsp225",
]

TSP_KNOWN_OPTIMA = {
    "eil51": 426,
    "berlin52": 7542,
    "st70": 675,
    "kroA100": 21282,
    "kroB100": 22141,
    "ch130": 6110,
    "rat195": 2323,
    "tsp225": 3919,
}

TSP_INSTANCE_ROLES = {
    "eil51": "tuning",
    "berlin52": "tuning",
    "st70": "tuning",
    "kroA100": "comparison",
    "ch130": "comparison",
    "rat195": "comparison",
}

JSP_INSTANCES = ["ft10", "ta01", "ta21", "ta31", "ta41", "ta51", "ta71"]

JSP_BASE = "https://raw.githubusercontent.com/SchedulingLab/jsp-instances/main"
JSP_CLASSICAL_URL = f"{JSP_BASE}/classical.json"

TSP_MIRRORS = [
    "https://raw.githubusercontent.com/mastqe/tsplib/master/{name}.tsp",
    "https://raw.githubusercontent.com/pdrozdowski/TSPLib.Net/master/TSPLIB95/tsp/{name}.tsp",
    "https://raw.githubusercontent.com/coin-or/jorlib/master/jorlib-core/src/test/resources/tspLib/tsp/{name}.tsp",
]

UCI_DATASETS = {
    "zoo": {
        "id": 111,
        "slug": "zoo",
        "filename": "zoo.data",
    },
    "wine": {
        "id": 109,
        "slug": "wine",
        "filename": "wine.data",
    },
    "breast_cancer_diagnostic": {
        "id": 17,
        "slug": "breast+cancer+wisconsin+diagnostic",
        "filename": "wdbc.data",
    },
    "ionosphere": {
        "id": 52,
        "slug": "ionosphere",
        "filename": "ionosphere.data",
    },
    "sonar": {
        "id": 151,
        "slug": "connectionist+bench+sonar+mines+vs+rocks",
        "filename": "sonar.all-data",
    },
    "spect": {
        "id": 95,
        "slug": "spect+heart",
        "filename": "SPECT.train",
        "extra_members": ["SPECT.test"],
    },
    "spectf": {
        "id": 96,
        "slug": "spectf+heart",
        "filename": "SPECTF.train",
        "extra_members": ["SPECTF.test"],
    },
    "lymphography": {
        "id": 63,
        "slug": "lymphography",
        "filename": "lymphography.data",
    },
    "madelon": {
        "id": 171,
        "slug": "madelon",
        "is_zip_nested": True,
    },
}

OPENML_DATASETS = {
    "BreastEW": 1510,   # wdbc: 569 x 30 (+ class)
    "WineEW": 187,      # wine: 178 x 13 (+ class)
    "SonarEW": 40,      # sonar: 208 x 60 (+ class)
    "IonosphereEW": 59, # ionosphere: 351 x 34 (+ class)
    "ZooEW": 62,        # zoo: 101 x 16 (+ class)
    "LymphographyEW": 10,
    "SpectEW": 336,     # SPECT: 267 x 22 (+ class)
    "MadelonEW": 1485,
}

JBROWNLEE_FALLBACKS = {
    "sonar": "https://raw.githubusercontent.com/jbrownlee/Datasets/master/sonar.csv",
    "ionosphere": "https://raw.githubusercontent.com/jbrownlee/Datasets/master/ionosphere.csv",
    "wine": "https://raw.githubusercontent.com/jbrownlee/Datasets/master/wine.csv",
}


def download_url(url: str, dest: Path, timeout: int = 120) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "MSALGCM-dataset-downloader/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read()
    dest.write_bytes(data)


def fetch_json(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "MSALGCM-dataset-downloader/1.0"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def download_with_fallback(urls: list[str], dest: Path) -> str:
    last_error: Exception | None = None
    for url in urls:
        try:
            download_url(url, dest)
            return url
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise RuntimeError(f"All download attempts failed for {dest.name}: {last_error}")


def _download_tsp_subset(names: list[str], out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {"downloaded": [], "failed": []}
    for name in names:
        dest = out_dir / f"{name}.tsp"
        urls = [template.format(name=name) for template in TSP_MIRRORS]
        try:
            source = download_with_fallback(urls, dest)
            results["downloaded"].append({"instance": name, "source": source})
        except RuntimeError as exc:
            results["failed"].append({"instance": name, "error": str(exc)})
    return results


def download_tsp() -> dict:
    active_dir = DATASETS / "tsp" / "instances"
    removed_dir = DATASETS / "tsp" / "removed" / "instances"
    active_results = _download_tsp_subset(TSP_ACTIVE_INSTANCES, active_dir)
    removed_results = _download_tsp_subset(TSP_REMOVED_INSTANCES, removed_dir)

    active_metadata = {
        "source": "TSPLIB95 (via GitHub mirrors)",
        "format": "TSPLIB .tsp (EUC_2D)",
        "active_benchmark": {
            "tuning": [name for name in TSP_ACTIVE_INSTANCES if TSP_INSTANCE_ROLES[name] == "tuning"],
            "comparison": [
                name for name in TSP_ACTIVE_INSTANCES if TSP_INSTANCE_ROLES[name] == "comparison"
            ],
        },
        "removed_instances": "removed/",
        "known_optima": {name: TSP_KNOWN_OPTIMA[name] for name in TSP_ACTIVE_INSTANCES},
        "instances": [
            {
                "name": name,
                "file": f"instances/{name}.tsp",
                "known_optimum": TSP_KNOWN_OPTIMA.get(name),
                "role": TSP_INSTANCE_ROLES[name],
            }
            for name in TSP_ACTIVE_INSTANCES
        ],
    }
    removed_metadata = {
        "status": "removed_from_benchmark",
        "reason": "Hold-out instances excluded to keep the active TSP suite at six.",
        "source": "TSPLIB95 (via GitHub mirrors)",
        "format": "TSPLIB .tsp (EUC_2D)",
        "known_optima": {name: TSP_KNOWN_OPTIMA[name] for name in TSP_REMOVED_INSTANCES},
        "instances": [
            {
                "name": name,
                "file": f"instances/{name}.tsp",
                "known_optimum": TSP_KNOWN_OPTIMA.get(name),
                "former_role": "hold-out",
            }
            for name in TSP_REMOVED_INSTANCES
        ],
    }
    (DATASETS / "tsp" / "metadata.json").write_text(
        json.dumps(active_metadata, indent=2),
        encoding="utf-8",
    )
    (DATASETS / "tsp" / "removed" / "metadata.json").write_text(
        json.dumps(removed_metadata, indent=2),
        encoding="utf-8",
    )
    return {
        "active": active_results,
        "removed": removed_results,
    }


def download_jsp() -> dict:
    out_dir = DATASETS / "scheduling" / "jsp" / "instances"
    out_dir.mkdir(parents=True, exist_ok=True)
    classical = fetch_json(JSP_CLASSICAL_URL)
    by_name = {entry["name"]: entry for entry in classical}

    results = {"downloaded": [], "failed": []}
    metadata_instances = []

    for name in JSP_INSTANCES:
        entry = by_name.get(name)
        if entry is None:
            results["failed"].append({"instance": name, "error": "Not found in classical.json"})
            continue

        rel_path = entry["path"].replace("\\", "/")
        url = f"{JSP_BASE}/{rel_path}"
        dest = out_dir / f"{name}.txt"
        try:
            download_url(url, dest)
            results["downloaded"].append({"instance": name, "source": url})
            metadata_instances.append(
                {
                    "name": name,
                    "file": f"instances/{name}.txt",
                    "jobs": entry["jobs"],
                    "machines": entry["machines"],
                    "best_known_makespan": entry["optimum"],
                }
            )
        except Exception as exc:  # noqa: BLE001
            results["failed"].append({"instance": name, "error": str(exc)})

    metadata = {
        "source": "SchedulingLab/jsp-instances (Taillard & OR-Library classics)",
        "format": "Standard JSP text (machine, processing_time pairs per job)",
        "reference": "Taillard (1993); JSPLib / SchedulingLab",
        "instances": metadata_instances,
    }
    jsp_meta = DATASETS / "scheduling" / "jsp" / "metadata.json"
    jsp_meta.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    shutil.copy2(jsp_meta, DATASETS / "scheduling" / "metadata.json")
    return results


def extract_zip_members(zip_bytes: bytes, members: list[str], dest_dir: Path) -> list[Path]:
    extracted: list[Path] = []
    with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        for member in members:
            suffix = member.split("/")[-1]
            matches = [name for name in names if name.endswith(suffix)]
            if not matches:
                raise FileNotFoundError(f"No file ending with {suffix} in archive")
            dest = dest_dir / suffix
            dest.write_bytes(zf.read(matches[0]))
            extracted.append(dest)
    return extracted


def download_uci_dataset(name: str, info: dict, dest_dir: Path) -> dict:
    zip_url = f"https://archive.ics.uci.edu/static/public/{info['id']}/{info['slug']}.zip"
    request = urllib.request.Request(
        zip_url,
        headers={"User-Agent": "MSALGCM-dataset-downloader/1.0"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        zip_bytes = response.read()

    dataset_dir = dest_dir / name
    dataset_dir.mkdir(parents=True, exist_ok=True)
    archive_path = dataset_dir / f"{name}.zip"
    archive_path.write_bytes(zip_bytes)

    if info.get("is_zip_nested"):
        with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
            zf.extractall(dataset_dir / "extracted")
        return {
            "dataset": name,
            "source": zip_url,
            "path": str(dataset_dir / "extracted"),
        }

    members = [info["filename"]] + info.get("extra_members", [])
    files = extract_zip_members(zip_bytes, members, dataset_dir)
    return {
        "dataset": name,
        "source": zip_url,
        "files": [str(path) for path in files],
    }


def download_uci_with_fallback(name: str, info: dict, dest_dir: Path) -> dict:
    try:
        return download_uci_dataset(name, info, dest_dir)
    except Exception as uci_error:  # noqa: BLE001
        fallback = JBROWNLEE_FALLBACKS.get(name)
        if not fallback:
            raise uci_error
        dataset_dir = dest_dir / name
        dataset_dir.mkdir(parents=True, exist_ok=True)
        dest = dataset_dir / f"{name}.csv"
        download_url(fallback, dest)
        return {
            "dataset": name,
            "source": fallback,
            "file": str(dest),
            "note": "UCI download failed; used jbrownlee/Datasets fallback",
        }


def discretize_equal_width(values: list[float], bins: int = 5) -> list[int]:
    if not values:
        return []
    vmin = min(values)
    vmax = max(values)
    if vmin == vmax:
        return [0 for _ in values]
    step = (vmax - vmin) / bins
    result = []
    for value in values:
        if value >= vmax:
            result.append(bins - 1)
        else:
            result.append(int((value - vmin) / step))
    return result


def load_openml_csv(dataset_id: int, dataset_name: str) -> tuple[list[list[float | int | str]], list[str]]:
    import openml
    import pandas as pd

    data = openml.datasets.get_dataset(dataset_id, download_data=True)
    x, y, _, _ = data.get_data(target=data.default_target_attribute, dataset_format="dataframe")
    frame = pd.concat([x, y], axis=1)
    frame = frame.dropna()
    rows = frame.values.tolist()
    columns = [str(col) for col in frame.columns]
    return rows, columns


def rows_to_csv(rows: list[list[object]], columns: list[str], dest: Path) -> None:
    import csv

    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)


def build_ew_from_openml(name: str, dataset_id: int, ew_dir: Path, bins: int = 5) -> dict:
    import pandas as pd

    rows, columns = load_openml_csv(dataset_id, name)
    frame = pd.DataFrame(rows, columns=columns)
    label_col = columns[-1]
    feature_frame = frame.drop(columns=[label_col])

    encoded = pd.DataFrame()
    for column in feature_frame.columns:
        series = feature_frame[column]
        if pd.api.types.is_numeric_dtype(series):
            encoded[column] = series.astype(float)
        else:
            encoded[column] = series.astype("category").cat.codes.astype(float)

    discretized_rows: list[list[int | str]] = []
    for idx, row in encoded.iterrows():
        numeric_features = [float(value) for value in row.tolist()]
        discretized = discretize_equal_width(numeric_features, bins=bins)
        discretized_rows.append(discretized + [frame.iloc[idx][label_col]])

    feature_count = len(columns) - 1
    feature_columns = [f"F{i + 1}" for i in range(feature_count)] + ["class"]
    dest = ew_dir / f"{name}.csv"
    rows_to_csv(discretized_rows, feature_columns, dest)
    return {
        "dataset": name,
        "source": f"OpenML dataset {dataset_id} + equal-width discretization (k={bins})",
        "file": str(dest),
        "instances": len(discretized_rows),
        "features": feature_count,
        "discretization": f"equal_width_{bins}_bins",
    }


def build_spect_ew(raw_dir: Path, ew_dir: Path) -> dict:
    spect_dir = raw_dir / "spect"
    train_path = spect_dir / "SPECT.train"
    test_path = spect_dir / "SPECT.test"
    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError("SPECT train/test files not found")

    rows: list[list[str]] = []
    for path in (train_path, test_path):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = [part.strip() for part in line.split(",")]
            label = parts[0]
            features = parts[1:]
            rows.append(features + [label])

    columns = [f"F{i + 1}" for i in range(len(rows[0]) - 1)] + ["class"]
    dest = ew_dir / "SpectEW.csv"
    rows_to_csv(rows, columns, dest)
    return {
        "dataset": "SpectEW",
        "source": "UCI SPECT train+test (native 22 binary features)",
        "file": str(dest),
        "instances": len(rows),
        "features": len(columns) - 1,
        "discretization": "none (already binary)",
    }


def download_feature_selection() -> dict:
    raw_dir = DATASETS / "feature_selection" / "raw"
    ew_dir = DATASETS / "feature_selection" / "ew"
    raw_dir.mkdir(parents=True, exist_ok=True)
    ew_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "uci_downloaded": [],
        "uci_failed": [],
        "ew_downloaded": [],
        "ew_failed": [],
    }

    for name, info in UCI_DATASETS.items():
        try:
            item = download_uci_with_fallback(name, info, raw_dir)
            results["uci_downloaded"].append(item)
        except Exception as exc:  # noqa: BLE001
            results["uci_failed"].append({"dataset": name, "error": str(exc)})

    for name, dataset_id in OPENML_DATASETS.items():
        if name == "SpectEW":
            continue
        try:
            item = build_ew_from_openml(name, dataset_id, ew_dir)
            results["ew_downloaded"].append(item)
        except Exception as exc:  # noqa: BLE001
            results["ew_failed"].append({"dataset": name, "error": str(exc)})

    try:
        results["ew_downloaded"].append(build_spect_ew(raw_dir, ew_dir))
    except Exception as exc:  # noqa: BLE001
        results["ew_failed"].append({"dataset": "SpectEW", "error": str(exc)})

    metadata = {
        "raw_uci": {
            "source": "UCI Machine Learning Repository (archive.ics.uci.edu)",
            "directory": "raw/",
            "datasets": results["uci_downloaded"],
        },
        "ew_benchmarks": {
            "source": (
                "Literature-aligned EW benchmarks: OpenML originals with equal-width "
                "discretization (k=5), plus native-binary SPECT as SpectEW"
            ),
            "directory": "ew/",
            "reference": "Hall & Holmes (2003); metaheuristic feature-selection benchmark suite",
            "datasets": results["ew_downloaded"],
            "note": (
                "EW CSV files match the instance/feature counts used in metaheuristic "
                "feature-selection papers (e.g., BreastEW 569x30, WineEW 178x13)."
            ),
        },
    }
    (DATASETS / "feature_selection" / "metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )
    return results


def main() -> None:
    summary = {
        "tsp": download_tsp(),
        "jsp": download_jsp(),
        "feature_selection": download_feature_selection(),
    }
    report_path = DATASETS / "download_report.json"
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"\nReport written to {report_path}")


if __name__ == "__main__":
    main()
