"""Landscape engines for producing ProMis-style probabilities."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Protocol, Tuple


Coordinate = Tuple[float, float]


class LandscapeEngine(Protocol):
    """Protocol implemented by probability landscape engines."""

    name: str

    def evaluate(self, coordinates: Iterable[Coordinate]) -> List[float]:
        """Return one satisfaction probability per coordinate."""


@dataclass(frozen=True)
class ForbiddenZone:
    """Simple circular low-probability zone used by the demo engine."""

    x: float
    y: float
    radius_m: float
    probability: float


class DemoLandscapeEngine:
    """Deterministic ProMis-like engine for RViz-only validation."""

    name = "demo"

    def __init__(self, config: Dict[str, Any]) -> None:
        demo = config.get("demo", {}) if isinstance(config.get("demo", {}), dict) else {}
        self.preferred_corridor = str(demo.get("preferred_corridor", "top"))
        self.corridor_split_y = float(demo.get("corridor_split_y", 0.0))
        self.corridor_sigma_m = max(float(demo.get("corridor_sigma_m", 2.0)), 1.0e-6)
        self.base_probability = float(demo.get("base_probability", 0.55))
        self.preferred_bonus = float(demo.get("preferred_bonus", 0.35))
        self.opposite_penalty = float(demo.get("opposite_penalty", 0.25))
        self.wave_amplitude = float(demo.get("wave_amplitude", 0.08))
        self.wave_length_m = max(float(demo.get("wave_length_m", 8.0)), 1.0e-6)
        self.forbidden_zones = self._read_forbidden_zones(demo)

    def evaluate(self, coordinates: Iterable[Coordinate]) -> List[float]:
        probabilities: List[float] = []
        for x, y in coordinates:
            prob = self._corridor_probability(float(x), float(y))
            prob += self.wave_amplitude * math.sin(float(x) / self.wave_length_m)
            for zone in self.forbidden_zones:
                dist = math.hypot(float(x) - zone.x, float(y) - zone.y)
                if dist <= zone.radius_m:
                    influence = 1.0 - dist / max(zone.radius_m, 1.0e-6)
                    prob = min(prob, zone.probability + (1.0 - influence) * 0.2)
            probabilities.append(min(max(prob, 0.0), 1.0))
        return probabilities

    def _corridor_probability(self, x: float, y: float) -> float:
        del x
        signed_y = y - self.corridor_split_y
        prefers_top = self.preferred_corridor.lower() != "bottom"
        on_preferred_side = signed_y >= 0.0 if prefers_top else signed_y <= 0.0
        distance_from_split = abs(signed_y)
        corridor_shape = 1.0 - math.exp(
            -(distance_from_split**2) / (2.0 * self.corridor_sigma_m**2)
        )
        if on_preferred_side:
            return self.base_probability + self.preferred_bonus * corridor_shape
        return self.base_probability - self.opposite_penalty * corridor_shape

    @staticmethod
    def _read_forbidden_zones(demo: Dict[str, Any]) -> List[ForbiddenZone]:
        zones: List[ForbiddenZone] = []
        for item in demo.get("forbidden_zones", []):
            if not isinstance(item, dict):
                continue
            center = item.get("center", [0.0, 0.0])
            zones.append(
                ForbiddenZone(
                    x=float(center[0]),
                    y=float(center[1]),
                    radius_m=float(item.get("radius_m", 1.0)),
                    probability=float(item.get("probability", 0.02)),
                )
            )
        return zones


class ProMisLandscapeEngine:
    """Thin adapter around the official ProMis Python API.

    This engine expects a precomputed StaRMap pickle and a logic program in the
    mission config. That keeps the ROS node focused on runtime evaluation while
    still allowing a real ProMis backend when the data is available.
    """

    name = "promis"

    def __init__(self, config: Dict[str, Any]) -> None:
        promis_config = (
            config.get("promis", {}) if isinstance(config.get("promis", {}), dict) else {}
        )
        star_map_path = promis_config.get("star_map_pickle")
        logic = promis_config.get("logic")
        if not star_map_path:
            raise ValueError("engine.promis.star_map_pickle is required")
        if not logic:
            raise ValueError("engine.promis.logic is required")

        try:
            from promis import ProMis
        except ImportError:
            from promis.promis import ProMis
        from promis.geo import CartesianCollection
        from promis.star_map import StaRMap

        self._cartesian_collection_type = CartesianCollection
        self._star_map = StaRMap.load(str(Path(star_map_path).expanduser()))
        self._promis = ProMis(self._star_map)
        self._logic = str(logic)
        self._n_jobs = promis_config.get("n_jobs")
        self._batch_size = int(promis_config.get("batch_size", 10))
        self._interpolation_method = str(promis_config.get("interpolation_method", "linear"))

    def evaluate(self, coordinates: Iterable[Coordinate]) -> List[float]:
        import numpy as np

        coordinate_list = list(coordinates)
        points = self._cartesian_collection_type(self._star_map.uam.origin)
        points.append_with_default(np.asarray(coordinate_list, dtype=float), 0.0)
        self._promis.solve(
            points,
            self._logic,
            n_jobs=self._n_jobs,
            batch_size=self._batch_size,
            interpolation_method=self._interpolation_method,
        )
        return [float(value) for value in points.data["v0"].to_numpy()]


def create_landscape_engine(config: Dict[str, Any]) -> LandscapeEngine:
    """Create the configured landscape engine."""

    mode = str(config.get("mode", "demo")).lower()
    if mode == "promis":
        return ProMisLandscapeEngine(config)
    if mode == "auto":
        try:
            return ProMisLandscapeEngine(config)
        except Exception:
            return DemoLandscapeEngine(config)
    if mode == "demo":
        return DemoLandscapeEngine(config)
    raise ValueError(f"Unsupported ProMis engine mode: {mode}")
