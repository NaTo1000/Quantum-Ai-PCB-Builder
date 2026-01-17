"""
Component definitions for PCB design.

This module provides the core component representations used throughout
the PCB design system, including microcontrollers, sensors, and other
electronic components.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class ComponentType(Enum):
    """Enumeration of supported electronic component types."""

    MICROCONTROLLER = auto()
    RESISTOR = auto()
    CAPACITOR = auto()
    INDUCTOR = auto()
    TRANSISTOR = auto()
    DIODE = auto()
    LED = auto()
    SENSOR = auto()
    CONNECTOR = auto()
    CRYSTAL = auto()
    VOLTAGE_REGULATOR = auto()
    RF_MODULE = auto()
    ANTENNA = auto()
    IC = auto()
    SWITCH = auto()
    RELAY = auto()
    TRANSFORMER = auto()
    FUSE = auto()
    BATTERY = auto()
    CUSTOM = auto()


@dataclass
class Pin:
    """Represents a component pin for electrical connections."""

    name: str
    number: int
    pin_type: str = "io"
    voltage: float = 3.3
    connected_to: str | None = None


@dataclass
class Footprint:
    """Physical footprint specification for PCB placement."""

    name: str
    width_mm: float
    height_mm: float
    pin_count: int
    smd: bool = True
    thermal_pad: bool = False


@dataclass
class Component:
    """
    Represents an electronic component for PCB design.

    This class encapsulates all properties needed for component placement,
    routing, and manufacturing in a PCB design workflow.

    Attributes:
        name: Human-readable component name
        component_type: Category of the component
        value: Component value (e.g., "10kΩ", "100nF")
        package: Package type (e.g., "0805", "QFP-48")
        footprint: Physical footprint specification
        pins: List of component pins
        position: (x, y) position on PCB in mm
        rotation: Rotation angle in degrees
        layer: PCB layer for placement
        properties: Additional component-specific properties
    """

    name: str
    component_type: ComponentType
    value: str = ""
    package: str = ""
    footprint: Footprint | None = None
    pins: list[Pin] = field(default_factory=list)
    position: tuple[float, float] = (0.0, 0.0)
    rotation: float = 0.0
    layer: str = "top"
    properties: dict[str, Any] = field(default_factory=dict)
    uuid: str = field(default_factory=lambda: str(uuid4()))

    def get_bounding_box(self) -> tuple[float, float, float, float]:
        """
        Calculate the bounding box of the component.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y) in mm
        """
        if self.footprint is None:
            return (self.position[0], self.position[1], self.position[0], self.position[1])

        half_w = self.footprint.width_mm / 2
        half_h = self.footprint.height_mm / 2
        return (
            self.position[0] - half_w,
            self.position[1] - half_h,
            self.position[0] + half_w,
            self.position[1] + half_h,
        )

    def get_area(self) -> float:
        """Calculate the area occupied by the component in mm²."""
        if self.footprint is None:
            return 0.0
        return self.footprint.width_mm * self.footprint.height_mm

    def distance_to(self, other: "Component") -> float:
        """Calculate Euclidean distance to another component."""
        dx = self.position[0] - other.position[0]
        dy = self.position[1] - other.position[1]
        return (dx * dx + dy * dy) ** 0.5

    def overlaps(self, other: "Component", margin: float = 0.5) -> bool:
        """
        Check if this component overlaps with another.

        Args:
            other: Another component to check against
            margin: Minimum spacing margin in mm

        Returns:
            True if components overlap (including margin)
        """
        bb1 = self.get_bounding_box()
        bb2 = other.get_bounding_box()

        return not (
            bb1[2] + margin < bb2[0]
            or bb1[0] - margin > bb2[2]
            or bb1[3] + margin < bb2[1]
            or bb1[1] - margin > bb2[3]
        )


# Pre-defined common component templates
COMMON_COMPONENTS: dict[str, dict[str, Any]] = {
    "ESP32-WROOM-32": {
        "component_type": ComponentType.MICROCONTROLLER,
        "package": "SMD",
        "footprint": Footprint("ESP32-WROOM-32", 18.0, 25.5, 38, smd=True),
        "properties": {
            "cpu": "Xtensa LX6",
            "frequency_mhz": 240,
            "flash_mb": 4,
            "wifi": True,
            "bluetooth": True,
        },
    },
    "SX1276": {
        "component_type": ComponentType.RF_MODULE,
        "package": "QFN-28",
        "footprint": Footprint("QFN-28", 6.0, 6.0, 28, smd=True, thermal_pad=True),
        "properties": {
            "frequency_mhz": 868,
            "protocol": "LoRa",
            "sensitivity_dbm": -148,
            "tx_power_dbm": 20,
        },
    },
    "AMS1117-3.3": {
        "component_type": ComponentType.VOLTAGE_REGULATOR,
        "package": "SOT-223",
        "footprint": Footprint("SOT-223", 6.5, 3.5, 3, smd=True),
        "properties": {
            "voltage_in_max": 15.0,
            "voltage_out": 3.3,
            "current_max_ma": 1000,
        },
    },
}


def create_component_from_template(template_name: str, name: str) -> Component:
    """
    Create a component instance from a pre-defined template.

    Args:
        template_name: Name of the template (e.g., "ESP32-WROOM-32")
        name: Instance name for this component

    Returns:
        Configured Component instance

    Raises:
        ValueError: If template_name is not found
    """
    if template_name not in COMMON_COMPONENTS:
        raise ValueError(f"Unknown component template: {template_name}")

    template = COMMON_COMPONENTS[template_name]
    return Component(
        name=name,
        component_type=template["component_type"],
        package=template["package"],
        footprint=template["footprint"],
        properties=template.get("properties", {}),
    )
