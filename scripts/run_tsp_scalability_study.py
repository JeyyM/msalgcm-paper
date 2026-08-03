"""Run the full TSP scalability study."""

from __future__ import annotations

from optimize.experiments.study import StudyRunner


def main() -> None:
    study_dir = StudyRunner().run("config/examples/tsp_scalability_study.json")
    print(f"Study complete: {study_dir}")


if __name__ == "__main__":
    main()
