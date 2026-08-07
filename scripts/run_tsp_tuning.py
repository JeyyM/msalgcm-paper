"""Run TSP parameter tuning experiments from a protocol JSON file."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from optimize.experiments.models import ExperimentConfig  # noqa: E402
from optimize.experiments.runner import ExperimentRunner  # noqa: E402

DEFAULT_PROTOCOL = ROOT / "config" / "tuning" / "tsp_tuning_protocol.json"


def _build_config(
    protocol: dict,
    algorithm: str,
    config_entry: dict,
    instance: dict,
    output_root: Path,
) -> ExperimentConfig:
    config_id = config_entry["id"]
    instance_name = instance["name"]
    prefix = protocol.get("experiment_prefix", "tuning")
    return ExperimentConfig.model_validate(
        {
            "experiment_name": f"{prefix}_{config_id}_{instance_name}",
            "domain": "tsp",
            "instance": instance_name,
            "instance_path": instance["path"],
            "algorithms": [algorithm],
            "runs": protocol["runs_per_config"],
            "evaluation_budget": protocol["evaluation_budget"],
            "seed_policy": {"base_seed": protocol["base_seed"]},
            "domain_config": protocol["domain_config"],
            "algorithm_configs": {algorithm: config_entry["params"]},
            "output": {"directory": str(output_root / "experiments")},
        }
    )


def _write_generated_config(
    config: ExperimentConfig,
    config_id: str,
    instance_name: str,
    generated_dir: Path,
) -> Path:
    generated_dir.mkdir(parents=True, exist_ok=True)
    path = generated_dir / f"{config_id}_{instance_name}.json"
    payload = json.loads(config.model_dump_json())
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _experiment_complete(experiment_dir: Path, expected_runs: int) -> bool:
    runs_csv = experiment_dir / "runs.csv"
    if not runs_csv.exists():
        return False
    with runs_csv.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    completed = sum(1 for row in rows if row.get("status") == "completed")
    return len(rows) >= expected_runs and completed == expected_runs


def _find_experiment_dir(output_root: Path, experiment_name: str) -> Path | None:
    experiments_root = output_root / "experiments"
    if not experiments_root.exists():
        return None
    matches = sorted(experiments_root.glob(f"*_{experiment_name}"))
    return matches[-1] if matches else None


def _append_run_log(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {message}\n")


def run_tuning(
    protocol_path: Path,
    tuning_root: Path,
    generated_dir: Path,
    skip_existing: bool = True,
) -> Path:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    tuning_root.mkdir(parents=True, exist_ok=True)
    (tuning_root / "experiments").mkdir(parents=True, exist_ok=True)

    manifest = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "protocol_path": str(protocol_path.resolve().relative_to(ROOT.resolve())),
        "protocol_name": protocol.get("protocol_name"),
        "protocol": protocol,
        "jobs": [],
    }
    manifest_path = tuning_root / "tuning_run_manifest.json"
    log_path = tuning_root / "tuning_run.log"

    runner = ExperimentRunner()
    expected_runs = protocol["runs_per_config"]

    for algorithm, algo_block in protocol["algorithms"].items():
        for config_entry in algo_block["configs"]:
            for instance in protocol["tuning_instances"]:
                config = _build_config(protocol, algorithm, config_entry, instance, tuning_root)
                config_path = _write_generated_config(
                    config,
                    config_entry["id"],
                    instance["name"],
                    generated_dir,
                )
                existing = _find_experiment_dir(tuning_root, config.experiment_name)
                if skip_existing and existing and _experiment_complete(existing, expected_runs):
                    message = f"SKIP complete: {config.experiment_name} -> {existing.name}"
                    print(message)
                    _append_run_log(log_path, message)
                    manifest["jobs"].append(
                        {
                            "experiment_name": config.experiment_name,
                            "algorithm": algorithm,
                            "config_id": config_entry["id"],
                            "instance": instance["name"],
                            "status": "skipped_existing",
                            "experiment_dir": str(existing),
                        }
                    )
                    continue

                message = f"RUN {config.experiment_name} ({algorithm}, {config_entry['id']}, {instance['name']})"
                print(message, flush=True)
                _append_run_log(log_path, message)
                experiment_dir = runner.run(config_path)
                manifest["jobs"].append(
                    {
                        "experiment_name": config.experiment_name,
                        "algorithm": algorithm,
                        "config_id": config_entry["id"],
                        "instance": instance["name"],
                        "status": "completed",
                        "experiment_dir": str(experiment_dir),
                    }
                )

    manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Tuning manifest written to {manifest_path}")
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TSP parameter tuning batch")
    parser.add_argument(
        "--protocol",
        type=Path,
        default=DEFAULT_PROTOCOL,
        help="Path to tuning protocol JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "tuning",
        help="Root directory for tuning artifacts",
    )
    parser.add_argument(
        "--generated-dir",
        type=Path,
        default=ROOT / "config" / "tuning" / "generated",
        help="Where to write generated experiment configs",
    )
    parser.add_argument("--force", action="store_true", help="Re-run even if experiment folder is complete")
    args = parser.parse_args()

    run_tuning(
        protocol_path=args.protocol,
        tuning_root=args.output,
        generated_dir=args.generated_dir,
        skip_existing=not args.force,
    )


if __name__ == "__main__":
    main()
