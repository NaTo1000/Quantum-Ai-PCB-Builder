"""Tests for core component functionality."""

import pytest

from quantum_pcb_builder.core.component import (
    COMMON_COMPONENTS,
    Component,
    ComponentType,
    Footprint,
    Pin,
    create_component_from_template,
)


class TestFootprint:
    """Tests for Footprint class."""

    def test_footprint_creation(self) -> None:
        """Test basic footprint creation."""
        fp = Footprint(
            name="QFP-48",
            width_mm=10.0,
            height_mm=10.0,
            pin_count=48,
            smd=True,
            thermal_pad=True,
        )
        assert fp.name == "QFP-48"
        assert fp.width_mm == 10.0
        assert fp.height_mm == 10.0
        assert fp.pin_count == 48
        assert fp.smd is True
        assert fp.thermal_pad is True

    def test_footprint_defaults(self) -> None:
        """Test footprint default values."""
        fp = Footprint("0805", 2.0, 1.25, 2)
        assert fp.smd is True
        assert fp.thermal_pad is False


class TestPin:
    """Tests for Pin class."""

    def test_pin_creation(self) -> None:
        """Test pin creation."""
        pin = Pin(name="VCC", number=1, pin_type="power", voltage=3.3)
        assert pin.name == "VCC"
        assert pin.number == 1
        assert pin.pin_type == "power"
        assert pin.voltage == 3.3
        assert pin.connected_to is None

    def test_pin_defaults(self) -> None:
        """Test pin default values."""
        pin = Pin(name="GPIO", number=5)
        assert pin.pin_type == "io"
        assert pin.voltage == 3.3


class TestComponent:
    """Tests for Component class."""

    def test_component_creation(self) -> None:
        """Test basic component creation."""
        comp = Component(
            name="U1",
            component_type=ComponentType.MICROCONTROLLER,
            value="ESP32",
            package="QFN-48",
        )
        assert comp.name == "U1"
        assert comp.component_type == ComponentType.MICROCONTROLLER
        assert comp.value == "ESP32"
        assert comp.package == "QFN-48"
        assert comp.position == (0.0, 0.0)
        assert comp.rotation == 0.0
        assert comp.layer == "top"

    def test_component_uuid_generated(self) -> None:
        """Test that UUID is automatically generated."""
        comp1 = Component(name="R1", component_type=ComponentType.RESISTOR)
        comp2 = Component(name="R2", component_type=ComponentType.RESISTOR)
        assert comp1.uuid != comp2.uuid
        assert len(comp1.uuid) == 36

    def test_get_bounding_box_no_footprint(self) -> None:
        """Test bounding box without footprint."""
        comp = Component(name="R1", component_type=ComponentType.RESISTOR)
        comp.position = (10.0, 20.0)
        bbox = comp.get_bounding_box()
        assert bbox == (10.0, 20.0, 10.0, 20.0)

    def test_get_bounding_box_with_footprint(self) -> None:
        """Test bounding box with footprint."""
        comp = Component(
            name="U1",
            component_type=ComponentType.IC,
            footprint=Footprint("SOT-23", 4.0, 2.0, 3),
        )
        comp.position = (10.0, 10.0)
        bbox = comp.get_bounding_box()
        assert bbox == (8.0, 9.0, 12.0, 11.0)

    def test_get_area(self) -> None:
        """Test area calculation."""
        comp = Component(
            name="U1",
            component_type=ComponentType.IC,
            footprint=Footprint("QFP", 10.0, 10.0, 44),
        )
        assert comp.get_area() == 100.0

    def test_get_area_no_footprint(self) -> None:
        """Test area calculation without footprint."""
        comp = Component(name="R1", component_type=ComponentType.RESISTOR)
        assert comp.get_area() == 0.0

    def test_distance_to(self) -> None:
        """Test distance calculation between components."""
        comp1 = Component(name="U1", component_type=ComponentType.IC)
        comp1.position = (0.0, 0.0)

        comp2 = Component(name="U2", component_type=ComponentType.IC)
        comp2.position = (3.0, 4.0)

        assert comp1.distance_to(comp2) == 5.0

    def test_overlaps_true(self) -> None:
        """Test overlap detection - overlapping components."""
        fp = Footprint("TEST", 10.0, 10.0, 4)
        comp1 = Component(name="U1", component_type=ComponentType.IC, footprint=fp)
        comp1.position = (10.0, 10.0)

        comp2 = Component(name="U2", component_type=ComponentType.IC, footprint=fp)
        comp2.position = (15.0, 15.0)

        assert comp1.overlaps(comp2) is True

    def test_overlaps_false(self) -> None:
        """Test overlap detection - non-overlapping components."""
        fp = Footprint("TEST", 10.0, 10.0, 4)
        comp1 = Component(name="U1", component_type=ComponentType.IC, footprint=fp)
        comp1.position = (10.0, 10.0)

        comp2 = Component(name="U2", component_type=ComponentType.IC, footprint=fp)
        comp2.position = (30.0, 30.0)

        assert comp1.overlaps(comp2) is False


class TestComponentTemplates:
    """Tests for component templates."""

    def test_common_components_exist(self) -> None:
        """Test that common components are defined."""
        assert "ESP32-WROOM-32" in COMMON_COMPONENTS
        assert "SX1276" in COMMON_COMPONENTS
        assert "AMS1117-3.3" in COMMON_COMPONENTS

    def test_create_from_template(self) -> None:
        """Test creating component from template."""
        comp = create_component_from_template("ESP32-WROOM-32", "U1")
        assert comp.name == "U1"
        assert comp.component_type == ComponentType.MICROCONTROLLER
        assert comp.footprint is not None
        assert comp.footprint.width_mm == 18.0
        assert comp.properties.get("wifi") is True

    def test_create_from_invalid_template(self) -> None:
        """Test error on invalid template name."""
        with pytest.raises(ValueError, match="Unknown component template"):
            create_component_from_template("INVALID_TEMPLATE", "U1")


class TestComponentType:
    """Tests for ComponentType enum."""

    def test_all_types_defined(self) -> None:
        """Test that all expected component types exist."""
        expected_types = [
            "MICROCONTROLLER",
            "RESISTOR",
            "CAPACITOR",
            "INDUCTOR",
            "TRANSISTOR",
            "DIODE",
            "LED",
            "SENSOR",
            "CONNECTOR",
            "VOLTAGE_REGULATOR",
            "RF_MODULE",
            "ANTENNA",
        ]
        for type_name in expected_types:
            assert hasattr(ComponentType, type_name)
