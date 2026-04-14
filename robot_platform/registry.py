from typing import Dict, List, Type

from robot_platform.adapters.base import RobotAdapter
from robot_platform.adapters.generic_mobile_base import GenericMobileBaseAdapter
from robot_platform.adapters.turtlebot3 import TurtleBot3Adapter


_ADAPTERS: Dict[str, Type[RobotAdapter]] = {
    "generic_mobile_base": GenericMobileBaseAdapter,
    "differential_drive": GenericMobileBaseAdapter,
    "turtlebot3": TurtleBot3Adapter,
}


def register_adapter(name: str, adapter_cls: Type[RobotAdapter]) -> None:
    _ADAPTERS[name.strip().lower()] = adapter_cls


def available_adapters() -> List[str]:
    return sorted(_ADAPTERS.keys())


def create_adapter(robot_type: str) -> RobotAdapter:
    key = robot_type.strip().lower()
    adapter_cls = _ADAPTERS.get(key)
    if adapter_cls is None:
        supported = ", ".join(available_adapters())
        raise ValueError(
            f"Unsupported robot_type '{robot_type}'. Available adapters: {supported}"
        )
    return adapter_cls()
