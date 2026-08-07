"""Update FS experiment configs to protocol v2 (standardized features, 0.99/0.01 weights)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = ROOT / "config"


def update_domain_config(payload: dict) -> bool:
    config = payload.get("domain_config")
    if not isinstance(config, dict):
        return False
    if config.get("performance_weight") is None and config.get("reduction_weight") is None:
        return False

    changed = False
    if config.get("performance_weight") != 0.99:
        config["performance_weight"] = 0.99
        changed = True
    if config.get("reduction_weight") != 0.01:
        config["reduction_weight"] = 0.01
        changed = True
    if config.get("standardize_features") is not True:
        config["standardize_features"] = True
        changed = True
    return changed


def main() -> None:
    updated = 0
    for path in CONFIG_ROOT.rglob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if payload.get("domain") != "feature_selection":
            continue
        if update_domain_config(payload):
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            updated += 1
            print(f"updated {path.relative_to(ROOT)}")
    print(f"Done: {updated} FS config files updated")


if __name__ == "__main__":
    main()
