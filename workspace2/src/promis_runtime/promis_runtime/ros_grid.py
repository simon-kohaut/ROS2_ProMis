"""ROS OccupancyGrid message helpers."""

from __future__ import annotations

import math
from typing import Iterable, List

from nav_msgs.msg import MapMetaData, OccupancyGrid

from promis_runtime.rolling_window import GridSpec


def probabilities_to_grid_data(probabilities: Iterable[float]) -> List[int]:
    """Convert probabilities to OccupancyGrid display values."""

    data: List[int] = []
    for probability in probabilities:
        value = float(probability)
        if math.isnan(value):
            data.append(-1)
        else:
            data.append(min(max(int(round(value * 100.0)), 0), 100))
    return data


def make_occupancy_grid(
    *,
    frame_id: str,
    stamp,
    spec: GridSpec,
    data: Iterable[int],
) -> OccupancyGrid:
    """Build a row-major OccupancyGrid from grid metadata and data."""

    grid = OccupancyGrid()
    grid.header.frame_id = frame_id
    grid.header.stamp = stamp
    grid.info = MapMetaData()
    grid.info.map_load_time = stamp
    grid.info.resolution = float(spec.resolution_m)
    grid.info.width = int(spec.width_cells)
    grid.info.height = int(spec.height_cells)
    grid.info.origin.position.x = float(spec.origin_x)
    grid.info.origin.position.y = float(spec.origin_y)
    grid.info.origin.position.z = 0.0
    grid.info.origin.orientation.w = 1.0
    grid.data = [int(value) for value in data]
    return grid

