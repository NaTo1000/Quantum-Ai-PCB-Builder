"""
Tests for the Design Validator module.
"""

import pytest
from src.core.nlp.intent_parser import IntentParser
from src.core.design.schematic_generator import (
    SchematicGenerator, Schematic, SchematicComponent, Net, Pin,
    PinType, NetType
)
from src.core.design.validator import (
    DesignValidator, ValidationResult, Violation,
    ViolationType, SeverityLevel
)


class TestDesignValidator:
    """Test suite for the DesignValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create a DesignValidator instance for testing."""
        return DesignValidator()
    
    @pytest.fixture
    def generator(self):
        """Create a SchematicGenerator instance for testing."""
        return SchematicGenerator()
    
    @pytest.fixture
    def parser(self):
        """Create an IntentParser instance for testing."""
        return IntentParser()
    
    def test_validate_returns_result(self, validator, generator, parser):
        """Test that validate returns a ValidationResult."""
        prompt = "ESP32 board with LED"
        design_intent = parser.parse(prompt)
        schematic = generator.generate(design_intent)
        
        result = validator.validate(schematic)
        
        assert isinstance(result, ValidationResult)
        assert isinstance(result.violations, list)
        assert isinstance(result.summary, dict)
    
    def test_valid_design_passes(self, validator, generator, parser):
        """Test that a valid design passes validation."""
        prompt = "ESP32 board with sensor"
        design_intent = parser.parse(prompt)
        schematic = generator.generate(design_intent)
        
        result = validator.validate(schematic)
        
        # May have warnings but no critical or error
        critical_count = result.summary.get("critical", 0)
        assert critical_count == 0
    
    def test_detects_missing_power_net(self, validator):
        """Test detection of missing power net."""
        # Create schematic without power net
        schematic = Schematic(
            schematic_id="test-001",
            name="Test",
            version="1.0",
            components=[
                SchematicComponent(
                    component_id="comp-001",
                    reference="U1",
                    component_type="microcontroller",
                    value=None,
                    footprint="QFN-48",
                    pins=[
                        Pin("pin-001", "VCC", PinType.POWER, 1),
                        Pin("pin-002", "GND", PinType.GROUND, 2),
                    ]
                )
            ],
            nets=[],  # No nets
            metadata={}
        )
        
        result = validator.validate(schematic)
        
        violation_types = [v.violation_type for v in result.violations]
        assert ViolationType.MISSING_POWER in violation_types
        assert ViolationType.MISSING_GROUND in violation_types
    
    def test_detects_duplicate_references(self, validator):
        """Test detection of duplicate reference designators."""
        schematic = Schematic(
            schematic_id="test-001",
            name="Test",
            version="1.0",
            components=[
                SchematicComponent(
                    component_id="comp-001",
                    reference="R1",  # Duplicate
                    component_type="resistor",
                    value="10k",
                    footprint="0805",
                    pins=[]
                ),
                SchematicComponent(
                    component_id="comp-002",
                    reference="R1",  # Duplicate
                    component_type="resistor",
                    value="20k",
                    footprint="0805",
                    pins=[]
                )
            ],
            nets=[
                Net("net-001", "VCC", NetType.POWER, []),
                Net("net-002", "GND", NetType.GROUND, [])
            ],
            metadata={}
        )
        
        result = validator.validate(schematic)
        
        violation_types = [v.violation_type for v in result.violations]
        assert ViolationType.REFERENCE_DUPLICATE in violation_types
    
    def test_detects_missing_component_value(self, validator):
        """Test detection of missing component values."""
        schematic = Schematic(
            schematic_id="test-001",
            name="Test",
            version="1.0",
            components=[
                SchematicComponent(
                    component_id="comp-001",
                    reference="R1",
                    component_type="resistor",
                    value=None,  # Missing value
                    footprint="0805",
                    pins=[]
                )
            ],
            nets=[
                Net("net-001", "VCC", NetType.POWER, []),
                Net("net-002", "GND", NetType.GROUND, [])
            ],
            metadata={}
        )
        
        result = validator.validate(schematic)
        
        violation_types = [v.violation_type for v in result.violations]
        assert ViolationType.MISSING_VALUE in violation_types
    
    def test_detects_single_pin_net(self, validator):
        """Test detection of single-pin nets."""
        schematic = Schematic(
            schematic_id="test-001",
            name="Test",
            version="1.0",
            components=[
                SchematicComponent(
                    component_id="comp-001",
                    reference="U1",
                    component_type="microcontroller",
                    value=None,
                    footprint="QFN-48",
                    pins=[
                        Pin("pin-001", "VCC", PinType.POWER, 1),
                    ]
                )
            ],
            nets=[
                Net("net-001", "VCC", NetType.POWER, [("comp-001", "pin-001")]),
                Net("net-002", "GND", NetType.GROUND, []),
                Net("net-003", "SIGNAL", NetType.SIGNAL, [("comp-001", "pin-001")])  # Single connection
            ],
            metadata={}
        )
        
        result = validator.validate(schematic)
        
        violation_types = [v.violation_type for v in result.violations]
        assert ViolationType.SINGLE_PIN_NET in violation_types
    
    def test_validation_result_to_dict(self, validator, generator, parser):
        """Test ValidationResult conversion to dictionary."""
        prompt = "ESP32 board"
        design_intent = parser.parse(prompt)
        schematic = generator.generate(design_intent)
        
        result = validator.validate(schematic)
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert "is_valid" in result_dict
        assert "violations" in result_dict
        assert "summary" in result_dict
    
    def test_summary_counts(self, validator, generator, parser):
        """Test that summary counts are correct."""
        prompt = "Simple LED"
        design_intent = parser.parse(prompt)
        schematic = generator.generate(design_intent)
        
        result = validator.validate(schematic)
        
        summary = result.summary
        assert "total" in summary
        assert "critical" in summary
        assert "errors" in summary
        assert "warnings" in summary
        assert "info" in summary
        
        total = (
            summary["critical"] + 
            summary["errors"] + 
            summary["warnings"] + 
            summary["info"]
        )
        assert summary["total"] == total


class TestViolation:
    """Test suite for Violation dataclass."""
    
    def test_violation_creation(self):
        """Test creating a Violation."""
        violation = Violation(
            violation_id="VIO-0001",
            violation_type=ViolationType.MISSING_VALUE,
            severity=SeverityLevel.WARNING,
            message="Component R1 missing value",
            component_id="comp-001"
        )
        
        assert violation.violation_type == ViolationType.MISSING_VALUE
        assert violation.severity == SeverityLevel.WARNING
        assert "R1" in violation.message
    
    def test_violation_to_dict(self):
        """Test Violation conversion to dictionary."""
        violation = Violation(
            violation_id="VIO-0001",
            violation_type=ViolationType.FLOATING_PIN,
            severity=SeverityLevel.ERROR,
            message="Floating pin detected",
            suggestion="Connect the pin"
        )
        
        result = violation.to_dict()
        
        assert isinstance(result, dict)
        assert result["type"] == "floating_pin"
        assert result["severity"] == "error"
        assert result["suggestion"] == "Connect the pin"
