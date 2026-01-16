"""
Natural Language Intent Parser

This module extracts design intent from natural language prompts
and converts them into structured design specifications.
"""

import re
from dataclasses import dataclass, field
from typing import Any
from enum import Enum


class BoardType(Enum):
    """Supported PCB/chip board types."""
    ESP32 = "esp32"
    LORA = "lora"
    ARDUINO = "arduino"
    RASPBERRY_PI = "raspberry_pi"
    CUSTOM = "custom"
    GENERIC = "generic"


class DesignComplexity(Enum):
    """Design complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ADVANCED = "advanced"


@dataclass
class ComponentSpec:
    """Specification for a single component."""
    name: str
    component_type: str
    value: str | None = None
    package: str | None = None
    quantity: int = 1
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class DesignIntent:
    """Extracted design intent from natural language."""
    board_type: BoardType
    components: list[ComponentSpec]
    features: list[str]
    constraints: dict[str, Any]
    complexity: DesignComplexity
    power_requirements: dict[str, Any]
    connectivity: list[str]
    raw_prompt: str

    def to_dict(self) -> dict[str, Any]:
        """Convert design intent to dictionary."""
        return {
            "board_type": self.board_type.value,
            "components": [
                {
                    "name": c.name,
                    "type": c.component_type,
                    "value": c.value,
                    "package": c.package,
                    "quantity": c.quantity,
                    "properties": c.properties
                }
                for c in self.components
            ],
            "features": self.features,
            "constraints": self.constraints,
            "complexity": self.complexity.value,
            "power_requirements": self.power_requirements,
            "connectivity": self.connectivity,
            "raw_prompt": self.raw_prompt
        }


class IntentParser:
    """
    Parses natural language prompts to extract PCB/chip design intent.
    
    This parser uses pattern matching and keyword extraction to understand
    user requirements and convert them into structured design specifications.
    """
    
    BOARD_PATTERNS = {
        BoardType.ESP32: [r'\besp32\b', r'\besp-32\b', r'\bespressif\b'],
        BoardType.LORA: [r'\blora\b', r'\blorawan\b', r'\blong.?range\b'],
        BoardType.ARDUINO: [r'\barduino\b', r'\bavr\b', r'\batmega\b'],
        BoardType.RASPBERRY_PI: [r'\braspberry\s*pi\b', r'\brpi\b', r'\bpi\s*zero\b'],
    }
    
    COMPONENT_PATTERNS = {
        "resistor": [r'\bresistor\b', r'\b(\d+)\s*[kKmM]?\s*[oO]hm\b', r'\bR\d+\b'],
        "capacitor": [r'\bcapacitor\b', r'\bcap\b', r'\b(\d+)\s*[pPnNuUmM]?[fF]\b'],
        "inductor": [r'\binductor\b', r'\bcoil\b', r'\b(\d+)\s*[uUnN]?[hH]\b'],
        "led": [r'\bled\b', r'\blight.?emitting\b', r'\bindicator\b'],
        "sensor": [r'\bsensor\b', r'\btemperature\b', r'\bhumidity\b', r'\bpressure\b'],
        "microcontroller": [r'\bmcu\b', r'\bmicrocontroller\b', r'\bprocessor\b'],
        "transistor": [r'\btransistor\b', r'\bmosfet\b', r'\bbjt\b', r'\bfet\b'],
        "regulator": [r'\bregulator\b', r'\bldo\b', r'\bvoltage\s*reg\b'],
        "crystal": [r'\bcrystal\b', r'\boscillator\b', r'\bxtal\b'],
        "connector": [r'\bconnector\b', r'\bheader\b', r'\bpin\s*header\b'],
    }
    
    FEATURE_PATTERNS = {
        "wifi": [r'\bwi-?fi\b', r'\bwireless\b', r'\b802\.11\b'],
        "bluetooth": [r'\bbluetooth\b', r'\bble\b', r'\bbt\b'],
        "usb": [r'\busb\b', r'\busb-c\b', r'\bmicro.?usb\b'],
        "battery": [r'\bbattery\b', r'\blipo\b', r'\brechargeable\b'],
        "solar": [r'\bsolar\b', r'\bphotovoltaic\b'],
        "display": [r'\bdisplay\b', r'\blcd\b', r'\boled\b', r'\bscreen\b'],
        "gps": [r'\bgps\b', r'\bgnss\b', r'\blocation\b'],
        "motor_control": [r'\bmotor\b', r'\bpwm\b', r'\bservo\b'],
        "audio": [r'\baudio\b', r'\bspeaker\b', r'\bmicrophone\b'],
        "ethernet": [r'\bethernet\b', r'\blan\b', r'\brj45\b'],
    }
    
    CONNECTIVITY_PATTERNS = {
        "i2c": [r'\bi2c\b', r'\biic\b', r'\btwo.?wire\b'],
        "spi": [r'\bspi\b', r'\bserial.?peripheral\b'],
        "uart": [r'\buart\b', r'\bserial\b', r'\btx.?rx\b'],
        "gpio": [r'\bgpio\b', r'\bdigital.?pin\b'],
        "adc": [r'\badc\b', r'\banalog\b'],
        "pwm": [r'\bpwm\b'],
        "can": [r'\bcan\b', r'\bcanbus\b'],
    }

    def __init__(self):
        """Initialize the intent parser."""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        self._board_compiled = {
            board: [re.compile(p, re.IGNORECASE) for p in patterns]
            for board, patterns in self.BOARD_PATTERNS.items()
        }
        self._component_compiled = {
            comp: [re.compile(p, re.IGNORECASE) for p in patterns]
            for comp, patterns in self.COMPONENT_PATTERNS.items()
        }
        self._feature_compiled = {
            feat: [re.compile(p, re.IGNORECASE) for p in patterns]
            for feat, patterns in self.FEATURE_PATTERNS.items()
        }
        self._connectivity_compiled = {
            conn: [re.compile(p, re.IGNORECASE) for p in patterns]
            for conn, patterns in self.CONNECTIVITY_PATTERNS.items()
        }

    def parse(self, prompt: str) -> DesignIntent:
        """
        Parse a natural language prompt into a structured design intent.
        
        Args:
            prompt: Natural language description of the desired design.
            
        Returns:
            DesignIntent object containing extracted specifications.
        """
        board_type = self._extract_board_type(prompt)
        components = self._extract_components(prompt)
        features = self._extract_features(prompt)
        connectivity = self._extract_connectivity(prompt)
        constraints = self._extract_constraints(prompt)
        power_req = self._extract_power_requirements(prompt)
        complexity = self._determine_complexity(components, features)
        
        return DesignIntent(
            board_type=board_type,
            components=components,
            features=features,
            constraints=constraints,
            complexity=complexity,
            power_requirements=power_req,
            connectivity=connectivity,
            raw_prompt=prompt
        )

    def _extract_board_type(self, prompt: str) -> BoardType:
        """Extract the target board type from the prompt."""
        for board_type, patterns in self._board_compiled.items():
            for pattern in patterns:
                if pattern.search(prompt):
                    return board_type
        return BoardType.GENERIC

    def _extract_components(self, prompt: str) -> list[ComponentSpec]:
        """Extract component specifications from the prompt."""
        components = []
        
        for comp_type, patterns in self._component_compiled.items():
            for pattern in patterns:
                matches = pattern.findall(prompt)
                if matches:
                    # Extract value if captured
                    value = matches[0] if isinstance(matches[0], str) and matches[0] else None
                    components.append(ComponentSpec(
                        name=f"{comp_type}_1",
                        component_type=comp_type,
                        value=value,
                        quantity=1
                    ))
                    break
        
        return components

    def _extract_features(self, prompt: str) -> list[str]:
        """Extract desired features from the prompt."""
        features = []
        
        for feature, patterns in self._feature_compiled.items():
            for pattern in patterns:
                if pattern.search(prompt):
                    features.append(feature)
                    break
        
        return features

    def _extract_connectivity(self, prompt: str) -> list[str]:
        """Extract connectivity requirements from the prompt."""
        connectivity = []
        
        for conn, patterns in self._connectivity_compiled.items():
            for pattern in patterns:
                if pattern.search(prompt):
                    connectivity.append(conn)
                    break
        
        return connectivity

    def _extract_constraints(self, prompt: str) -> dict[str, Any]:
        """Extract design constraints from the prompt."""
        constraints: dict[str, Any] = {}
        
        # Size constraints
        size_pattern = re.compile(r'(\d+)\s*[xX×]\s*(\d+)\s*(mm|cm|inch)?', re.IGNORECASE)
        size_match = size_pattern.search(prompt)
        if size_match:
            unit = size_match.group(3) or "mm"
            constraints["size"] = {
                "width": int(size_match.group(1)),
                "height": int(size_match.group(2)),
                "unit": unit.lower()
            }
        
        # Layer constraints
        layer_pattern = re.compile(r'(\d+)\s*layer', re.IGNORECASE)
        layer_match = layer_pattern.search(prompt)
        if layer_match:
            constraints["layers"] = int(layer_match.group(1))
        
        # Temperature constraints
        temp_pattern = re.compile(r'(-?\d+)\s*°?[cC]', re.IGNORECASE)
        temp_matches = temp_pattern.findall(prompt)
        if temp_matches:
            temps = [int(t) for t in temp_matches]
            constraints["temperature"] = {
                "min": min(temps),
                "max": max(temps)
            }
        
        return constraints

    def _extract_power_requirements(self, prompt: str) -> dict[str, Any]:
        """Extract power requirements from the prompt."""
        power: dict[str, Any] = {}
        
        # Voltage
        voltage_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*[vV](?:olt)?', re.IGNORECASE)
        voltage_match = voltage_pattern.search(prompt)
        if voltage_match:
            power["voltage"] = float(voltage_match.group(1))
        
        # Current
        current_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*([mμu])?[aA](?:mp)?', re.IGNORECASE)
        current_match = current_pattern.search(prompt)
        if current_match:
            value = float(current_match.group(1))
            prefix = current_match.group(2)
            if prefix and prefix.lower() in ['m', 'μ', 'u']:
                multiplier = {'m': 0.001, 'μ': 0.000001, 'u': 0.000001}.get(prefix.lower(), 1)
                value *= multiplier
            power["current"] = value
        
        # Power consumption
        power_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*([mμu])?[wW](?:att)?', re.IGNORECASE)
        power_match = power_pattern.search(prompt)
        if power_match:
            value = float(power_match.group(1))
            prefix = power_match.group(2)
            if prefix and prefix.lower() in ['m', 'μ', 'u']:
                multiplier = {'m': 0.001, 'μ': 0.000001, 'u': 0.000001}.get(prefix.lower(), 1)
                value *= multiplier
            power["wattage"] = value
        
        return power

    def _determine_complexity(
        self,
        components: list[ComponentSpec],
        features: list[str]
    ) -> DesignComplexity:
        """Determine the complexity level of the design."""
        score = len(components) + len(features) * 2
        
        if score <= 3:
            return DesignComplexity.SIMPLE
        elif score <= 7:
            return DesignComplexity.MODERATE
        elif score <= 12:
            return DesignComplexity.COMPLEX
        else:
            return DesignComplexity.ADVANCED
