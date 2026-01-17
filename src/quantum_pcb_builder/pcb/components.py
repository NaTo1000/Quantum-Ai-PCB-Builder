"""PCB component definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from quantum_pcb_builder.core.base import BaseComponent


class PinType(Enum):
    """Types of component pins."""

    INPUT = "input"
    OUTPUT = "output"
    BIDIRECTIONAL = "bidirectional"
    POWER = "power"
    GROUND = "ground"
    ANALOG = "analog"
    DIGITAL = "digital"


@dataclass
class Pin:
    """Represents a pin on a component."""

    name: str
    pin_number: int
    pin_type: PinType
    voltage: float = 3.3
    description: str = ""


@dataclass
class Microcontroller(BaseComponent):
    """Microcontroller component (ESP32, Arduino, etc.)."""

    component_type: str = "microcontroller"
    architecture: str = "xtensa"
    clock_speed_mhz: int = 240
    flash_size_mb: int = 4
    ram_size_kb: int = 520
    gpio_count: int = 34
    pins: list[Pin] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Set specifications after initialization."""
        if not self.specifications:
            self.specifications = self._build_specifications()

    def _build_specifications(self) -> dict[str, Any]:
        """Build specifications dictionary."""
        return {
            "architecture": self.architecture,
            "clock_speed_mhz": self.clock_speed_mhz,
            "flash_size_mb": self.flash_size_mb,
            "ram_size_kb": self.ram_size_kb,
            "gpio_count": self.gpio_count,
        }

    def validate(self) -> bool:
        """Validate microcontroller configuration."""
        if not super().validate():
            return False
        if self.clock_speed_mhz <= 0:
            return False
        if self.flash_size_mb <= 0:
            return False
        return not self.gpio_count <= 0

    @classmethod
    def esp32(cls, name: str = "ESP32") -> Microcontroller:
        """Create an ESP32 microcontroller."""
        return cls(
            name=name,
            architecture="xtensa",
            clock_speed_mhz=240,
            flash_size_mb=4,
            ram_size_kb=520,
            gpio_count=34,
        )

    @classmethod
    def esp32_s3(cls, name: str = "ESP32-S3") -> Microcontroller:
        """Create an ESP32-S3 microcontroller."""
        return cls(
            name=name,
            architecture="xtensa",
            clock_speed_mhz=240,
            flash_size_mb=8,
            ram_size_kb=512,
            gpio_count=45,
        )


@dataclass
class Sensor(BaseComponent):
    """Sensor component (temperature, humidity, motion, etc.)."""

    component_type: str = "sensor"
    sensor_category: str = "environmental"
    measurement_type: str = "temperature"
    measurement_range: tuple[float, float] = (0.0, 100.0)
    accuracy: float = 0.1
    interface: str = "I2C"
    power_voltage: float = 3.3

    def __post_init__(self) -> None:
        """Set specifications after initialization."""
        if not self.specifications:
            self.specifications = self._build_specifications()

    def _build_specifications(self) -> dict[str, Any]:
        """Build specifications dictionary."""
        return {
            "sensor_category": self.sensor_category,
            "measurement_type": self.measurement_type,
            "measurement_range": list(self.measurement_range),
            "accuracy": self.accuracy,
            "interface": self.interface,
            "power_voltage": self.power_voltage,
        }

    def validate(self) -> bool:
        """Validate sensor configuration."""
        if not super().validate():
            return False
        if self.measurement_range[0] >= self.measurement_range[1]:
            return False
        return not self.accuracy <= 0


@dataclass
class CommunicationModule(BaseComponent):
    """Communication module (LoRa, WiFi, Bluetooth, etc.)."""

    component_type: str = "communication"
    protocol: str = "WiFi"
    frequency_mhz: float = 2400.0
    range_meters: int = 100
    data_rate_kbps: float = 1000.0
    power_consumption_mw: float = 100.0

    def __post_init__(self) -> None:
        """Set specifications after initialization."""
        if not self.specifications:
            self.specifications = self._build_specifications()
        if not self.specifications:
            self.specifications = self._build_specifications()

    def _build_specifications(self) -> dict[str, Any]:
        """Build specifications dictionary."""
        return {
            "protocol": self.protocol,
            "frequency_mhz": self.frequency_mhz,
            "range_meters": self.range_meters,
            "data_rate_kbps": self.data_rate_kbps,
            "power_consumption_mw": self.power_consumption_mw,
        }

    def validate(self) -> bool:
        """Validate communication module configuration."""
        if not super().validate():
            return False
        if self.frequency_mhz <= 0:
            return False
        return not self.range_meters <= 0

    @classmethod
    def lora(cls, name: str = "LoRa Module") -> CommunicationModule:
        """Create a LoRa communication module."""
        return cls(
            name=name,
            protocol="LoRa",
            frequency_mhz=868.0,
            range_meters=10000,
            data_rate_kbps=50.0,
            power_consumption_mw=50.0,
        )

    @classmethod
    def wifi(cls, name: str = "WiFi Module") -> CommunicationModule:
        """Create a WiFi communication module."""
        return cls(
            name=name,
            protocol="WiFi",
            frequency_mhz=2400.0,
            range_meters=100,
            data_rate_kbps=54000.0,
            power_consumption_mw=200.0,
        )


@dataclass
class PowerModule(BaseComponent):
    """Power management module."""

    component_type: str = "power"
    input_voltage_range: tuple[float, float] = (5.0, 12.0)
    output_voltage: float = 3.3
    max_current_ma: float = 500.0
    efficiency_percent: float = 85.0
    protection_features: list[str] = field(default_factory=lambda: ["overcurrent", "overvoltage"])

    def __post_init__(self) -> None:
        """Set specifications after initialization."""
        if not self.specifications:
            self.specifications = self._build_specifications()

    def _build_specifications(self) -> dict[str, Any]:
        """Build specifications dictionary."""
        return {
            "input_voltage_range": list(self.input_voltage_range),
            "output_voltage": self.output_voltage,
            "max_current_ma": self.max_current_ma,
            "efficiency_percent": self.efficiency_percent,
            "protection_features": self.protection_features,
        }

    def validate(self) -> bool:
        """Validate power module configuration."""
        if not super().validate():
            return False
        if self.input_voltage_range[0] >= self.input_voltage_range[1]:
            return False
        if self.output_voltage <= 0:
            return False
        if self.max_current_ma <= 0:
            return False
        return 0 < self.efficiency_percent <= 100


class ComponentLibrary:
    """Library of pre-defined components for quick design."""

    def __init__(self) -> None:
        """Initialize the component library."""
        self._components: dict[str, BaseComponent] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default components into the library."""
        # Microcontrollers
        self.add("esp32", Microcontroller.esp32())
        self.add("esp32_s3", Microcontroller.esp32_s3())

        # Communication modules
        self.add("lora", CommunicationModule.lora())
        self.add("wifi", CommunicationModule.wifi())

        # Sensors
        self.add(
            "dht22",
            Sensor(
                name="DHT22",
                sensor_category="environmental",
                measurement_type="temperature_humidity",
                measurement_range=(-40.0, 80.0),
                accuracy=0.5,
                interface="OneWire",
            ),
        )

        # Power modules
        self.add(
            "ams1117",
            PowerModule(
                name="AMS1117-3.3",
                input_voltage_range=(4.5, 12.0),
                output_voltage=3.3,
                max_current_ma=1000.0,
                efficiency_percent=75.0,
            ),
        )

    def add(self, key: str, component: BaseComponent) -> None:
        """Add a component to the library."""
        self._components[key] = component

    def get(self, key: str) -> BaseComponent | None:
        """Get a component from the library."""
        return self._components.get(key)

    def list_components(self) -> list[str]:
        """List all component keys in the library."""
        return list(self._components.keys())

    def get_by_type(self, component_type: str) -> list[BaseComponent]:
        """Get all components of a specific type."""
        return [c for c in self._components.values() if c.component_type == component_type]

    def clone(self, key: str) -> BaseComponent | None:
        """Clone a component from the library with a new ID."""
        original = self.get(key)
        if original is None:
            return None
        return BaseComponent.from_dict({**original.to_dict(), "component_id": str(uuid4())})
