"""Analyze NN TS/PSO confirmation runs and merge winners into selected_parameters.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from analyze_tsp_tuning import (  # noqa: E402
    aggregate_by_config,
    collect_tuning_rows,
    select_winners,
    write_aggregate_csv,
    write_detail_csv,
)

DEFAULT_PROTOCOL = ROOT / "config" / "tuning" / "tsp_tuning_confirm_nn.json"
DEFAULT_INPUT = ROOT / "results" / "tuning" / "nn_confirm"
SELECTED_PATH = ROOT / "results" / "tuning" / "selected_parameters.json"


def merge_winners(
    confirm_winners: dict[str, dict],
    protocol_name: str,
) -> dict:
    if not SELECTED_PATH.exists():
        raise SystemExit(f"Missing base parameters: {SELECTED_PATH}")

    selected = json.loads(SELECTED_PATH.read_text(encoding="utf-8"))
    sources = dict(selected.get("sources", {}))
    winners = dict(selected.get("winners", {}))

    for algorithm in ("tabu_search", "particle_swarm"):
        if algorithm not in confirm_winners:
            raise SystemExit(f"No confirmation winner for {algorithm}")
        winner = confirm_winners[algorithm]
        winners[algorithm] = {
            "config_id": winner["config_id"],
            "config_label": winner["config_label"],
            "parameters": json.loads(winner["parameters"]),
        }
        sources[algorithm] = f"{protocol_name} / {winner['config_id']}"

    rationale = (
        "SA from v1 nearest-neighbor tuning (sa_slow_cool). "
        "TS and PSO selected by NN confirmation on tuning instances "
        "(v1 vs v2 finalists under nearest-neighbor init). "
        "See results/tuning/nn_confirm/."
    )
    selected["sources"] = sources
    selected["winners"] = winners
    selected["rationale"] = rationale
    selected["nn_confirm"] = {
        "protocol": protocol_name,
        "results_dir": "results/tuning/nn_confirm",
        "tabu_search": {
            "config_id": confirm_winners["tabu_search"]["config_id"],
            "aggregate_mean_gap_percentage": confirm_winners["tabu_search"]["aggregate_mean_gap_percentage"],
            "per_instance_mean_gap": confirm_winners["tabu_search"]["per_instance_mean_gap"],
        },
        "particle_swarm": {
            "config_id": confirm_winners["particle_swarm"]["config_id"],
            "aggregate_mean_gap_percentage": confirm_winners["particle_swarm"]["aggregate_mean_gap_percentage"],
            "per_instance_mean_gap": confirm_winners["particle_swarm"]["per_instance_mean_gap"],
        },
    }
    SELECTED_PATH.write_text(json.dumps(selected, indent=2) + "\n", encoding="utf-8")
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge NN TS/PSO confirmation into frozen parameters")
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    rows = collect_tuning_rows(protocol, args.input)
    aggregates = aggregate_by_config(rows)
    confirm_winners = select_winners(aggregates)

    missing = {"tabu_search", "particle_swarm"} - set(confirm_winners)
    if missing:
        raise SystemExit(f"Incomplete confirmation results; missing winners for: {sorted(missing)}")

    args.input.mkdir(parents=True, exist_ok=True)
    write_detail_csv(rows, args.input / "nn_confirm_results_detail.csv")
    write_aggregate_csv(aggregates, args.input / "nn_confirm_results_aggregate.csv")

    merged = merge_winners(confirm_winners, protocol.get("protocol_name", args.protocol.stem))
    print(json.dumps(merged["nn_confirm"], indent=2))
    print(f"Updated {SELECTED_PATH}")


if __name__ == "__main__":
    main()
