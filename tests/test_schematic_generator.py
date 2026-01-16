"""
Tests for the Schematic Generator module.
"""

import pytest
from src.core.nlp.intent_parser import IntentParser, BoardType, ComponentSpec
from src.core.design.schematic_generator import (
    SchematicGenerator, Schematic, SchematicComponent, Net, Pin,
    PinType, NetType
)


class TestSchematicGenerator:
    """Test suite for the SchematicGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create a SchematicGenerator instance for testing."""
        return SchematicGenerator()
    
    @pytest.fixture
    def parser(self):
        """Create an IntentParser instance for testing."""
        return IntentParser()
    
    def test_generate_from_intent(self, generator, parser):
        """Test generating schematic from design intent."""
        prompt = "ESP32 board with LED and temperature sensor"
        design_intent = parser.parse(prompt)
        
        schematic = generator.generate(design_intent)
        
        assert isinstance(schematic, Schematic)
        assert schematic.schematic_id is not None
        assert len(schematic.components) > 0
    
    def test_generates_board_component(self, generator, parser):
        """Test that board type generates main MCU component."""
        prompt = "ESP32 based design"
        design_intent = parser.parse(prompt)
        
        schematic = generator.generate(design_intent)
        
        # Should have a microcontroller component
        mcu_components = [
            c for c in schematic.components 
            if c.component_type == "microcontroller"
        ]
        assert len(mcu_components) > 0
    
    def test_generates_specified_components(self, generator, parser):
        """Test that specified components are included."""
        prompt = "Design with resistor, capacitor, and LED"
        design_intent = parser.parse(prompt)
        
        schematic = generator.generate(design_intent)
        
        component_types = [c.component_type for c in schematic.components]
        assert "resistor" in component_types
        assert "capacitor" in component_types
        assert "led" in component_types
    
    def test_generates_power_nets(self, generator, parser):
        """Test that power and ground nets are generated."""
        prompt = "ESP32 board with sensors"
        design_intent = parser.parse(prompt)
        
        schematic = generator.generate(design_intent)
        
        net_types = [n.net_type for n in schematic.nets]
        assert NetType.POWER in net_types
        assert NetType.GROUND in net_types
    
    def test_components_have_pins(self, generator, parser):
        """Test that components have pins defined."""
        prompt = "Simple LED circuit"
        design_intent = parser.parse(prompt)
        
        schematic = generator.generate(design_intent)
        
        for component in schematic.components:
            assert isinstance(component.pins, list)
    
    def test_reference_designators_unique(self, generator, parser):
        """Test that reference designators are unique."""
        prompt = "Board with multiple resistors and capacitors"
        design_intent = parser.parse(prompt)
        
        schematic = generator.generate(design_intent)
        
        references = [c.reference for c in schematic.components]
        assert len(references) == len(set(references))
    
    def test_schematic_to_dict(self, generator, parser):
        """Test schematic conversion to dictionary."""
        prompt = "ESP32 WiFi board"
        design_intent = parser.parse(prompt)
        
        schematic = generator.generate(design_intent)
        result = schematic.to_dict()
        
        assert isinstance(result, dict)
        assert "schematic_id" in result
        assert "name" in result
        assert "components" in result
        assert "nets" in result
        assert "metadata" in result
    
    def test_feature_components_added(self, generator, parser):
        """Test that feature-specific components are added."""
        prompt = "ESP32 with USB and battery power"
        design_intent = parser.parse(prompt)
        
        schematic = generator.generate(design_intent)
        
        # Should have bypass capacitor for features
        cap_components = [
            c for c in schematic.components 
            if c.component_type == "capacitor"
        ]
        assert len(cap_components) > 0
    
    def test_usb_adds_esd_protection(self, generator, parser):
        """Test that USB feature adds ESD protection."""
        prompt = "Board with USB connectivity"
        design_intent = parser.parse(prompt)
        
        schematic = generator.generate(design_intent)
        
        esd_components = [
            c for c in schematic.components 
            if c.component_type == "esd_protection"
        ]
        assert len(esd_components) > 0
    
    def test_battery_adds_charger(self, generator, parser):
        """Test that battery feature adds charging circuit."""
        prompt = "Battery powered device"
        design_intent = parser.parse(prompt)
        
        schematic = generator.generate(design_intent)
        
        charger_components = [
            c for c in schematic.components 
            if c.component_type == "battery_charger"
        ]
        assert len(charger_components) > 0


class TestSchematicComponent:
    """Test suite for SchematicComponent dataclass."""
    
    def test_component_creation(self):
        """Test creating a SchematicComponent."""
        component = SchematicComponent(
            component_id="comp-001",
            reference="R1",
            component_type="resistor",
            value="10k",
            footprint="0805",
            pins=[]
        )
        
        assert component.reference == "R1"
        assert component.component_type == "resistor"
        assert component.value == "10k"
    
    def test_component_defaults(self):
        """Test SchematicComponent default values."""
        component = SchematicComponent(
            component_id="comp-001",
            reference="U1",
            component_type="microcontroller",
            value=None,
            footprint="QFN-48",
            pins=[]
        )
        
        assert component.position == (0.0, 0.0)
        assert component.rotation == 0.0
        assert component.properties == {}


class TestPin:
    """Test suite for Pin dataclass."""
    
    def test_pin_creation(self):
        """Test creating a Pin."""
        pin = Pin(
            pin_id="pin-001",
            name="VCC",
            pin_type=PinType.POWER,
            number=1
        )
        
        assert pin.name == "VCC"
        assert pin.pin_type == PinType.POWER
        assert pin.number == 1
    
    def test_pin_default_position(self):
        """Test Pin default position."""
        pin = Pin(
            pin_id="pin-001",
            name="GND",
            pin_type=PinType.GROUND,
            number=2
        )
        
        assert pin.position == (0.0, 0.0)


class TestNet:
    """Test suite for Net dataclass."""
    
    def test_net_creation(self):
        """Test creating a Net."""
        net = Net(
            net_id="net-001",
            name="VCC_3V3",
            net_type=NetType.POWER,
            connections=[("comp-001", "pin-001")]
        )
        
        assert net.name == "VCC_3V3"
        assert net.net_type == NetType.POWER
        assert len(net.connections) == 1
