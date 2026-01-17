"""
PCB Board representation for physical layout.

This module provides classes for representing the physical PCB,
including layers, routing areas, and design rule specifications.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any
from uuid import uuid4

from quantum_pcb_builder.core.component import Component


class PCBLayer(Enum):
    """Enumeration of PCB layers."""

    TOP_COPPER = auto()
    BOTTOM_COPPER = auto()
    INNER_1 = auto()
    INNER_2 = auto()
    TOP_SILKSCREEN = auto()
    BOTTOM_SILKSCREEN = auto()
    TOP_SOLDER_MASK = auto()
    BOTTOM_SOLDER_MASK = auto()
    TOP_PASTE = auto()
    BOTTOM_PASTE = auto()
    EDGE_CUTS = auto()


@dataclass
class DesignRules:
    """Design rules for PCB manufacturing constraints."""

    min_trace_width_mm: float = 0.15
    min_clearance_mm: float = 0.15
    min_via_diameter_mm: float = 0.4
    min_via_drill_mm: float = 0.2
    min_annular_ring_mm: float = 0.1
    min_silk_width_mm: float = 0.15
    copper_weight_oz: float = 1.0
    board_thickness_mm: float = 1.6

    def validate_trace(self, width: float) -> bool:
        """Check if trace width meets design rules."""
        return width >= self.min_trace_width_mm

    def validate_clearance(self, clearance: float) -> bool:
        """Check if clearance meets design rules."""
        return clearance >= self.min_clearance_mm


@dataclass
class Via:
    """Represents a via connecting multiple layers."""

    position: tuple[float, float]
    diameter_mm: float = 0.4
    drill_mm: float = 0.2
    start_layer: PCBLayer = PCBLayer.TOP_COPPER
    end_layer: PCBLayer = PCBLayer.BOTTOM_COPPER
    net_name: str = ""
    uuid: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class TraceSegment:
    """Represents a single trace segment on a PCB layer."""

    start: tuple[float, float]
    end: tuple[float, float]
    width_mm: float = 0.25
    layer: PCBLayer = PCBLayer.TOP_COPPER
    net_name: str = ""
    uuid: str = field(default_factory=lambda: str(uuid4()))

    def get_length(self) -> float:
        """Calculate the length of this trace segment."""
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        return (dx * dx + dy * dy) ** 0.5

    def get_manhattan_length(self) -> float:
        """Calculate Manhattan distance of this segment."""
        return abs(self.end[0] - self.start[0]) + abs(self.end[1] - self.start[1])


@dataclass
class Zone:
    """Represents a copper zone (pour) on a PCB layer."""

    name: str
    vertices: list[tuple[float, float]]
    layer: PCBLayer = PCBLayer.TOP_COPPER
    net_name: str = ""
    priority: int = 0
    properties: dict[str, Any] = field(default_factory=dict)
    uuid: str = field(default_factory=lambda: str(uuid4()))

    def get_area(self) -> float:
        """Calculate the area of this zone using shoelace formula."""
        n = len(self.vertices)
        if n < 3:
            return 0.0

        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += self.vertices[i][0] * self.vertices[j][1]
            area -= self.vertices[j][0] * self.vertices[i][1]

        return abs(area) / 2.0


class PCBBoard:
    """
    Represents a complete PCB board with all design elements.

    This class manages the physical PCB layout including components,
    traces, vias, zones, and design rules.

    Attributes:
        name: Board name/identifier
        width_mm: Board width in millimeters
        height_mm: Board height in millimeters
        layer_count: Number of copper layers
        design_rules: Manufacturing design rules
    """

    def __init__(
        self,
        name: str = "Untitled Board",
        width_mm: float = 100.0,
        height_mm: float = 100.0,
        layer_count: int = 2,
    ) -> None:
        """Initialize a new PCB board."""
        self.name = name
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.layer_count = layer_count
        self.design_rules = DesignRules()

        self.components: dict[str, Component] = {}
        self.traces: list[TraceSegment] = []
        self.vias: list[Via] = []
        self.zones: list[Zone] = []

        self._uuid = str(uuid4())
        self._layers = self._initialize_layers()

    @property
    def uuid(self) -> str:
        """Return the unique identifier for this board."""
        return self._uuid

    def _initialize_layers(self) -> list[PCBLayer]:
        """Initialize available copper layers based on layer count."""
        layers = [PCBLayer.TOP_COPPER, PCBLayer.BOTTOM_COPPER]
        if self.layer_count > 2:
            layers.append(PCBLayer.INNER_1)
        if self.layer_count > 3:
            layers.append(PCBLayer.INNER_2)
        return layers

    def place_component(
        self,
        component: Component,
        position: tuple[float, float],
        rotation: float = 0.0,
        layer: str = "top",
    ) -> bool:
        """
        Place a component on the board.

        Args:
            component: Component to place
            position: (x, y) position in mm
            rotation: Rotation angle in degrees
            layer: Layer for placement ("top" or "bottom")

        Returns:
            True if placement was successful
        """
        if not self._is_within_bounds(position, component):
            return False

        component.position = position
        component.rotation = rotation
        component.layer = layer
        self.components[component.uuid] = component
        return True

    def _is_within_bounds(self, position: tuple[float, float], component: Component) -> bool:
        """Check if component placement is within board bounds."""
        if component.footprint is None:
            return 0 <= position[0] <= self.width_mm and 0 <= position[1] <= self.height_mm

        half_w = component.footprint.width_mm / 2
        half_h = component.footprint.height_mm / 2

        return (
            half_w <= position[0] <= self.width_mm - half_w
            and half_h <= position[1] <= self.height_mm - half_h
        )

    def add_trace(self, trace: TraceSegment) -> bool:
        """
        Add a trace segment to the board.

        Args:
            trace: Trace segment to add

        Returns:
            True if trace was added successfully
        """
        if not self.design_rules.validate_trace(trace.width_mm):
            return False

        self.traces.append(trace)
        return True

    def add_via(self, via: Via) -> bool:
        """
        Add a via to the board.

        Args:
            via: Via to add

        Returns:
            True if via was added successfully
        """
        if via.diameter_mm < self.design_rules.min_via_diameter_mm:
            return False
        if via.drill_mm < self.design_rules.min_via_drill_mm:
            return False

        self.vias.append(via)
        return True

    def add_zone(self, zone: Zone) -> None:
        """Add a copper zone to the board."""
        self.zones.append(zone)

    def get_total_trace_length(self) -> float:
        """Calculate the total length of all traces."""
        return sum(trace.get_length() for trace in self.traces)

    def get_via_count(self) -> int:
        """Return the number of vias on the board."""
        return len(self.vias)

    def get_component_density(self) -> float:
        """
        Calculate component density as ratio of component area to board area.

        Returns:
            Density ratio (0.0 to 1.0)
        """
        board_area = self.width_mm * self.height_mm
        component_area = sum(comp.get_area() for comp in self.components.values())
        return component_area / board_area if board_area > 0 else 0.0

    def get_layer_utilization(self, layer: PCBLayer) -> float:
        """
        Calculate trace utilization for a specific layer.

        Args:
            layer: PCB layer to analyze

        Returns:
            Estimated utilization ratio
        """
        board_area = self.width_mm * self.height_mm
        layer_traces = [t for t in self.traces if t.layer == layer]
        trace_area = sum(t.get_length() * t.width_mm for t in layer_traces)
        return trace_area / board_area if board_area > 0 else 0.0

    def check_design_rule_violations(self) -> list[str]:
        """
        Check for design rule violations.

        Returns:
            List of violation messages
        """
        violations = []

        # Check trace widths
        for trace in self.traces:
            if trace.width_mm < self.design_rules.min_trace_width_mm:
                violations.append(
                    f"Trace at {trace.start} has width {trace.width_mm}mm "
                    f"(min: {self.design_rules.min_trace_width_mm}mm)"
                )

        # Check vias
        for via in self.vias:
            if via.diameter_mm < self.design_rules.min_via_diameter_mm:
                violations.append(
                    f"Via at {via.position} has diameter {via.diameter_mm}mm "
                    f"(min: {self.design_rules.min_via_diameter_mm}mm)"
                )

        # Check component overlaps
        comp_list = list(self.components.values())
        for i, comp1 in enumerate(comp_list):
            for comp2 in comp_list[i + 1 :]:
                if comp1.layer == comp2.layer and comp1.overlaps(
                    comp2, self.design_rules.min_clearance_mm
                ):
                    violations.append(
                        f"Components '{comp1.name}' and '{comp2.name}' violate clearance rules"
                    )

        return violations

    def get_manufacturing_summary(self) -> dict[str, Any]:
        """
        Generate a summary for manufacturing.

        Returns:
            Dictionary with manufacturing-relevant information
        """
        return {
            "name": self.name,
            "dimensions_mm": (self.width_mm, self.height_mm),
            "layer_count": self.layer_count,
            "component_count": len(self.components),
            "via_count": len(self.vias),
            "total_trace_length_mm": self.get_total_trace_length(),
            "component_density": self.get_component_density(),
            "design_rules": {
                "min_trace_width_mm": self.design_rules.min_trace_width_mm,
                "min_clearance_mm": self.design_rules.min_clearance_mm,
                "copper_weight_oz": self.design_rules.copper_weight_oz,
                "board_thickness_mm": self.design_rules.board_thickness_mm,
            },
        }

    def __repr__(self) -> str:
        """Return string representation of the board."""
        return (
            f"PCBBoard(name='{self.name}', "
            f"size={self.width_mm}x{self.height_mm}mm, "
            f"layers={self.layer_count}, "
            f"components={len(self.components)})"
        )
