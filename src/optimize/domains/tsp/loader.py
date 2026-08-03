"""TSPLIB instance loader."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TSPInstance:
    name: str
    dimension: int
    coordinates: list[tuple[float, float]]

    @property
    def num_cities(self) -> int:
        return self.dimension


def load_tsplib(path: str | Path) -> TSPInstance:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"TSP instance not found: {file_path}")

    name = file_path.stem
    dimension = 0
    edge_weight_type: str | None = None
    coordinates: list[tuple[float, float]] = []
    in_coord_section = False

    with file_path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            upper = line.upper()
            if upper.startswith("NAME"):
                name = line.split(":", 1)[1].strip()
            elif upper.startswith("DIMENSION"):
                dimension = int(line.split(":", 1)[1].strip())
            elif upper.startswith("EDGE_WEIGHT_TYPE"):
                edge_weight_type = line.split(":", 1)[1].strip().upper()
            elif upper.startswith("NODE_COORD_SECTION"):
                in_coord_section = True
                continue
            elif upper.startswith("EOF"):
                break
            elif in_coord_section:
                parts = line.split()
                if len(parts) >= 3:
                    coordinates.append((float(parts[1]), float(parts[2])))

    if dimension <= 0:
        raise ValueError(f"invalid or missing DIMENSION in {file_path}")
    if edge_weight_type not in {None, "EUC_2D"}:
        raise ValueError(f"unsupported EDGE_WEIGHT_TYPE: {edge_weight_type}")
    if len(coordinates) != dimension:
        raise ValueError(
            f"expected {dimension} coordinates, found {len(coordinates)} in {file_path}"
        )

    return TSPInstance(name=name, dimension=dimension, coordinates=coordinates)
