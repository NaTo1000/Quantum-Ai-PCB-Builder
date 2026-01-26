"""Tests for PCB module."""

from quantum_pcb_builder.pcb.components import (
    CommunicationModule,
    ComponentLibrary,
    Microcontroller,
    PowerModule,
    Sensor,
)
from quantum_pcb_builder.pcb.layout import (
    Connection,
    LayerType,
    PCBLayout,
    Position,
)
from quantum_pcb_builder.pcb.validators import (
    ComponentCompatibilityChecker,
    DesignValidator,
)


class TestMicrocontroller:
    """Tests for Microcontroller component."""

    def test_create_esp32(self) -> None:
        """Test creating an ESP32."""
        mcu = Microcontroller.esp32()
        assert mcu.name == "ESP32"
        assert mcu.component_type == "microcontroller"
        assert mcu.clock_speed_mhz == 240
        assert mcu.gpio_count == 34

    def test_create_esp32_s3(self) -> None:
        """Test creating an ESP32-S3."""
        mcu = Microcontroller.esp32_s3()
        assert mcu.name == "ESP32-S3"
        assert mcu.flash_size_mb == 8
        assert mcu.gpio_count == 45

    def test_validate_mcu(self) -> None:
        """Test MCU validation."""
        valid_mcu = Microcontroller.esp32()
        assert valid_mcu.validate()

        invalid_mcu = Microcontroller(
            name="Bad MCU",
            clock_speed_mhz=0,  # Invalid
        )
        assert not invalid_mcu.validate()

    def test_mcu_specifications(self) -> None:
        """Test that specifications are properly built."""
        mcu = Microcontroller.esp32()
        specs = mcu.specifications
        assert specs["clock_speed_mhz"] == 240
        assert specs["architecture"] == "xtensa"


class TestSensor:
    """Tests for Sensor component."""

    def test_create_sensor(self) -> None:
        """Test creating a sensor."""
        sensor = Sensor(
            name="DHT22",
            sensor_category="environmental",
            measurement_type="temperature",
            measurement_range=(-40.0, 80.0),
            accuracy=0.5,
        )
        assert sensor.name == "DHT22"
        assert sensor.component_type == "sensor"
        assert sensor.measurement_range == (-40.0, 80.0)

    def test_validate_sensor(self) -> None:
        """Test sensor validation."""
        valid_sensor = Sensor(
            name="Test",
            measurement_range=(0.0, 100.0),
            accuracy=0.1,
        )
        assert valid_sensor.validate()

        # Invalid range
        invalid_sensor = Sensor(
            name="Test",
            measurement_range=(100.0, 0.0),  # Invalid: min > max
            accuracy=0.1,
        )
        assert not invalid_sensor.validate()


class TestCommunicationModule:
    """Tests for CommunicationModule component."""

    def test_create_lora(self) -> None:
        """Test creating a LoRa module."""
        lora = CommunicationModule.lora()
        assert lora.protocol == "LoRa"
        assert lora.frequency_mhz == 868.0
        assert lora.range_meters == 10000

    def test_create_wifi(self) -> None:
        """Test creating a WiFi module."""
        wifi = CommunicationModule.wifi()
        assert wifi.protocol == "WiFi"
        assert wifi.frequency_mhz == 2400.0


class TestPowerModule:
    """Tests for PowerModule component."""

    def test_create_power_module(self) -> None:
        """Test creating a power module."""
        power = PowerModule(
            name="AMS1117",
            input_voltage_range=(4.5, 12.0),
            output_voltage=3.3,
            max_current_ma=1000.0,
        )
        assert power.name == "AMS1117"
        assert power.output_voltage == 3.3

    def test_validate_power_module(self) -> None:
        """Test power module validation."""
        valid_power = PowerModule(
            name="Test",
            input_voltage_range=(5.0, 12.0),
            output_voltage=3.3,
            max_current_ma=500.0,
            efficiency_percent=85.0,
        )
        assert valid_power.validate()

        # Invalid efficiency
        invalid_power = PowerModule(
            name="Test",
            input_voltage_range=(5.0, 12.0),
            output_voltage=3.3,
            max_current_ma=500.0,
            efficiency_percent=150.0,  # Invalid
        )
        assert not invalid_power.validate()


class TestComponentLibrary:
    """Tests for ComponentLibrary."""

    def test_default_components(self) -> None:
        """Test that default components are loaded."""
        library = ComponentLibrary()
        components = library.list_components()
        assert "esp32" in components
        assert "lora" in components
        assert "dht22" in components

    def test_get_component(self) -> None:
        """Test getting a component from library."""
        library = ComponentLibrary()
        esp32 = library.get("esp32")
        assert esp32 is not None
        assert esp32.name == "ESP32"

    def test_get_by_type(self) -> None:
        """Test getting components by type."""
        library = ComponentLibrary()
        mcus = library.get_by_type("microcontroller")
        assert len(mcus) >= 2  # ESP32 and ESP32-S3

    def test_clone_component(self) -> None:
        """Test cloning a component."""
        library = ComponentLibrary()
        original = library.get("esp32")
        cloned = library.clone("esp32")

        assert cloned is not None
        assert original is not None
        assert cloned.component_id != original.component_id
        assert cloned.name == original.name


class TestPosition:
    """Tests for Position class."""

    def test_create_position(self) -> None:
        """Test creating a position."""
        pos = Position(x=10.0, y=20.0, rotation=45.0)
        assert pos.x == 10.0
        assert pos.y == 20.0
        assert pos.rotation == 45.0

    def test_distance_calculation(self) -> None:
        """Test distance calculation between positions."""
        pos1 = Position(x=0.0, y=0.0)
        pos2 = Position(x=3.0, y=4.0)
        distance = pos1.distance_to(pos2)
        assert distance == 5.0  # 3-4-5 triangle

    def test_serialization(self) -> None:
        """Test position serialization."""
        pos = Position(x=10.0, y=20.0, layer=LayerType.BOTTOM)
        data = pos.to_dict()
        restored = Position.from_dict(data)
        assert restored.x == pos.x
        assert restored.layer == LayerType.BOTTOM


class TestConnection:
    """Tests for Connection class."""

    def test_create_connection(self) -> None:
        """Test creating a connection."""
        conn = Connection(
            source_component_id="comp1",
            target_component_id="comp2",
            net_name="SPI",
        )
        assert conn.source_component_id == "comp1"
        assert conn.target_component_id == "comp2"
        assert conn.validate()

    def test_invalid_connection(self) -> None:
        """Test invalid connection."""
        conn = Connection()  # Missing required fields
        assert not conn.validate()


class TestPCBLayout:
    """Tests for PCBLayout class."""

    def test_create_layout(self) -> None:
        """Test creating a PCB layout."""
        layout = PCBLayout(
            name="Test PCB",
            width_mm=100.0,
            height_mm=80.0,
            layer_count=2,
        )
        assert layout.name == "Test PCB"
        assert layout.width_mm == 100.0
        assert layout.height_mm == 80.0

    def test_place_component(self) -> None:
        """Test placing a component on the layout."""
        layout = PCBLayout(name="Test", width_mm=100.0, height_mm=100.0)
        mcu = Microcontroller.esp32()
        pos = Position(x=50.0, y=50.0)

        result = layout.place_component(mcu, pos)
        assert result
        assert mcu in layout.components

        placed_pos = layout.get_placement(mcu.component_id)
        assert placed_pos is not None
        assert placed_pos.x == 50.0

    def test_place_out_of_bounds(self) -> None:
        """Test placing component out of bounds."""
        layout = PCBLayout(name="Test", width_mm=100.0, height_mm=100.0)
        mcu = Microcontroller.esp32()
        pos = Position(x=150.0, y=50.0)  # Out of bounds

        result = layout.place_component(mcu, pos)
        assert not result

    def test_connect_components(self) -> None:
        """Test connecting components."""
        layout = PCBLayout(name="Test", width_mm=100.0, height_mm=100.0)
        mcu = Microcontroller.esp32()
        sensor = Sensor(name="Temp", measurement_range=(0.0, 100.0), accuracy=0.1)

        layout.place_component(mcu, Position(x=50.0, y=50.0))
        layout.place_component(sensor, Position(x=20.0, y=20.0))

        conn = layout.connect_components(
            mcu.component_id,
            sensor.component_id,
            net_name="I2C",
        )
        assert conn is not None
        assert conn.net_name == "I2C"

        connections = layout.get_connections()
        assert len(connections) == 1

    def test_validate_layout(self) -> None:
        """Test layout validation."""
        layout = PCBLayout(name="Test", width_mm=100.0, height_mm=100.0)
        mcu = Microcontroller.esp32()
        layout.place_component(mcu, Position(x=50.0, y=50.0))

        is_valid, issues = layout.validate()
        assert is_valid
        assert len(issues) == 0


class TestDesignValidator:
    """Tests for DesignValidator."""

    def test_validate_valid_design(self) -> None:
        """Test validating a valid design."""
        layout = PCBLayout(name="Test", width_mm=100.0, height_mm=100.0)
        layout.place_component(Microcontroller.esp32(), Position(x=50.0, y=50.0))

        validator = DesignValidator()
        result = validator.validate(layout)
        assert result.is_valid

    def test_validate_empty_design(self) -> None:
        """Test validating an empty design."""
        layout = PCBLayout(name="Empty", width_mm=100.0, height_mm=100.0)

        validator = DesignValidator()
        result = validator.validate(layout)
        assert not result.is_valid


class TestComponentCompatibilityChecker:
    """Tests for ComponentCompatibilityChecker."""

    def test_check_compatible_pair(self) -> None:
        """Test checking compatible component pair."""
        checker = ComponentCompatibilityChecker()
        mcu = Microcontroller.esp32()
        sensor = Sensor(name="Temp", measurement_range=(0.0, 100.0), accuracy=0.1)

        result = checker.check_pair(mcu, sensor)
        assert result.is_valid
