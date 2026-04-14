"""Rolling grid geometry used by the ProMis map node."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Tuple


Coordinate = Tuple[float, float]


@dataclass(frozen=True)
class RollingWindowConfig:
    """Configuration for a rolling rectangular grid."""

    width_m: float = 20.0
    height_m: float = 20.0
    resolution_m: float = 0.2
    snap_to_grid: bool = True

    def __post_init__(self) -> None:
        if self.width_m <= 0.0:
            raise ValueError("width_m must be positive")
        if self.height_m <= 0.0:
            raise ValueError("height_m must be positive")
        if self.resolution_m <= 0.0:
            raise ValueError("resolution_m must be positive")


@dataclass(frozen=True)
class GridSpec:
    """Concrete grid metadata for a single rolling-window update."""

    origin_x: float
    origin_y: float
    width_cells: int
    height_cells: int
    resolution_m: float

    @property
    def width_m(self) -> float:
        return self.width_cells * self.resolution_m

    @property
    def height_m(self) -> float:
        return self.height_cells * self.resolution_m

    @property
    def cell_count(self) -> int:
        return self.width_cells * self.height_cells


def _cell_count(length_m: float, resolution_m: float) -> int:
    return max(1, int(math.ceil(length_m / resolution_m)))


def make_grid_spec(
    center_x: float,
    center_y: float,
    config: RollingWindowConfig,
) -> GridSpec:
    """Create a grid spec centered around a robot pose."""

    width_cells = _cell_count(config.width_m, config.resolution_m)
    height_cells = _cell_count(config.height_m, config.resolution_m)
    width_m = width_cells * config.resolution_m
    height_m = height_cells * config.resolution_m

    origin_x = float(center_x) - width_m / 2.0
    origin_y = float(center_y) - height_m / 2.0

    if config.snap_to_grid:
        origin_x = math.floor(origin_x / config.resolution_m) * config.resolution_m
        origin_y = math.floor(origin_y / config.resolution_m) * config.resolution_m

    return GridSpec(
        origin_x=origin_x,
        origin_y=origin_y,
        width_cells=width_cells,
        height_cells=height_cells,
        resolution_m=config.resolution_m,
    )


def iter_cell_centers(spec: GridSpec) -> Iterable[Coordinate]:
    """Yield cell centers in ROS OccupancyGrid row-major order."""

    resolution = spec.resolution_m
    for row in range(spec.height_cells):
        y = spec.origin_y + (row + 0.5) * resolution
        for col in range(spec.width_cells):
            x = spec.origin_x + (col + 0.5) * resolution
            yield (x, y)


def cell_centers(spec: GridSpec) -> List[Coordinate]:
    """Return all cell centers as a list."""

    return list(iter_cell_centers(spec))

