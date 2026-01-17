"""PCB layout management."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from quantum_pcb_builder.core.base import BaseComponent, BaseDesign


class LayerType(Enum):
    """Types of PCB layers."""

    TOP = "top"
    BOTTOM = "bottom"
    INNER1 = "inner1"
    INNER2 = "inner2"
    SILKSCREEN_TOP = "silkscreen_top"
    SILKSCREEN_BOTTOM = "silkscreen_bottom"
    SOLDER_MASK_TOP = "solder_mask_top"
    SOLDER_MASK_BOTTOM = "solder_mask_bottom"


@dataclass
class Position:
    """2D position on the PCB."""

    x: float
    y: float
    rotation: float = 0.0  # Rotation in degrees
    layer: LayerType = LayerType.TOP

    def to_dict(self) -> dict[str, Any]:
        """Serialize position to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "rotation": self.rotation,
            "layer": self.layer.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Position:
        """Create position from dictionary."""
        return cls(
            x=data["x"],
            y=data["y"],
            rotation=data.get("rotation", 0.0),
            layer=LayerType(data.get("layer", "top")),
        )

    def distance_to(self, other: Position) -> float:
        """Calculate distance to another position."""
        return float(((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5)


@dataclass
class Connection:
    """Represents a connection between two components."""

    connection_id: str = field(default_factory=lambda: str(uuid4()))
    source_component_id: str = ""
    source_pin: str = ""
    target_component_id: str = ""
    target_pin: str = ""
    net_name: str = ""
    trace_width_mm: float = 0.25

    def to_dict(self) -> dict[str, Any]:
        """Serialize connection to dictionary."""
        return {
            "connection_id": self.connection_id,
            "source_component_id": self.source_component_id,
            "source_pin": self.source_pin,
            "target_component_id": self.target_component_id,
            "target_pin": self.target_pin,
            "net_name": self.net_name,
            "trace_width_mm": self.trace_width_mm,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Connection:
        """Create connection from dictionary."""
        return cls(
            connection_id=data.get("connection_id", str(uuid4())),
            source_component_id=data["source_component_id"],
            source_pin=data.get("source_pin", ""),
            target_component_id=data["target_component_id"],
            target_pin=data.get("target_pin", ""),
            net_name=data.get("net_name", ""),
            trace_width_mm=data.get("trace_width_mm", 0.25),
        )

    def validate(self) -> bool:
        """Validate the connection."""
        return bool(self.source_component_id and self.target_component_id)


@dataclass
class Layer:
    """Represents a PCB layer."""

    layer_type: LayerType
    thickness_mm: float = 0.035  # Copper thickness
    traces: list[Connection] = field(default_factory=list)

    def add_trace(self, connection: Connection) -> None:
        """Add a trace to this layer."""
        self.traces.append(connection)

    def to_dict(self) -> dict[str, Any]:
        """Serialize layer to dictionary."""
        return {
            "layer_type": self.layer_type.value,
            "thickness_mm": self.thickness_mm,
            "traces": [t.to_dict() for t in self.traces],
        }


@dataclass
class PlacedComponent:
    """A component with its position on the PCB."""

    component: BaseComponent
    position: Position

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "component": self.component.to_dict(),
            "position": self.position.to_dict(),
        }


class PCBLayout(BaseDesign):
    """PCB layout with component placement and routing."""

    def __init__(
        self,
        name: str,
        description: str = "",
        width_mm: float = 100.0,
        height_mm: float = 100.0,
        layer_count: int = 2,
    ) -> None:
        """Initialize PCB layout."""
        super().__init__(name=name, description=description)
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.layer_count = layer_count
        self._placements: dict[str, Position] = {}
        self._connections: list[Connection] = []
        self._layers: list[Layer] = self._create_layers(layer_count)

    def _create_layers(self, count: int) -> list[Layer]:
        """Create the PCB layers."""
        layers = [Layer(LayerType.TOP), Layer(LayerType.BOTTOM)]
        if count > 2:
            layers.insert(1, Layer(LayerType.INNER1))
        if count > 3:
            layers.insert(2, Layer(LayerType.INNER2))
        return layers

    def place_component(self, component: BaseComponent, position: Position) -> bool:
        """Place a component at a specific position."""
        # Check bounds
        if not self._is_within_bounds(position):
            return False

        # Add component if not already in design
        existing = self.get_component(component.component_id)
        if existing is None:
            self.add_component(component)

        self._placements[component.component_id] = position
        return True

    def _is_within_bounds(self, position: Position) -> bool:
        """Check if a position is within PCB bounds."""
        return 0 <= position.x <= self.width_mm and 0 <= position.y <= self.height_mm

    def get_placement(self, component_id: str) -> Position | None:
        """Get the position of a placed component."""
        return self._placements.get(component_id)

    def connect_components(
        self,
        source_id: str,
        target_id: str,
        source_pin: str = "",
        target_pin: str = "",
        net_name: str = "",
    ) -> Connection | None:
        """Create a connection between two components."""
        source = self.get_component(source_id)
        target = self.get_component(target_id)

        if source is None or target is None:
            return None

        connection = Connection(
            source_component_id=source_id,
            source_pin=source_pin,
            target_component_id=target_id,
            target_pin=target_pin,
            net_name=net_name,
        )
        self._connections.append(connection)
        return connection

    def get_connections(self) -> list[Connection]:
        """Get all connections in the layout."""
        return self._connections.copy()

    def get_component_connections(self, component_id: str) -> list[Connection]:
        """Get all connections for a specific component."""
        return [
            c
            for c in self._connections
            if c.source_component_id == component_id or c.target_component_id == component_id
        ]

    def validate(self) -> tuple[bool, list[str]]:
        """Validate the PCB layout."""
        is_valid, issues = super().validate()

        # Check all components are placed
        for comp in self.components:
            if comp.component_id not in self._placements:
                issues.append(f"Component {comp.name} is not placed on the PCB")
                is_valid = False

        # Check all connections are valid
        for conn in self._connections:
            if not conn.validate():
                issues.append(f"Invalid connection: {conn.connection_id}")
                is_valid = False

        # Check for out-of-bounds placements
        for comp_id, pos in self._placements.items():
            if not self._is_within_bounds(pos):
                issues.append(f"Component {comp_id} is placed outside PCB bounds")
                is_valid = False

        return (is_valid, issues)

    def to_dict(self) -> dict[str, Any]:
        """Serialize layout to dictionary."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "width_mm": self.width_mm,
                "height_mm": self.height_mm,
                "layer_count": self.layer_count,
                "placements": {k: v.to_dict() for k, v in self._placements.items()},
                "connections": [c.to_dict() for c in self._connections],
                "layers": [layer.to_dict() for layer in self._layers],
            }
        )
        return base_dict

    def get_placed_components(self) -> list[PlacedComponent]:
        """Get all placed components with their positions."""
        result = []
        for comp in self.components:
            pos = self._placements.get(comp.component_id)
            if pos:
                result.append(PlacedComponent(component=comp, position=pos))
        return result
