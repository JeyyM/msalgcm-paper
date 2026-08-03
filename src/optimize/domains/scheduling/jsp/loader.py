"""Classic job-shop instance loader (Taillard / OR-Library format)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class JSPInstance:
    name: str
    num_jobs: int
    num_machines: int
    machines: tuple[tuple[int, ...], ...]
    processing_times: tuple[tuple[int, ...], ...]

    @property
    def num_operations(self) -> int:
        return self.num_jobs * self.num_machines


def load_jsp(path: str | Path) -> JSPInstance:
    """Load a standard JSP text file (machine, time pairs per job)."""
    file_path = Path(path)
    lines = [line.strip() for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"empty JSP instance file: {file_path}")

    header = lines[0].split()
    if len(header) < 2:
        raise ValueError(f"invalid JSP header in {file_path}: {lines[0]!r}")

    num_jobs = int(header[0])
    num_machines = int(header[1])
    if len(lines) - 1 != num_jobs:
        raise ValueError(
            f"expected {num_jobs} job rows in {file_path}, found {len(lines) - 1}",
        )

    machine_rows: list[tuple[int, ...]] = []
    time_rows: list[tuple[int, ...]] = []
    for job_index, line in enumerate(lines[1:], start=1):
        tokens = line.split()
        expected = num_machines * 2
        if len(tokens) != expected:
            raise ValueError(
                f"job {job_index} in {file_path} expected {expected} tokens, found {len(tokens)}",
            )
        machines = tuple(int(tokens[i]) for i in range(0, len(tokens), 2))
        times = tuple(int(tokens[i]) for i in range(1, len(tokens), 2))
        machine_rows.append(machines)
        time_rows.append(times)

    return JSPInstance(
        name=file_path.stem,
        num_jobs=num_jobs,
        num_machines=num_machines,
        machines=tuple(machine_rows),
        processing_times=tuple(time_rows),
    )
