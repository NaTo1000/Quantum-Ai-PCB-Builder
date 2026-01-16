"""
Schematic Generator

This module generates PCB/chip schematics from design intent specifications.
It creates structured schematic data that can be exported to various EDA formats.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any
from enum import Enum

from ..nlp.intent_parser import DesignIntent, ComponentSpec, BoardType


class PinType(Enum):
    """Types of component pins."""
    INPUT = "input"
    OUTPUT = "output"
    BIDIRECTIONAL = "bidirectional"
    POWER = "power"
    GROUND = "ground"
    NC = "no_connect"


class NetType(Enum):
    """Types of electrical nets."""
    SIGNAL = "signal"
    POWER = "power"
    GROUND = "ground"
    CLOCK = "clock"
    DIFFERENTIAL = "differential"


@dataclass
class Pin:
    """Represents a component pin."""
    pin_id: str
    name: str
    pin_type: PinType
    number: int
    position: tuple[float, float] = (0.0, 0.0)


@dataclass
class SchematicComponent:
    """A component in the schematic."""
    component_id: str
    reference: str
    component_type: str
    value: str | None
    footprint: str
    pins: list[Pin]
    position: tuple[float, float] = (0.0, 0.0)
    rotation: float = 0.0
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class Net:
    """An electrical connection between pins."""
    net_id: str
    name: str
    net_type: NetType
    connections: list[tuple[str, str]]  # List of (component_id, pin_id)


@dataclass
class Schematic:
    """Complete schematic representation."""
    schematic_id: str
    name: str
    version: str
    components: list[SchematicComponent]
    nets: list[Net]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert schematic to dictionary format."""
        return {
            "schematic_id": self.schematic_id,
            "name": self.name,
            "version": self.version,
            "components": [
                {
                    "id": c.component_id,
                    "reference": c.reference,
                    "type": c.component_type,
                    "value": c.value,
                    "footprint": c.footprint,
                    "position": c.position,
                    "rotation": c.rotation,
                    "pins": [
                        {
                            "id": p.pin_id,
                            "name": p.name,
                            "type": p.pin_type.value,
                            "number": p.number
                        }
                        for p in c.pins
                    ],
                    "properties": c.properties
                }
                for c in self.components
            ],
            "nets": [
                {
                    "id": n.net_id,
                    "name": n.name,
                    "type": n.net_type.value,
                    "connections": n.connections
                }
                for n in self.nets
            ],
            "metadata": self.metadata
        }


class SchematicGenerator:
    """
    Generates schematics from design intent specifications.
    
    This generator creates structured schematic data including components,
    pins, nets, and their interconnections based on the extracted design intent.
    """
    
    # Configuration constants
    DEFAULT_CONNECTOR_PIN_COUNT = 10
    
    # Component library with default configurations
    COMPONENT_LIBRARY: dict[str, dict[str, Any]] = {
        "microcontroller": {
            "esp32": {
                "footprint": "QFN-48",
                "pins": [
                    ("VCC", PinType.POWER, 1),
                    ("GND", PinType.GROUND, 2),
                    ("EN", PinType.INPUT, 3),
                    ("GPIO0", PinType.BIDIRECTIONAL, 4),
                    ("GPIO1", PinType.BIDIRECTIONAL, 5),
                    ("GPIO2", PinType.BIDIRECTIONAL, 6),
                    ("TX", PinType.OUTPUT, 7),
                    ("RX", PinType.INPUT, 8),
                    ("SDA", PinType.BIDIRECTIONAL, 9),
                    ("SCL", PinType.OUTPUT, 10),
                ]
            },
            "generic": {
                "footprint": "DIP-28",
                "pins": [
                    ("VCC", PinType.POWER, 1),
                    ("GND", PinType.GROUND, 14),
                    ("RESET", PinType.INPUT, 2),
                ]
            }
        },
        "resistor": {
            "default": {
                "footprint": "0805",
                "pins": [
                    ("1", PinType.BIDIRECTIONAL, 1),
                    ("2", PinType.BIDIRECTIONAL, 2),
                ]
            }
        },
        "capacitor": {
            "default": {
                "footprint": "0805",
                "pins": [
                    ("+", PinType.BIDIRECTIONAL, 1),
                    ("-", PinType.BIDIRECTIONAL, 2),
                ]
            }
        },
        "led": {
            "default": {
                "footprint": "LED_SMD_0805",
                "pins": [
                    ("A", PinType.INPUT, 1),
                    ("K", PinType.OUTPUT, 2),
                ]
            }
        },
        "regulator": {
            "default": {
                "footprint": "SOT-223",
                "pins": [
                    ("VIN", PinType.POWER, 1),
                    ("GND", PinType.GROUND, 2),
                    ("VOUT", PinType.POWER, 3),
                ]
            }
        },
        "crystal": {
            "default": {
                "footprint": "HC49",
                "pins": [
                    ("X1", PinType.BIDIRECTIONAL, 1),
                    ("X2", PinType.BIDIRECTIONAL, 2),
                ]
            }
        },
        "connector": {
            "default": {
                "footprint": "CONN_HDR_2x5",
                # 10 pins for a standard 2x5 header connector
                "pins": [
                    (f"P{i}", PinType.BIDIRECTIONAL, i) for i in range(1, 11)
                ]
            }
        },
        "sensor": {
            "default": {
                "footprint": "SMD_SENSOR",
                "pins": [
                    ("VCC", PinType.POWER, 1),
                    ("GND", PinType.GROUND, 2),
                    ("DATA", PinType.OUTPUT, 3),
                ]
            }
        },
        "transistor": {
            "default": {
                "footprint": "SOT-23",
                "pins": [
                    ("B", PinType.INPUT, 1),
                    ("C", PinType.OUTPUT, 2),
                    ("E", PinType.OUTPUT, 3),
                ]
            }
        },
        "inductor": {
            "default": {
                "footprint": "1210",
                "pins": [
                    ("1", PinType.BIDIRECTIONAL, 1),
                    ("2", PinType.BIDIRECTIONAL, 2),
                ]
            }
        }
    }
    
    REFERENCE_PREFIXES = {
        "microcontroller": "U",
        "resistor": "R",
        "capacitor": "C",
        "led": "D",
        "regulator": "U",
        "crystal": "Y",
        "connector": "J",
        "sensor": "U",
        "transistor": "Q",
        "inductor": "L",
    }

    def __init__(self):
        """Initialize the schematic generator."""
        self._ref_counters: dict[str, int] = {}

    def generate(self, design_intent: DesignIntent) -> Schematic:
        """
        Generate a schematic from a design intent.
        
        Args:
            design_intent: The parsed design intent specification.
            
        Returns:
            A complete Schematic object.
        """
        self._ref_counters = {}
        
        components = self._generate_components(design_intent)
        nets = self._generate_nets(components, design_intent)
        
        schematic = Schematic(
            schematic_id=str(uuid.uuid4()),
            name=self._generate_name(design_intent),
            version="1.0.0",
            components=components,
            nets=nets,
            metadata={
                "board_type": design_intent.board_type.value,
                "complexity": design_intent.complexity.value,
                "features": design_intent.features,
                "power_requirements": design_intent.power_requirements,
                "constraints": design_intent.constraints,
            }
        )
        
        return schematic

    def _generate_name(self, design_intent: DesignIntent) -> str:
        """Generate a descriptive name for the schematic."""
        board = design_intent.board_type.value.upper()
        features = "_".join(design_intent.features[:3]) if design_intent.features else "basic"
        return f"{board}_{features}_design"

    def _generate_components(self, design_intent: DesignIntent) -> list[SchematicComponent]:
        """Generate schematic components from the design intent."""
        components: list[SchematicComponent] = []
        grid_x, grid_y = 0.0, 0.0
        grid_spacing = 50.0
        max_per_row = 5
        
        # Add main board component if specified
        if design_intent.board_type != BoardType.GENERIC:
            main_component = self._create_board_component(design_intent.board_type)
            components.append(main_component)
            grid_x += grid_spacing
        
        # Add specified components
        for i, comp_spec in enumerate(design_intent.components):
            component = self._create_component(comp_spec)
            
            # Position on grid
            col = i % max_per_row
            row = i // max_per_row
            component.position = (
                grid_x + col * grid_spacing,
                grid_y + row * grid_spacing
            )
            
            components.append(component)
        
        # Add supporting components for features
        feature_components = self._add_feature_components(design_intent.features)
        for comp in feature_components:
            components.append(comp)
        
        return components

    def _create_board_component(self, board_type: BoardType) -> SchematicComponent:
        """Create a component for the main board/MCU."""
        library = self.COMPONENT_LIBRARY.get("microcontroller", {})
        board_config = library.get(board_type.value, library.get("generic", {}))
        
        ref = self._get_next_reference("microcontroller")
        pins = [
            Pin(
                pin_id=str(uuid.uuid4()),
                name=name,
                pin_type=ptype,
                number=num
            )
            for name, ptype, num in board_config.get("pins", [])
        ]
        
        return SchematicComponent(
            component_id=str(uuid.uuid4()),
            reference=ref,
            component_type="microcontroller",
            value=board_type.value.upper(),
            footprint=board_config.get("footprint", "QFN-48"),
            pins=pins,
            properties={"board_type": board_type.value}
        )

    def _create_component(self, comp_spec: ComponentSpec) -> SchematicComponent:
        """Create a schematic component from a component specification."""
        library = self.COMPONENT_LIBRARY.get(comp_spec.component_type, {})
        comp_config = library.get("default", {})
        
        ref = self._get_next_reference(comp_spec.component_type)
        pins = [
            Pin(
                pin_id=str(uuid.uuid4()),
                name=name,
                pin_type=ptype,
                number=num
            )
            for name, ptype, num in comp_config.get("pins", [])
        ]
        
        return SchematicComponent(
            component_id=str(uuid.uuid4()),
            reference=ref,
            component_type=comp_spec.component_type,
            value=comp_spec.value,
            footprint=comp_config.get("footprint", "GENERIC"),
            pins=pins,
            properties=comp_spec.properties
        )

    def _add_feature_components(self, features: list[str]) -> list[SchematicComponent]:
        """Add supporting components for requested features."""
        components: list[SchematicComponent] = []
        
        # Common bypass capacitors for power stability
        if features:
            cap_spec = ComponentSpec(
                name="bypass_cap",
                component_type="capacitor",
                value="100nF",
                quantity=1
            )
            components.append(self._create_component(cap_spec))
        
        # USB features require protection components
        if "usb" in features:
            # ESD protection
            components.append(SchematicComponent(
                component_id=str(uuid.uuid4()),
                reference=self._get_next_reference("transistor"),
                component_type="esd_protection",
                value="USBLC6-2",
                footprint="SOT-23-6",
                pins=[
                    Pin(str(uuid.uuid4()), "D+", PinType.BIDIRECTIONAL, 1),
                    Pin(str(uuid.uuid4()), "D-", PinType.BIDIRECTIONAL, 2),
                    Pin(str(uuid.uuid4()), "VCC", PinType.POWER, 3),
                    Pin(str(uuid.uuid4()), "GND", PinType.GROUND, 4),
                ]
            ))
        
        # Battery feature requires charging circuit
        if "battery" in features:
            components.append(SchematicComponent(
                component_id=str(uuid.uuid4()),
                reference=self._get_next_reference("regulator"),
                component_type="battery_charger",
                value="MCP73831",
                footprint="SOT-23-5",
                pins=[
                    Pin(str(uuid.uuid4()), "VIN", PinType.POWER, 1),
                    Pin(str(uuid.uuid4()), "VBAT", PinType.POWER, 2),
                    Pin(str(uuid.uuid4()), "STAT", PinType.OUTPUT, 3),
                    Pin(str(uuid.uuid4()), "GND", PinType.GROUND, 4),
                ]
            ))
        
        return components

    def _get_next_reference(self, component_type: str) -> str:
        """Get the next reference designator for a component type."""
        prefix = self.REFERENCE_PREFIXES.get(component_type, "X")
        if prefix not in self._ref_counters:
            self._ref_counters[prefix] = 0
        self._ref_counters[prefix] += 1
        return f"{prefix}{self._ref_counters[prefix]}"

    def _generate_nets(
        self,
        components: list[SchematicComponent],
        design_intent: DesignIntent
    ) -> list[Net]:
        """Generate electrical nets connecting components."""
        nets: list[Net] = []
        
        # Create power and ground nets
        vcc_connections = []
        gnd_connections = []
        
        for comp in components:
            for pin in comp.pins:
                if pin.pin_type == PinType.POWER:
                    vcc_connections.append((comp.component_id, pin.pin_id))
                elif pin.pin_type == PinType.GROUND:
                    gnd_connections.append((comp.component_id, pin.pin_id))
        
        if vcc_connections:
            voltage = design_intent.power_requirements.get("voltage", 3.3)
            nets.append(Net(
                net_id=str(uuid.uuid4()),
                name=f"VCC_{voltage}V",
                net_type=NetType.POWER,
                connections=vcc_connections
            ))
        
        if gnd_connections:
            nets.append(Net(
                net_id=str(uuid.uuid4()),
                name="GND",
                net_type=NetType.GROUND,
                connections=gnd_connections
            ))
        
        return nets
