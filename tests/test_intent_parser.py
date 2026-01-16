"""
Tests for the NLP Intent Parser module.
"""

import pytest
from src.core.nlp.intent_parser import (
    IntentParser, DesignIntent, ComponentSpec,
    BoardType, DesignComplexity
)


class TestIntentParser:
    """Test suite for the IntentParser class."""
    
    @pytest.fixture
    def parser(self):
        """Create an IntentParser instance for testing."""
        return IntentParser()
    
    def test_parse_esp32_prompt(self, parser):
        """Test parsing a prompt mentioning ESP32."""
        prompt = "I need an ESP32-based board with WiFi and a temperature sensor"
        result = parser.parse(prompt)
        
        assert isinstance(result, DesignIntent)
        assert result.board_type == BoardType.ESP32
        assert "wifi" in result.features
        assert "sensor" in [c.component_type for c in result.components]
    
    def test_parse_lora_prompt(self, parser):
        """Test parsing a prompt mentioning LoRa."""
        prompt = "Design a LoRa sensor node with battery power"
        result = parser.parse(prompt)
        
        assert result.board_type == BoardType.LORA
        assert "battery" in result.features
    
    def test_parse_arduino_prompt(self, parser):
        """Test parsing a prompt mentioning Arduino."""
        prompt = "Create an Arduino-compatible board with motor control"
        result = parser.parse(prompt)
        
        assert result.board_type == BoardType.ARDUINO
        assert "motor_control" in result.features
    
    def test_parse_generic_prompt(self, parser):
        """Test parsing a generic prompt without specific board type."""
        prompt = "I want a simple LED controller with USB"
        result = parser.parse(prompt)
        
        assert result.board_type == BoardType.GENERIC
        assert "usb" in result.features
        assert "led" in [c.component_type for c in result.components]
    
    def test_extract_components(self, parser):
        """Test component extraction from prompt."""
        prompt = "Need a 10k resistor, 100nF capacitor, and an LED indicator"
        result = parser.parse(prompt)
        
        component_types = [c.component_type for c in result.components]
        assert "resistor" in component_types
        assert "capacitor" in component_types
        assert "led" in component_types
    
    def test_extract_connectivity(self, parser):
        """Test connectivity extraction from prompt."""
        prompt = "Board with I2C sensors and SPI display, UART debugging"
        result = parser.parse(prompt)
        
        assert "i2c" in result.connectivity
        assert "spi" in result.connectivity
        assert "uart" in result.connectivity
    
    def test_extract_size_constraints(self, parser):
        """Test size constraint extraction."""
        prompt = "PCB should be 50x30mm"
        result = parser.parse(prompt)
        
        assert "size" in result.constraints
        assert result.constraints["size"]["width"] == 50
        assert result.constraints["size"]["height"] == 30
    
    def test_extract_layer_constraints(self, parser):
        """Test layer constraint extraction."""
        prompt = "Need a 4 layer board for better signal integrity"
        result = parser.parse(prompt)
        
        assert "layers" in result.constraints
        assert result.constraints["layers"] == 4
    
    def test_extract_power_requirements(self, parser):
        """Test power requirement extraction."""
        prompt = "Operating at 3.3V with 100mA current draw"
        result = parser.parse(prompt)
        
        assert "voltage" in result.power_requirements
        assert result.power_requirements["voltage"] == 3.3
    
    def test_complexity_simple(self, parser):
        """Test complexity determination for simple designs."""
        prompt = "Simple LED with resistor"
        result = parser.parse(prompt)
        
        assert result.complexity == DesignComplexity.SIMPLE
    
    def test_complexity_complex(self, parser):
        """Test complexity determination for complex designs."""
        prompt = (
            "ESP32 with WiFi, Bluetooth, battery charging, GPS, display, "
            "motor control, and multiple sensors using I2C and SPI"
        )
        result = parser.parse(prompt)
        
        # Should be complex or advanced due to many features
        assert result.complexity in [DesignComplexity.COMPLEX, DesignComplexity.ADVANCED]
    
    def test_to_dict(self, parser):
        """Test conversion to dictionary."""
        prompt = "ESP32 board with WiFi"
        result = parser.parse(prompt)
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert "board_type" in result_dict
        assert "components" in result_dict
        assert "features" in result_dict
        assert result_dict["board_type"] == "esp32"
    
    def test_raw_prompt_preserved(self, parser):
        """Test that raw prompt is preserved in result."""
        prompt = "My custom design prompt"
        result = parser.parse(prompt)
        
        assert result.raw_prompt == prompt


class TestComponentSpec:
    """Test suite for the ComponentSpec dataclass."""
    
    def test_component_spec_creation(self):
        """Test creating a ComponentSpec."""
        spec = ComponentSpec(
            name="R1",
            component_type="resistor",
            value="10k",
            package="0805",
            quantity=1
        )
        
        assert spec.name == "R1"
        assert spec.component_type == "resistor"
        assert spec.value == "10k"
        assert spec.quantity == 1
    
    def test_component_spec_defaults(self):
        """Test ComponentSpec default values."""
        spec = ComponentSpec(
            name="C1",
            component_type="capacitor"
        )
        
        assert spec.value is None
        assert spec.package is None
        assert spec.quantity == 1
        assert spec.properties == {}
