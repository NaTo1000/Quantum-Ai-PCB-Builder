"""Design validators for PCB designs."""

from dataclasses import dataclass, field
from typing import Any

from quantum_pcb_builder.core.base import BaseComponent, BaseDesign, ValidationResult
from quantum_pcb_builder.pcb.layout import PCBLayout


@dataclass
class CompatibilityRule:
    """Rule for component compatibility checking."""

    rule_id: str
    description: str
    source_type: str
    target_type: str
    is_compatible: bool = True
    conditions: dict[str, Any] = field(default_factory=dict)


class ComponentCompatibilityChecker:
    """Checks compatibility between components."""

    def __init__(self) -> None:
        """Initialize the compatibility checker."""
        self._rules: list[CompatibilityRule] = []
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load default compatibility rules."""
        # Power compatibility rules
        self._rules.append(
            CompatibilityRule(
                rule_id="power_voltage_match",
                description="Power module output must match component voltage requirements",
                source_type="power",
                target_type="microcontroller",
                conditions={"voltage_tolerance": 0.2},
            )
        )

        # Communication compatibility
        self._rules.append(
            CompatibilityRule(
                rule_id="communication_interface",
                description="Communication modules must have compatible interfaces",
                source_type="microcontroller",
                target_type="communication",
            )
        )

        # Sensor compatibility
        self._rules.append(
            CompatibilityRule(
                rule_id="sensor_interface",
                description="Sensor interface must be supported by microcontroller",
                source_type="microcontroller",
                target_type="sensor",
            )
        )

    def add_rule(self, rule: CompatibilityRule) -> None:
        """Add a compatibility rule."""
        self._rules.append(rule)

    def check_pair(
        self, component_a: BaseComponent, component_b: BaseComponent
    ) -> ValidationResult:
        """Check compatibility between two components."""
        result = ValidationResult(is_valid=True)

        # Find applicable rules
        for rule in self._rules:
            is_matching_rule = (
                rule.source_type == component_a.component_type
                and rule.target_type == component_b.component_type
            ) or (
                rule.source_type == component_b.component_type
                and rule.target_type == component_a.component_type
            )
            # Apply rule-specific checks
            if is_matching_rule and not rule.is_compatible:
                result.add_error(
                    f"Incompatible components: {component_a.name} and {component_b.name} "
                    f"({rule.description})"
                )

        return result

    def check_design(self, design: BaseDesign) -> ValidationResult:
        """Check all components in a design for compatibility."""
        result = ValidationResult(is_valid=True)
        components = design.components

        for i, comp_a in enumerate(components):
            for comp_b in components[i + 1 :]:
                pair_result = self.check_pair(comp_a, comp_b)
                result = result.merge(pair_result)

        return result


class DesignValidator:
    """Comprehensive design validator."""

    def __init__(self) -> None:
        """Initialize the design validator."""
        self.compatibility_checker = ComponentCompatibilityChecker()
        self._min_trace_width_mm: float = 0.15
        self._min_component_spacing_mm: float = 0.5

    def validate(self, design: BaseDesign) -> ValidationResult:
        """Perform full validation on a design."""
        result = ValidationResult(is_valid=True)

        # Basic validation
        is_valid, issues = design.validate()
        if not is_valid:
            for issue in issues:
                result.add_error(issue)

        # Component validation
        for comp in design.components:
            if not comp.validate():
                result.add_error(f"Component validation failed: {comp.name}")

        # Compatibility checking
        compat_result = self.compatibility_checker.check_design(design)
        result = result.merge(compat_result)

        # Layout-specific validation
        if isinstance(design, PCBLayout):
            layout_result = self._validate_layout(design)
            result = result.merge(layout_result)

        return result

    def _validate_layout(self, layout: PCBLayout) -> ValidationResult:
        """Validate PCB layout specific rules."""
        result = ValidationResult(is_valid=True)

        # Check component spacing
        placed = layout.get_placed_components()
        for i, pc_a in enumerate(placed):
            for pc_b in placed[i + 1 :]:
                distance = pc_a.position.distance_to(pc_b.position)
                if distance < self._min_component_spacing_mm:
                    result.add_warning(
                        f"Components {pc_a.component.name} and {pc_b.component.name} "
                        f"are very close ({distance:.2f}mm)"
                    )

        # Check connections
        for conn in layout.get_connections():
            if conn.trace_width_mm < self._min_trace_width_mm:
                result.add_warning(
                    f"Trace width {conn.trace_width_mm}mm is below minimum "
                    f"recommended {self._min_trace_width_mm}mm"
                )

        return result
