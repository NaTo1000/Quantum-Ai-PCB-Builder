"""Base classes for the Quantum PCB Builder system."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.is_valid = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def merge(self, other: ValidationResult) -> ValidationResult:
        """Merge another validation result into this one."""
        return ValidationResult(
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
        )


@dataclass
class BaseComponent:
    """Base class for PCB components."""

    name: str
    component_type: str
    specifications: dict[str, Any] = field(default_factory=dict)
    component_id: str = field(default_factory=lambda: str(uuid4()))

    def validate(self) -> bool:
        """Validate the component configuration."""
        return bool(self.name and self.component_type)

    def to_dict(self) -> dict[str, Any]:
        """Serialize component to dictionary."""
        return {
            "component_id": self.component_id,
            "name": self.name,
            "component_type": self.component_type,
            "specifications": self.specifications,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaseComponent:
        """Create a component from a dictionary."""
        return cls(
            component_id=data.get("component_id", str(uuid4())),
            name=data["name"],
            component_type=data["component_type"],
            specifications=data.get("specifications", {}),
        )


@dataclass
class BaseDesign:
    """Base class for PCB designs."""

    name: str
    description: str = ""
    design_id: str = field(default_factory=lambda: str(uuid4()))
    components: list[BaseComponent] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_component(self, component: BaseComponent) -> None:
        """Add a component to the design."""
        self.components.append(component)

    def remove_component(self, component_id: str) -> bool:
        """Remove a component from the design by ID."""
        for i, comp in enumerate(self.components):
            if comp.component_id == component_id:
                self.components.pop(i)
                return True
        return False

    def get_component(self, component_id: str) -> BaseComponent | None:
        """Get a component by ID."""
        for comp in self.components:
            if comp.component_id == component_id:
                return comp
        return None

    def validate(self) -> tuple[bool, list[str]]:
        """Validate the entire design."""
        issues: list[str] = []

        if not self.name:
            issues.append("Design must have a name")

        if not self.components:
            issues.append("Design must have at least one component")

        for comp in self.components:
            if not comp.validate():
                issues.append(f"Component {comp.component_id} is invalid")

        return (len(issues) == 0, issues)

    def to_dict(self) -> dict[str, Any]:
        """Serialize design to dictionary."""
        return {
            "design_id": self.design_id,
            "name": self.name,
            "description": self.description,
            "components": [comp.to_dict() for comp in self.components],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaseDesign:
        """Create a design from a dictionary."""
        components = [
            BaseComponent.from_dict(comp_data) for comp_data in data.get("components", [])
        ]
        return cls(
            design_id=data.get("design_id", str(uuid4())),
            name=data["name"],
            description=data.get("description", ""),
            components=components,
            metadata=data.get("metadata", {}),
        )
