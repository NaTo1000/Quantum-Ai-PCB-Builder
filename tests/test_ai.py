"""Tests for AI module."""

from quantum_pcb_builder.ai.designer import (
    AIDesigner,
    ApplicationDomain,
    CommunicationType,
    DesignRequirements,
    DesignSuggestion,
)
from quantum_pcb_builder.ai.optimizer import (
    LayoutOptimizer,
    OptimizationGoal,
)
from quantum_pcb_builder.pcb.components import Microcontroller
from quantum_pcb_builder.pcb.layout import PCBLayout, Position


class TestDesignRequirements:
    """Tests for DesignRequirements."""

    def test_create_requirements(self) -> None:
        """Test creating design requirements."""
        req = DesignRequirements(
            name="IoT Sensor",
            description="Weather monitoring device",
            domain=ApplicationDomain.IOT,
            communication_types=[CommunicationType.LORA],
            sensor_types=["temperature", "humidity"],
        )
        assert req.name == "IoT Sensor"
        assert req.domain == ApplicationDomain.IOT
        assert CommunicationType.LORA in req.communication_types

    def test_serialize_requirements(self) -> None:
        """Test serializing requirements."""
        req = DesignRequirements(
            name="Test",
            domain=ApplicationDomain.INDUSTRIAL,
        )
        data = req.to_dict()
        assert data["name"] == "Test"
        assert data["domain"] == "industrial"


class TestAIDesigner:
    """Tests for AIDesigner."""

    def test_generate_design(self) -> None:
        """Test generating a design from requirements."""
        designer = AIDesigner()
        req = DesignRequirements(
            name="Test Device",
            domain=ApplicationDomain.IOT,
            communication_types=[CommunicationType.WIFI],
            sensor_types=["temperature"],
        )

        layout = designer.generate_design(req)

        assert layout.name == "Test Device"
        assert len(layout.components) > 0

        # Should have MCU
        mcu_found = any(c.component_type == "microcontroller" for c in layout.components)
        assert mcu_found

        # Should have communication module
        comm_found = any(c.component_type == "communication" for c in layout.components)
        assert comm_found

    def test_generate_design_with_lora(self) -> None:
        """Test generating a design with LoRa."""
        designer = AIDesigner()
        req = DesignRequirements(
            name="LoRa Device",
            communication_types=[CommunicationType.LORA],
        )

        layout = designer.generate_design(req)
        connections = layout.get_connections()
        assert len(connections) > 0

    def test_get_suggestions(self) -> None:
        """Test getting design suggestions."""
        designer = AIDesigner()
        layout = PCBLayout(name="Test", width_mm=100.0, height_mm=100.0)
        layout.place_component(Microcontroller.esp32(), Position(x=50.0, y=50.0))

        req = DesignRequirements(
            name="Test",
            communication_types=[CommunicationType.WIFI],
        )

        suggestions = designer.get_suggestions(layout, req)
        assert len(suggestions) > 0

        # Should suggest adding communication
        comm_suggestions = [s for s in suggestions if s.category == "communication"]
        assert len(comm_suggestions) > 0

    def test_brainstorm(self) -> None:
        """Test brainstorming ideas."""
        designer = AIDesigner()

        suggestions = designer.brainstorm("remote weather station with battery power")

        assert len(suggestions) > 0

        # Should have LoRa suggestion for "remote"
        categories = [s.category for s in suggestions]
        assert "communication" in categories or "power" in categories


class TestDesignSuggestion:
    """Tests for DesignSuggestion."""

    def test_create_suggestion(self) -> None:
        """Test creating a suggestion."""
        suggestion = DesignSuggestion(
            category="communication",
            title="Add WiFi",
            description="Add WiFi for connectivity",
            confidence=0.9,
        )
        assert suggestion.category == "communication"
        assert suggestion.confidence == 0.9

    def test_serialize_suggestion(self) -> None:
        """Test serializing a suggestion."""
        suggestion = DesignSuggestion(
            category="test",
            title="Test",
            confidence=0.5,
        )
        data = suggestion.to_dict()
        assert data["category"] == "test"
        assert data["confidence"] == 0.5


class TestLayoutOptimizer:
    """Tests for LayoutOptimizer."""

    def test_optimize_simple_layout(self) -> None:
        """Test optimizing a simple layout."""
        layout = PCBLayout(name="Test", width_mm=100.0, height_mm=100.0)

        mcu = Microcontroller.esp32()
        sensor = Microcontroller.esp32_s3()  # Just for testing

        layout.place_component(mcu, Position(x=10.0, y=10.0))
        layout.place_component(sensor, Position(x=90.0, y=90.0))
        layout.connect_components(mcu.component_id, sensor.component_id)

        optimizer = LayoutOptimizer()
        result = optimizer.optimize(
            layout,
            [OptimizationGoal.MINIMIZE_TRACE_LENGTH],
        )

        assert result.iterations > 0
        assert "total_trace_length" in result.metrics_before
        assert "total_trace_length" in result.metrics_after

    def test_optimize_spacing(self) -> None:
        """Test optimizing component spacing."""
        layout = PCBLayout(name="Test", width_mm=100.0, height_mm=100.0)

        mcu1 = Microcontroller.esp32()
        mcu2 = Microcontroller.esp32_s3()

        # Place very close together
        layout.place_component(mcu1, Position(x=50.0, y=50.0))
        layout.place_component(mcu2, Position(x=51.0, y=51.0))

        optimizer = LayoutOptimizer()
        result = optimizer.optimize(layout, [OptimizationGoal.MAXIMIZE_SPACING])

        assert result.iterations > 0

    def test_analyze_layout(self) -> None:
        """Test analyzing a layout."""
        layout = PCBLayout(name="Test", width_mm=100.0, height_mm=100.0)
        layout.place_component(Microcontroller.esp32(), Position(x=50.0, y=50.0))

        optimizer = LayoutOptimizer()
        analysis = optimizer.analyze(layout)

        assert "metrics" in analysis
        assert "recommendations" in analysis
        assert "component_count" in analysis["metrics"]
