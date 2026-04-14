"""Conversions between ProMis probabilities and ROS/Nav2 grid values."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List


UNKNOWN_OCCUPANCY = -1
FREE_OCCUPANCY = 0
OCCUPIED_OCCUPANCY = 100


@dataclass(frozen=True)
class CostConversionConfig:
    """Parameters for converting probability values into occupancy costs."""

    max_occupancy: int = OCCUPIED_OCCUPANCY
    gamma: float = 1.0
    unknown_probability: float = 0.5
    lethal_probability_threshold: float = 0.05
    unknown_on_nan: bool = False


def clamp_probability(value: float) -> float:
    """Clamp a probability into the inclusive [0, 1] interval."""

    if math.isnan(float(value)):
        return 0.0
    return min(max(float(value), 0.0), 1.0)


def probability_to_occupancy(
    probability: float,
    config: CostConversionConfig | None = None,
) -> int:
    """Convert a ProMis satisfaction probability to OccupancyGrid data.

    In this workspace, high probability means semantically preferred and low
    probability means expensive. OccupancyGrid uses low values as free and high
    values as occupied, so the conversion is inverted.
    """

    cfg = config or CostConversionConfig()
    probability = float(probability)

    if math.isnan(probability):
        if cfg.unknown_on_nan:
            return UNKNOWN_OCCUPANCY
        probability = cfg.unknown_probability

    probability = clamp_probability(probability)

    if probability <= cfg.lethal_probability_threshold:
        return OCCUPIED_OCCUPANCY

    gamma = max(float(cfg.gamma), 1.0e-6)
    cost = cfg.max_occupancy * ((1.0 - probability) ** gamma)
    return min(max(int(round(cost)), FREE_OCCUPANCY), OCCUPIED_OCCUPANCY)


def probabilities_to_occupancy(
    probabilities: Iterable[float],
    config: CostConversionConfig | None = None,
) -> List[int]:
    """Convert an iterable of probabilities to OccupancyGrid integer values."""

    return [probability_to_occupancy(value, config) for value in probabilities]


def occupancy_to_probability(occupancy: int) -> float:
    """Approximate the inverse mapping for diagnostics and tests."""

    if int(occupancy) == UNKNOWN_OCCUPANCY:
        return float("nan")
    occupancy = min(max(int(occupancy), FREE_OCCUPANCY), OCCUPIED_OCCUPANCY)
    return 1.0 - (occupancy / float(OCCUPIED_OCCUPANCY))

