"""Tests for the factory module."""

from __future__ import annotations

import pytest

from quantum_pcb_builder.core.base import BaseComponent
from quantum_pcb_builder.core.exceptions import (
    ComponentNotFoundError,
    ConfigurationError,
)
from quantum_pcb_builder.core.factory import (
    ComponentBuilder,
    ComponentFactory,
)
from quantum_pcb_builder.core.quality import QualityLevel


class TestComponentFactory:
    """Tests for the ComponentFactory class."""

    def setup_method(self) -> None:
        """Reset factory before each test."""
        ComponentFactory.reset()

    def test_singleton(self) -> None:
        """Test that factory is singleton."""
        factory1 = ComponentFactory()
        factory2 = ComponentFactory()
        assert factory1 is factory2

    def test_register_component(self) -> None:
        """Test registering a component type."""
        factory = ComponentFactory()
        factory.register(
            component_type="test_component",
            factory_func=lambda name, **specs: BaseComponent(
                name=name,
                component_type="test",
                specifications=specs,
            ),
            description="Test component",
        )
        assert "test_component" in factory.list_types()

    def test_create_component(self) -> None:
        """Test creating a component."""
        factory = ComponentFactory()
        factory.register(
            component_type="simple",
            factory_func=lambda name, **specs: BaseComponent(
                name=name,
                component_type="simple",
                specifications=specs,
            ),
        )
        component = factory.create("simple", name="Test")
        assert component.name == "Test"
        assert component.component_type == "simple"

    def test_create_with_specs(self) -> None:
        """Test creating component with specifications."""
        factory = ComponentFactory()
        factory.register(
            component_type="configurable",
            factory_func=lambda name, **specs: BaseComponent(
                name=name,
                component_type="configurable",
                specifications=specs,
            ),
            default_specs={"voltage": 3.3},
        )
        component = factory.create("configurable", name="Test", current=100)
        assert component.specifications["voltage"] == 3.3
        assert component.specifications["current"] == 100

    def test_create_not_registered(self) -> None:
        """Test creating unregistered component type."""
        factory = ComponentFactory()
        with pytest.raises(ComponentNotFoundError):
            factory.create("nonexistent", name="Test")

    def test_unregister(self) -> None:
        """Test unregistering a component type."""
        factory = ComponentFactory()
        factory.register(
            component_type="temp",
            factory_func=lambda name, **specs: BaseComponent(
                name=name,
                component_type="temp",
            ),
        )
        assert factory.unregister("temp") is True
        assert "temp" not in factory.list_types()
        assert factory.unregister("temp") is False

    def test_get_blueprint(self) -> None:
        """Test getting blueprint."""
        factory = ComponentFactory()
        factory.register(
            component_type="test",
            factory_func=lambda name, **specs: BaseComponent(
                name=name,
                component_type="test",
            ),
            description="Test desc",
            version="2.0.0",
        )
        blueprint = factory.get_blueprint("test")
        assert blueprint is not None
        assert blueprint.description == "Test desc"
        assert blueprint.version == "2.0.0"

    def test_get_info(self) -> None:
        """Test getting component info."""
        factory = ComponentFactory()
        factory.register(
            component_type="info_test",
            factory_func=lambda name, **specs: BaseComponent(
                name=name,
                component_type="info_test",
            ),
            description="Info test component",
            version="1.2.3",
            default_specs={"x": 1},
        )
        info = factory.get_info("info_test")
        assert info["type"] == "info_test"
        assert info["description"] == "Info test component"
        assert info["version"] == "1.2.3"
        assert info["default_specs"]["x"] == 1

    def test_get_info_not_found(self) -> None:
        """Test getting info for unregistered type."""
        factory = ComponentFactory()
        with pytest.raises(ComponentNotFoundError):
            factory.get_info("nonexistent")


class TestComponentBuilder:
    """Tests for the ComponentBuilder class."""

    def setup_method(self) -> None:
        """Reset factory before each test."""
        ComponentFactory.reset()
        factory = ComponentFactory()
        factory.register(
            component_type="buildable",
            factory_func=lambda name, **specs: BaseComponent(
                name=name,
                component_type="buildable",
                specifications=specs,
            ),
        )

    def test_build_component(self) -> None:
        """Test building a component."""
        builder = ComponentBuilder[BaseComponent]("buildable")
        component = builder.with_name("MyComponent").build()
        assert component.name == "MyComponent"

    def test_build_with_specs(self) -> None:
        """Test building with specifications."""
        builder = ComponentBuilder[BaseComponent]("buildable")
        component = (
            builder.with_name("Test").with_spec("voltage", 5.0).with_spec("current", 100).build()
        )
        assert component.specifications["voltage"] == 5.0
        assert component.specifications["current"] == 100

    def test_build_with_multiple_specs(self) -> None:
        """Test building with multiple specs at once."""
        builder = ComponentBuilder[BaseComponent]("buildable")
        component = (
            builder.with_name("Test").with_specs(voltage=3.3, current=50, power=0.165).build()
        )
        assert component.specifications["voltage"] == 3.3
        assert component.specifications["current"] == 50
        assert component.specifications["power"] == 0.165

    def test_build_without_name(self) -> None:
        """Test building without name raises error."""
        builder = ComponentBuilder[BaseComponent]("buildable")
        with pytest.raises(ConfigurationError):
            builder.build()

    def test_skip_validation(self) -> None:
        """Test skipping validation."""
        builder = ComponentBuilder[BaseComponent]("buildable")
        component = builder.with_name("Test").skip_validation().build()
        assert component is not None

    def test_quality_level(self) -> None:
        """Test setting quality level."""
        builder = ComponentBuilder[BaseComponent]("buildable")
        builder.with_quality_level(QualityLevel.PREMIUM)
        assert builder._quality_level == QualityLevel.PREMIUM

    def test_chaining(self) -> None:
        """Test method chaining."""
        builder = ComponentBuilder[BaseComponent]("buildable")
        result = (
            builder.with_name("Chain")
            .with_spec("a", 1)
            .with_specs(b=2, c=3)
            .with_quality_level(QualityLevel.STRICT)
        )
        assert result is builder
