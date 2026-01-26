"""Tests for core module."""

from quantum_pcb_builder.core.base import (
    BaseComponent,
    BaseDesign,
    ValidationResult,
)
from quantum_pcb_builder.core.events import Event, EventBus


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_valid_result(self) -> None:
        """Test creating a valid result."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_add_error(self) -> None:
        """Test adding an error."""
        result = ValidationResult(is_valid=True)
        result.add_error("Test error")
        assert not result.is_valid
        assert "Test error" in result.errors

    def test_add_warning(self) -> None:
        """Test adding a warning."""
        result = ValidationResult(is_valid=True)
        result.add_warning("Test warning")
        assert result.is_valid  # Warnings don't affect validity
        assert "Test warning" in result.warnings

    def test_merge_results(self) -> None:
        """Test merging validation results."""
        result1 = ValidationResult(is_valid=True, warnings=["warn1"])
        result2 = ValidationResult(is_valid=False, errors=["error1"])

        merged = result1.merge(result2)
        assert not merged.is_valid
        assert "warn1" in merged.warnings
        assert "error1" in merged.errors


class TestBaseComponent:
    """Tests for BaseComponent class."""

    def test_create_component(self) -> None:
        """Test creating a basic component."""
        comp = BaseComponent(name="Test", component_type="sensor")
        assert comp.name == "Test"
        assert comp.component_type == "sensor"
        assert comp.component_id  # Should have an auto-generated ID

    def test_validate_component(self) -> None:
        """Test component validation."""
        valid_comp = BaseComponent(name="Test", component_type="sensor")
        assert valid_comp.validate()

        invalid_comp = BaseComponent(name="", component_type="sensor")
        assert not invalid_comp.validate()

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        comp = BaseComponent(
            name="Test",
            component_type="sensor",
            specifications={"voltage": 3.3},
        )
        data = comp.to_dict()
        assert data["name"] == "Test"
        assert data["component_type"] == "sensor"
        assert data["specifications"]["voltage"] == 3.3

    def test_from_dict(self) -> None:
        """Test creating from dictionary."""
        data = {
            "name": "Test",
            "component_type": "sensor",
            "specifications": {"voltage": 3.3},
        }
        comp = BaseComponent.from_dict(data)
        assert comp.name == "Test"
        assert comp.component_type == "sensor"


class TestBaseDesign:
    """Tests for BaseDesign class."""

    def test_create_design(self) -> None:
        """Test creating a basic design."""
        design = BaseDesign(name="Test Design", description="A test")
        assert design.name == "Test Design"
        assert design.description == "A test"
        assert design.design_id

    def test_add_remove_component(self) -> None:
        """Test adding and removing components."""
        design = BaseDesign(name="Test")
        comp = BaseComponent(name="Sensor", component_type="sensor")

        design.add_component(comp)
        assert len(design.components) == 1

        removed = design.remove_component(comp.component_id)
        assert removed
        assert len(design.components) == 0

    def test_get_component(self) -> None:
        """Test getting a component by ID."""
        design = BaseDesign(name="Test")
        comp = BaseComponent(name="Sensor", component_type="sensor")
        design.add_component(comp)

        found = design.get_component(comp.component_id)
        assert found == comp

        not_found = design.get_component("invalid-id")
        assert not_found is None

    def test_validate_design(self) -> None:
        """Test design validation."""
        # Empty design should fail
        empty_design = BaseDesign(name="Test")
        is_valid, issues = empty_design.validate()
        assert not is_valid
        assert any("at least one component" in issue for issue in issues)

        # Design with component should pass
        valid_design = BaseDesign(name="Test")
        valid_design.add_component(BaseComponent(name="Sensor", component_type="sensor"))
        is_valid, issues = valid_design.validate()
        assert is_valid

    def test_serialization(self) -> None:
        """Test design serialization and deserialization."""
        design = BaseDesign(name="Test", description="A test design")
        design.add_component(BaseComponent(name="MCU", component_type="microcontroller"))

        data = design.to_dict()
        restored = BaseDesign.from_dict(data)

        assert restored.name == design.name
        assert restored.description == design.description
        assert len(restored.components) == 1


class TestEvent:
    """Tests for Event class."""

    def test_create_event(self) -> None:
        """Test creating an event."""
        event = Event(event_type="test_event", data={"key": "value"})
        assert event.event_type == "test_event"
        assert event.data["key"] == "value"
        assert event.event_id
        assert event.timestamp

    def test_event_to_dict(self) -> None:
        """Test event serialization."""
        event = Event(event_type="test", data={"x": 1}, source="test_source")
        data = event.to_dict()
        assert data["event_type"] == "test"
        assert data["data"]["x"] == 1
        assert data["source"] == "test_source"


class TestEventBus:
    """Tests for EventBus class."""

    def test_subscribe_and_publish(self) -> None:
        """Test subscribing to and publishing events."""
        bus = EventBus()
        received_events: list[Event] = []

        def handler(event: Event) -> None:
            received_events.append(event)

        bus.subscribe("test_event", handler)
        bus.publish(Event(event_type="test_event", data={}))

        assert len(received_events) == 1
        assert received_events[0].event_type == "test_event"

    def test_wildcard_subscription(self) -> None:
        """Test wildcard event subscription."""
        bus = EventBus()
        received_events: list[Event] = []

        def handler(event: Event) -> None:
            received_events.append(event)

        bus.subscribe("*", handler)
        bus.publish(Event(event_type="event_a", data={}))
        bus.publish(Event(event_type="event_b", data={}))

        assert len(received_events) == 2

    def test_unsubscribe(self) -> None:
        """Test unsubscribing from events."""
        bus = EventBus()
        received_events: list[Event] = []

        def handler(event: Event) -> None:
            received_events.append(event)

        bus.subscribe("test", handler)
        bus.publish(Event(event_type="test", data={}))
        assert len(received_events) == 1

        bus.unsubscribe("test", handler)
        bus.publish(Event(event_type="test", data={}))
        assert len(received_events) == 1  # Should still be 1

    def test_event_history(self) -> None:
        """Test event history tracking."""
        bus = EventBus()
        bus.publish(Event(event_type="event_a", data={}))
        bus.publish(Event(event_type="event_b", data={}))
        bus.publish(Event(event_type="event_a", data={}))

        all_history = bus.get_history()
        assert len(all_history) == 3

        filtered_history = bus.get_history(event_type="event_a")
        assert len(filtered_history) == 2
