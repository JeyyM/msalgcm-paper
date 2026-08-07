"""Launch a single JSP comparison run exactly as the web UI would.

Usage:
    python scripts/launch_jsp_run.py <instance> <algorithm>
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from optimize.api.services.jsp_catalog import prepare_jsp_launch, write_jsp_config_file
from optimize.experiments.runner import ExperimentRunner


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: launch_jsp_run.py <instance> <algorithm>", file=sys.stderr)
        raise SystemExit(2)

    instance, algorithm = sys.argv[1], sys.argv[2]
    prepare_jsp_launch(instance, algorithm)
    config_path = write_jsp_config_file(instance, algorithm)

    print(f"Launching {algorithm} on {instance} (config: {config_path})")
    runner = ExperimentRunner()
    result_dir = runner.run(config_path)
    print(f"DONE {instance} {algorithm} -> {result_dir}")


if __name__ == "__main__":
    main()
