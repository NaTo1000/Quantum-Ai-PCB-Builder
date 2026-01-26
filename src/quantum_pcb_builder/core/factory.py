"""Component factory for the Quantum PCB Builder system.

This module provides factory patterns for creating and registering
component types with proper error handling and validation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar

from quantum_pcb_builder.core.base import BaseComponent
from quantum_pcb_builder.core.exceptions import (
    ComponentNotFoundError,
    ComponentValidationError,
    ConfigurationError,
)
from quantum_pcb_builder.core.logging import get_logger
from quantum_pcb_builder.core.quality import QualityLevel, QualityReport, RuleBasedValidator

T = TypeVar("T", bound=BaseComponent)

logger = get_logger(__name__)


@dataclass
class ComponentBlueprint:
    """Blueprint for creating components."""

    component_type: str
    factory_func: Callable[..., BaseComponent]
    validator: RuleBasedValidator[BaseComponent] | None = None
    default_specs: dict[str, Any] | None = None
    description: str = ""
    version: str = "1.0.0"


class ComponentFactory:
    """Factory for creating and managing component types."""

    _instance: ComponentFactory | None = None
    _blueprints: dict[str, ComponentBlueprint] = {}

    def __new__(cls) -> ComponentFactory:
        """Singleton pattern for component factory."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._blueprints = {}
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the factory (useful for testing)."""
        cls._instance = None
        cls._blueprints = {}

    def register(
        self,
        component_type: str,
        factory_func: Callable[..., BaseComponent],
        validator: RuleBasedValidator[BaseComponent] | None = None,
        default_specs: dict[str, Any] | None = None,
        description: str = "",
        version: str = "1.0.0",
    ) -> ComponentFactory:
        """Register a component type.

        Args:
            component_type: Unique identifier for the component type.
            factory_func: Function that creates the component.
            validator: Optional validator for the component.
            default_specs: Default specifications for the component.
            description: Description of the component type.
            version: Version of the component specification.

        Returns:
            Self for chaining.

        Raises:
            ConfigurationError: If component type is already registered.
        """
        if component_type in self._blueprints:
            logger.warning(f"Overwriting existing blueprint for {component_type}")

        self._blueprints[component_type] = ComponentBlueprint(
            component_type=component_type,
            factory_func=factory_func,
            validator=validator,
            default_specs=default_specs or {},
            description=description,
            version=version,
        )

        logger.info(f"Registered component type: {component_type} v{version}")
        return self

    def unregister(self, component_type: str) -> bool:
        """Unregister a component type.

        Args:
            component_type: The component type to unregister.

        Returns:
            True if unregistered, False if not found.
        """
        if component_type in self._blueprints:
            del self._blueprints[component_type]
            logger.info(f"Unregistered component type: {component_type}")
            return True
        return False

    def create(
        self,
        component_type: str,
        name: str,
        validate: bool = True,
        quality_level: QualityLevel = QualityLevel.STANDARD,
        **specs: Any,
    ) -> BaseComponent:
        """Create a component of the specified type.

        Args:
            component_type: The type of component to create.
            name: Name for the component.
            validate: Whether to validate the component after creation.
            quality_level: Quality level for validation.
            **specs: Specifications for the component.

        Returns:
            The created component.

        Raises:
            ComponentNotFoundError: If component type is not registered.
            ComponentValidationError: If validation fails.
        """
        if component_type not in self._blueprints:
            raise ComponentNotFoundError(component_type)

        blueprint = self._blueprints[component_type]

        # Merge default specs with provided specs
        default = blueprint.default_specs or {}
        merged_specs = {**default, **specs}

        # Create the component
        try:
            component = blueprint.factory_func(name=name, **merged_specs)
        except Exception as e:
            logger.error(f"Failed to create component {component_type}: {e}")
            raise ComponentValidationError(
                message=f"Failed to create component: {e}",
                component_type=component_type,
            ) from e

        # Validate if requested
        if validate:
            self._validate_component(component, blueprint, quality_level)

        logger.debug(f"Created component: {component.component_id} ({component_type})")
        return component

    def _validate_component(
        self,
        component: BaseComponent,
        blueprint: ComponentBlueprint,
        quality_level: QualityLevel,
    ) -> None:
        """Validate a component using its blueprint validator.

        Raises:
            ComponentValidationError: If validation fails.
        """
        # Basic validation
        if not component.validate():
            raise ComponentValidationError(
                message="Component failed basic validation",
                component_id=component.component_id,
                component_type=blueprint.component_type,
            )

        # Blueprint validator
        if blueprint.validator:
            report = blueprint.validator.validate(component, quality_level)
            if not report.passed:
                raise ComponentValidationError(
                    message="Component failed quality validation",
                    component_id=component.component_id,
                    component_type=blueprint.component_type,
                    errors=report.errors,
                    warnings=report.warnings,
                    score=report.score,
                )

    def get_blueprint(self, component_type: str) -> ComponentBlueprint | None:
        """Get the blueprint for a component type."""
        return self._blueprints.get(component_type)

    def list_types(self) -> list[str]:
        """List all registered component types."""
        return list(self._blueprints.keys())

    def get_info(self, component_type: str) -> dict[str, Any]:
        """Get information about a component type.

        Args:
            component_type: The component type to get info for.

        Returns:
            Dictionary with component type information.

        Raises:
            ComponentNotFoundError: If component type is not registered.
        """
        if component_type not in self._blueprints:
            raise ComponentNotFoundError(component_type)

        blueprint = self._blueprints[component_type]
        return {
            "type": blueprint.component_type,
            "description": blueprint.description,
            "version": blueprint.version,
            "default_specs": blueprint.default_specs,
            "has_validator": blueprint.validator is not None,
        }


class ComponentBuilder(Generic[T]):
    """Builder pattern for creating components with fluent API."""

    def __init__(
        self,
        component_type: str,
        factory: ComponentFactory | None = None,
    ) -> None:
        self._component_type = component_type
        self._factory = factory or ComponentFactory()
        self._name: str = ""
        self._specs: dict[str, Any] = {}
        self._validate: bool = True
        self._quality_level: QualityLevel = QualityLevel.STANDARD

    def with_name(self, name: str) -> ComponentBuilder[T]:
        """Set the component name."""
        self._name = name
        return self

    def with_spec(self, key: str, value: Any) -> ComponentBuilder[T]:
        """Add a specification."""
        self._specs[key] = value
        return self

    def with_specs(self, **specs: Any) -> ComponentBuilder[T]:
        """Add multiple specifications."""
        self._specs.update(specs)
        return self

    def skip_validation(self) -> ComponentBuilder[T]:
        """Skip validation on build."""
        self._validate = False
        return self

    def with_quality_level(self, level: QualityLevel) -> ComponentBuilder[T]:
        """Set the quality level for validation."""
        self._quality_level = level
        return self

    def build(self) -> BaseComponent:
        """Build the component.

        Returns:
            The created component.

        Raises:
            ConfigurationError: If name is not set.
            ComponentNotFoundError: If component type is not registered.
            ComponentValidationError: If validation fails.
        """
        if not self._name:
            raise ConfigurationError(
                message="Component name is required",
                config_key="name",
            )

        return self._factory.create(
            component_type=self._component_type,
            name=self._name,
            validate=self._validate,
            quality_level=self._quality_level,
            **self._specs,
        )


# ============================================================================
# Abstract Builder for Extensibility
# ============================================================================


class AbstractComponentBuilder(ABC, Generic[T]):
    """Abstract builder for creating specific component types."""

    @abstractmethod
    def build(self) -> T:
        """Build the component."""
        ...

    @abstractmethod
    def validate_config(self) -> QualityReport:
        """Validate the builder configuration before building."""
        ...


# ============================================================================
# Default Component Registration
# ============================================================================


def register_default_components(factory: ComponentFactory) -> None:
    """Register default component types with the factory.

    This function registers the standard component types used in the
    Quantum PCB Builder system.
    """
    from quantum_pcb_builder.pcb.components import (
        CommunicationModule,
        Microcontroller,
        PowerModule,
        Sensor,
    )

    # Register microcontroller
    factory.register(
        component_type="microcontroller",
        factory_func=lambda name, **specs: Microcontroller(name=name, **specs),
        description="Microcontroller units (ESP32, Arduino, etc.)",
        version="1.0.0",
    )

    # Register sensor
    factory.register(
        component_type="sensor",
        factory_func=lambda name, **specs: Sensor(name=name, **specs),
        description="Sensors (temperature, humidity, motion, etc.)",
        version="1.0.0",
    )

    # Register communication module
    factory.register(
        component_type="communication",
        factory_func=lambda name, **specs: CommunicationModule(name=name, **specs),
        description="Communication modules (LoRa, WiFi, Bluetooth, etc.)",
        version="1.0.0",
    )

    # Register power module
    factory.register(
        component_type="power",
        factory_func=lambda name, **specs: PowerModule(name=name, **specs),
        description="Power management modules",
        version="1.0.0",
    )

    logger.info("Registered default component types")
