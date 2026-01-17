"""AI-powered PCB designer."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from quantum_pcb_builder.core.base import BaseComponent
from quantum_pcb_builder.pcb.components import (
    CommunicationModule,
    ComponentLibrary,
    Microcontroller,
    PowerModule,
    Sensor,
)
from quantum_pcb_builder.pcb.layout import PCBLayout, Position


class ApplicationDomain(Enum):
    """Application domains for PCB designs."""

    IOT = "iot"
    INDUSTRIAL = "industrial"
    CONSUMER = "consumer"
    AUTOMOTIVE = "automotive"
    MEDICAL = "medical"
    AEROSPACE = "aerospace"


class CommunicationType(Enum):
    """Types of communication required."""

    WIFI = "wifi"
    BLUETOOTH = "bluetooth"
    LORA = "lora"
    ZIGBEE = "zigbee"
    CELLULAR = "cellular"
    NONE = "none"


@dataclass
class DesignRequirements:
    """Requirements for generating a PCB design."""

    name: str
    description: str = ""
    domain: ApplicationDomain = ApplicationDomain.IOT
    communication_types: list[CommunicationType] = field(
        default_factory=lambda: [CommunicationType.WIFI]
    )
    sensor_types: list[str] = field(default_factory=list)
    power_source: str = "battery"
    target_size_mm: tuple[float, float] = (100.0, 100.0)
    layer_count: int = 2
    budget_constraints: dict[str, float] = field(default_factory=dict)
    additional_requirements: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize requirements to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "domain": self.domain.value,
            "communication_types": [ct.value for ct in self.communication_types],
            "sensor_types": self.sensor_types,
            "power_source": self.power_source,
            "target_size_mm": list(self.target_size_mm),
            "layer_count": self.layer_count,
            "budget_constraints": self.budget_constraints,
            "additional_requirements": self.additional_requirements,
        }


@dataclass
class DesignSuggestion:
    """A suggested component or modification for a design."""

    suggestion_id: str = field(default_factory=lambda: str(uuid4()))
    category: str = ""
    title: str = ""
    description: str = ""
    component: BaseComponent | None = None
    confidence: float = 0.0  # 0.0 to 1.0
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize suggestion to dictionary."""
        return {
            "suggestion_id": self.suggestion_id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "component": self.component.to_dict() if self.component else None,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }


class AIDesigner:
    """AI-powered autonomous PCB designer."""

    def __init__(self) -> None:
        """Initialize the AI designer."""
        self.component_library = ComponentLibrary()
        self._design_templates: dict[ApplicationDomain, dict[str, Any]] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load design templates for different domains."""
        self._design_templates[ApplicationDomain.IOT] = {
            "microcontroller": "esp32",
            "communication": ["wifi", "lora"],
            "sensors": ["dht22"],
            "power": "ams1117",
        }
        self._design_templates[ApplicationDomain.INDUSTRIAL] = {
            "microcontroller": "esp32_s3",
            "communication": ["wifi"],
            "sensors": [],
            "power": "ams1117",
        }

    def generate_design(self, requirements: DesignRequirements) -> PCBLayout:
        """Generate a PCB design based on requirements."""
        layout = PCBLayout(
            name=requirements.name,
            description=requirements.description,
            width_mm=requirements.target_size_mm[0],
            height_mm=requirements.target_size_mm[1],
            layer_count=requirements.layer_count,
        )

        # Add microcontroller
        mcu = self._select_microcontroller(requirements)
        layout.place_component(mcu, Position(x=layout.width_mm / 2, y=layout.height_mm / 2))

        # Add communication modules
        comm_offset: float = 0.0
        for comm_type in requirements.communication_types:
            comm_module = self._select_communication_module(comm_type)
            if comm_module:
                layout.place_component(
                    comm_module,
                    Position(
                        x=layout.width_mm * 0.8,
                        y=layout.height_mm * 0.3 + comm_offset,
                    ),
                )
                layout.connect_components(
                    mcu.component_id, comm_module.component_id, net_name="SPI"
                )
                comm_offset += 15.0

        # Add sensors
        sensor_offset: float = 0.0
        for sensor_type in requirements.sensor_types:
            sensor = self._select_sensor(sensor_type)
            if sensor:
                layout.place_component(
                    sensor,
                    Position(
                        x=layout.width_mm * 0.2,
                        y=layout.height_mm * 0.3 + sensor_offset,
                    ),
                )
                layout.connect_components(mcu.component_id, sensor.component_id, net_name="I2C")
                sensor_offset += 10.0

        # Add power module
        power = self._select_power_module(requirements)
        layout.place_component(power, Position(x=layout.width_mm * 0.1, y=layout.height_mm * 0.9))
        layout.connect_components(power.component_id, mcu.component_id, net_name="VCC")

        return layout

    def _select_microcontroller(self, requirements: DesignRequirements) -> Microcontroller:
        """Select appropriate microcontroller based on requirements."""
        # Use ESP32-S3 for more demanding applications
        if requirements.domain in [
            ApplicationDomain.INDUSTRIAL,
            ApplicationDomain.AUTOMOTIVE,
        ]:
            return Microcontroller.esp32_s3(name=f"{requirements.name}_MCU")
        return Microcontroller.esp32(name=f"{requirements.name}_MCU")

    def _select_communication_module(
        self, comm_type: CommunicationType
    ) -> CommunicationModule | None:
        """Select appropriate communication module."""
        if comm_type == CommunicationType.LORA:
            return CommunicationModule.lora()
        elif comm_type == CommunicationType.WIFI:
            return CommunicationModule.wifi()
        return None

    def _select_sensor(self, sensor_type: str) -> Sensor | None:
        """Select appropriate sensor based on type."""
        sensor_map = {
            "temperature": Sensor(
                name="Temperature Sensor",
                sensor_category="environmental",
                measurement_type="temperature",
                measurement_range=(-40.0, 125.0),
                accuracy=0.5,
                interface="I2C",
            ),
            "humidity": Sensor(
                name="Humidity Sensor",
                sensor_category="environmental",
                measurement_type="humidity",
                measurement_range=(0.0, 100.0),
                accuracy=2.0,
                interface="I2C",
            ),
            "motion": Sensor(
                name="Motion Sensor",
                sensor_category="motion",
                measurement_type="acceleration",
                measurement_range=(-16.0, 16.0),
                accuracy=0.1,
                interface="I2C",
            ),
        }
        return sensor_map.get(sensor_type)

    def _select_power_module(self, requirements: DesignRequirements) -> PowerModule:
        """Select appropriate power module."""
        if requirements.power_source == "battery":
            return PowerModule(
                name="Battery Power Module",
                input_voltage_range=(3.0, 4.2),
                output_voltage=3.3,
                max_current_ma=500.0,
                efficiency_percent=90.0,
                protection_features=["overcurrent", "low_battery"],
            )
        return PowerModule(
            name="DC Power Module",
            input_voltage_range=(5.0, 12.0),
            output_voltage=3.3,
            max_current_ma=1000.0,
            efficiency_percent=85.0,
        )

    def get_suggestions(
        self, layout: PCBLayout, requirements: DesignRequirements
    ) -> list[DesignSuggestion]:
        """Get AI-powered suggestions for improving a design."""
        suggestions: list[DesignSuggestion] = []

        # Check for missing communication modules
        has_comm = any(c.component_type == "communication" for c in layout.components)
        if not has_comm and requirements.communication_types:
            suggestions.append(
                DesignSuggestion(
                    category="communication",
                    title="Add Communication Module",
                    description="Design lacks wireless communication capability",
                    component=CommunicationModule.wifi(),
                    confidence=0.9,
                    rationale="IoT devices typically require wireless connectivity",
                )
            )

        # Check for power redundancy
        power_modules = [c for c in layout.components if c.component_type == "power"]
        if len(power_modules) == 1:
            suggestions.append(
                DesignSuggestion(
                    category="power",
                    title="Add Backup Power",
                    description="Consider adding redundant power supply",
                    confidence=0.6,
                    rationale="Redundant power improves reliability",
                )
            )

        # Check component density
        if len(layout.components) > 0:
            area = layout.width_mm * layout.height_mm
            density = len(layout.components) / area * 1000  # per 1000 sq mm
            if density > 0.5:
                suggestions.append(
                    DesignSuggestion(
                        category="layout",
                        title="Reduce Component Density",
                        description="PCB is densely populated, consider larger board",
                        confidence=0.7,
                        rationale="High density can cause thermal and manufacturing issues",
                    )
                )

        return suggestions

    def brainstorm(self, prompt: str) -> list[DesignSuggestion]:
        """Brainstorm design ideas based on a natural language prompt."""
        suggestions: list[DesignSuggestion] = []

        # Parse common keywords and generate suggestions
        prompt_lower = prompt.lower()

        if "weather" in prompt_lower or "environmental" in prompt_lower:
            suggestions.append(
                DesignSuggestion(
                    category="sensor",
                    title="Environmental Monitoring",
                    description="Add temperature, humidity, and pressure sensors",
                    confidence=0.85,
                    rationale="Weather/environmental monitoring requires multiple sensors",
                )
            )

        if "remote" in prompt_lower or "long range" in prompt_lower:
            suggestions.append(
                DesignSuggestion(
                    category="communication",
                    title="LoRa Communication",
                    description="Use LoRa for long-range, low-power communication",
                    component=CommunicationModule.lora(),
                    confidence=0.9,
                    rationale="LoRa provides excellent range for remote applications",
                )
            )

        if "battery" in prompt_lower or "portable" in prompt_lower:
            suggestions.append(
                DesignSuggestion(
                    category="power",
                    title="Battery Power Management",
                    description="Include battery charging and power management",
                    confidence=0.85,
                    rationale="Portable devices need efficient power management",
                )
            )

        if "industrial" in prompt_lower or "rugged" in prompt_lower:
            suggestions.append(
                DesignSuggestion(
                    category="design",
                    title="Industrial-Grade Components",
                    description="Use components rated for industrial temperature range",
                    confidence=0.8,
                    rationale="Industrial environments require robust components",
                )
            )

        return suggestions
