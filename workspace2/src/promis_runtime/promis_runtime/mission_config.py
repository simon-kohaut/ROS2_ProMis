"""Mission configuration loading for the ProMis runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import yaml

from promis_runtime.probability_cost import CostConversionConfig
from promis_runtime.rolling_window import RollingWindowConfig


@dataclass(frozen=True)
class RuntimeConfig:
    """Runtime settings used by the ProMis map node."""

    global_frame: str = "map"
    robot_frame: str = "base_link"
    update_rate_hz: float = 1.0
    min_recompute_translation_m: float = 0.5
    min_recompute_yaw_rad: float = 0.35
    stale_timeout_sec: float = 3.0


@dataclass(frozen=True)
class MissionConfig:
    """Normalized mission configuration."""

    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    rolling_window: RollingWindowConfig = field(default_factory=RollingWindowConfig)
    cost_conversion: CostConversionConfig = field(default_factory=CostConversionConfig)
    engine: Dict[str, Any] = field(default_factory=dict)


def _section(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = data.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"mission config section '{key}' must be a mapping")
    return value


def load_mission_config(path: str | Path) -> MissionConfig:
    """Load a mission YAML file and normalize defaults."""

    path = Path(path).expanduser()
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    if not isinstance(raw, dict):
        raise ValueError("mission config root must be a mapping")

    runtime = _section(raw, "runtime")
    rolling = _section(raw, "rolling_window")
    cost = _section(raw, "cost_conversion")
    engine = _section(raw, "engine")

    return MissionConfig(
        runtime=RuntimeConfig(
            global_frame=str(runtime.get("global_frame", "map")),
            robot_frame=str(runtime.get("robot_frame", "base_link")),
            update_rate_hz=float(runtime.get("update_rate_hz", 1.0)),
            min_recompute_translation_m=float(
                runtime.get("min_recompute_translation_m", 0.5)
            ),
            min_recompute_yaw_rad=float(runtime.get("min_recompute_yaw_rad", 0.35)),
            stale_timeout_sec=float(runtime.get("stale_timeout_sec", 3.0)),
        ),
        rolling_window=RollingWindowConfig(
            width_m=float(rolling.get("width_m", 20.0)),
            height_m=float(rolling.get("height_m", 20.0)),
            resolution_m=float(rolling.get("resolution_m", 0.2)),
            snap_to_grid=bool(rolling.get("snap_to_grid", True)),
        ),
        cost_conversion=CostConversionConfig(
            max_occupancy=int(cost.get("max_occupancy", 100)),
            gamma=float(cost.get("gamma", 1.0)),
            unknown_probability=float(cost.get("unknown_probability", 0.5)),
            lethal_probability_threshold=float(
                cost.get("lethal_probability_threshold", 0.05)
            ),
            unknown_on_nan=bool(cost.get("unknown_on_nan", False)),
        ),
        engine=engine,
    )

