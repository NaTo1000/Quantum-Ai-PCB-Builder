"""
Design Validator

This module validates PCB/chip designs for conflicts, errors, and design rule violations.
It performs electrical rule checks (ERC) and design rule checks (DRC).
"""

from dataclasses import dataclass
from typing import Any
from enum import Enum

from .schematic_generator import Schematic, SchematicComponent, Net, PinType, NetType


class SeverityLevel(Enum):
    """Severity levels for design issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ViolationType(Enum):
    """Types of design violations."""
    # Electrical Rule Checks
    FLOATING_PIN = "floating_pin"
    POWER_SHORT = "power_short"
    MISSING_POWER = "missing_power"
    MISSING_GROUND = "missing_ground"
    MULTIPLE_DRIVERS = "multiple_drivers"
    NO_DRIVER = "no_driver"
    
    # Design Rule Checks
    CLEARANCE_VIOLATION = "clearance_violation"
    TRACE_WIDTH = "trace_width"
    DRILL_SIZE = "drill_size"
    COMPONENT_OVERLAP = "component_overlap"
    
    # Component Checks
    MISSING_VALUE = "missing_value"
    INVALID_FOOTPRINT = "invalid_footprint"
    REFERENCE_DUPLICATE = "reference_duplicate"
    
    # Connectivity Checks
    UNCONNECTED_NET = "unconnected_net"
    SINGLE_PIN_NET = "single_pin_net"


@dataclass
class Violation:
    """A design violation or issue."""
    violation_id: str
    violation_type: ViolationType
    severity: SeverityLevel
    message: str
    component_id: str | None = None
    net_id: str | None = None
    location: tuple[float, float] | None = None
    suggestion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert violation to dictionary."""
        return {
            "id": self.violation_id,
            "type": self.violation_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "component_id": self.component_id,
            "net_id": self.net_id,
            "location": self.location,
            "suggestion": self.suggestion
        }


@dataclass
class ValidationResult:
    """Result of design validation."""
    is_valid: bool
    violations: list[Violation]
    summary: dict[str, int]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            "is_valid": self.is_valid,
            "violations": [v.to_dict() for v in self.violations],
            "summary": self.summary
        }


class DesignValidator:
    """
    Validates PCB/chip designs for errors and conflicts.
    
    Performs comprehensive checks including:
    - Electrical Rule Checks (ERC)
    - Design Rule Checks (DRC)
    - Component validation
    - Connectivity analysis
    """
    
    # Design rule constraints
    DEFAULT_RULES: dict[str, Any] = {
        "min_clearance_mm": 0.15,
        "min_trace_width_mm": 0.2,
        "min_drill_size_mm": 0.3,
        "max_component_overlap_percent": 0,
    }

    def __init__(self, rules: dict[str, Any] | None = None):
        """
        Initialize the validator with design rules.
        
        Args:
            rules: Custom design rules to override defaults.
        """
        self.rules = {**self.DEFAULT_RULES}
        if rules:
            self.rules.update(rules)
        self._violation_counter = 0

    def validate(self, schematic: Schematic) -> ValidationResult:
        """
        Validate a schematic design.
        
        Args:
            schematic: The schematic to validate.
            
        Returns:
            ValidationResult containing all violations and summary.
        """
        self._violation_counter = 0
        violations: list[Violation] = []
        
        # Run all validation checks
        violations.extend(self._check_power_connections(schematic))
        violations.extend(self._check_floating_pins(schematic))
        violations.extend(self._check_net_integrity(schematic))
        violations.extend(self._check_component_values(schematic))
        violations.extend(self._check_reference_duplicates(schematic))
        violations.extend(self._check_component_positions(schematic))
        
        # Determine if design is valid
        has_critical = any(v.severity == SeverityLevel.CRITICAL for v in violations)
        has_error = any(v.severity == SeverityLevel.ERROR for v in violations)
        is_valid = not (has_critical or has_error)
        
        # Generate summary
        summary = {
            "total": len(violations),
            "critical": sum(1 for v in violations if v.severity == SeverityLevel.CRITICAL),
            "errors": sum(1 for v in violations if v.severity == SeverityLevel.ERROR),
            "warnings": sum(1 for v in violations if v.severity == SeverityLevel.WARNING),
            "info": sum(1 for v in violations if v.severity == SeverityLevel.INFO),
        }
        
        return ValidationResult(
            is_valid=is_valid,
            violations=violations,
            summary=summary
        )

    def _generate_violation_id(self) -> str:
        """Generate a unique violation ID."""
        self._violation_counter += 1
        return f"VIO-{self._violation_counter:04d}"

    def _check_power_connections(self, schematic: Schematic) -> list[Violation]:
        """Check for proper power and ground connections."""
        violations: list[Violation] = []
        
        # Find power and ground nets
        power_nets = [n for n in schematic.nets if n.net_type == NetType.POWER]
        ground_nets = [n for n in schematic.nets if n.net_type == NetType.GROUND]
        
        # Check if power net exists
        if not power_nets:
            violations.append(Violation(
                violation_id=self._generate_violation_id(),
                violation_type=ViolationType.MISSING_POWER,
                severity=SeverityLevel.ERROR,
                message="No power net found in the design",
                suggestion="Add a power supply connection to the design"
            ))
        
        # Check if ground net exists
        if not ground_nets:
            violations.append(Violation(
                violation_id=self._generate_violation_id(),
                violation_type=ViolationType.MISSING_GROUND,
                severity=SeverityLevel.ERROR,
                message="No ground net found in the design",
                suggestion="Add a ground connection to the design"
            ))
        
        # Check for power/ground shorts
        for net in schematic.nets:
            connected_pins = set()
            for comp_id, pin_id in net.connections:
                comp = next((c for c in schematic.components if c.component_id == comp_id), None)
                if comp:
                    pin = next((p for p in comp.pins if p.pin_id == pin_id), None)
                    if pin:
                        connected_pins.add(pin.pin_type)
            
            if PinType.POWER in connected_pins and PinType.GROUND in connected_pins:
                violations.append(Violation(
                    violation_id=self._generate_violation_id(),
                    violation_type=ViolationType.POWER_SHORT,
                    severity=SeverityLevel.CRITICAL,
                    message=f"Power short detected on net '{net.name}'",
                    net_id=net.net_id,
                    suggestion="Check wiring between power and ground pins"
                ))
        
        return violations

    def _check_floating_pins(self, schematic: Schematic) -> list[Violation]:
        """Check for unconnected (floating) pins that should be connected."""
        violations: list[Violation] = []
        
        # Build set of connected pins
        connected_pins: set[str] = set()
        for net in schematic.nets:
            for _, pin_id in net.connections:
                connected_pins.add(pin_id)
        
        # Check each component for floating pins
        for component in schematic.components:
            for pin in component.pins:
                # Power and ground pins should be connected
                if pin.pin_type in [PinType.POWER, PinType.GROUND]:
                    if pin.pin_id not in connected_pins:
                        violations.append(Violation(
                            violation_id=self._generate_violation_id(),
                            violation_type=ViolationType.FLOATING_PIN,
                            severity=SeverityLevel.ERROR,
                            message=f"Floating {pin.pin_type.value} pin '{pin.name}' on {component.reference}",
                            component_id=component.component_id,
                            suggestion=f"Connect pin '{pin.name}' to the appropriate power/ground net"
                        ))
                
                # Input pins should generally be connected (warning only)
                elif pin.pin_type == PinType.INPUT:
                    if pin.pin_id not in connected_pins:
                        violations.append(Violation(
                            violation_id=self._generate_violation_id(),
                            violation_type=ViolationType.FLOATING_PIN,
                            severity=SeverityLevel.WARNING,
                            message=f"Unconnected input pin '{pin.name}' on {component.reference}",
                            component_id=component.component_id,
                            suggestion=f"Connect or tie pin '{pin.name}' to appropriate signal/level"
                        ))
        
        return violations

    def _check_net_integrity(self, schematic: Schematic) -> list[Violation]:
        """Check net connectivity and integrity."""
        violations: list[Violation] = []
        
        for net in schematic.nets:
            # Check for single-pin nets (useless connections)
            if len(net.connections) == 1:
                violations.append(Violation(
                    violation_id=self._generate_violation_id(),
                    violation_type=ViolationType.SINGLE_PIN_NET,
                    severity=SeverityLevel.WARNING,
                    message=f"Net '{net.name}' has only one connection",
                    net_id=net.net_id,
                    suggestion="Either add more connections or remove this net"
                ))
            
            # Check for empty nets
            if len(net.connections) == 0:
                violations.append(Violation(
                    violation_id=self._generate_violation_id(),
                    violation_type=ViolationType.UNCONNECTED_NET,
                    severity=SeverityLevel.WARNING,
                    message=f"Net '{net.name}' has no connections",
                    net_id=net.net_id,
                    suggestion="Remove this empty net"
                ))
            
            # Check for multiple output drivers on same net (for signal nets)
            if net.net_type == NetType.SIGNAL:
                driver_count = 0
                for comp_id, pin_id in net.connections:
                    comp = next((c for c in schematic.components if c.component_id == comp_id), None)
                    if comp:
                        pin = next((p for p in comp.pins if p.pin_id == pin_id), None)
                        if pin and pin.pin_type == PinType.OUTPUT:
                            driver_count += 1
                
                if driver_count > 1:
                    violations.append(Violation(
                        violation_id=self._generate_violation_id(),
                        violation_type=ViolationType.MULTIPLE_DRIVERS,
                        severity=SeverityLevel.ERROR,
                        message=f"Net '{net.name}' has {driver_count} output drivers",
                        net_id=net.net_id,
                        suggestion="Use buffers or ensure only one output drives this net"
                    ))
        
        return violations

    def _check_component_values(self, schematic: Schematic) -> list[Violation]:
        """Check that components have valid values."""
        violations: list[Violation] = []
        
        # Components that require values
        value_required = ["resistor", "capacitor", "inductor", "crystal"]
        
        for component in schematic.components:
            if component.component_type in value_required:
                if not component.value:
                    violations.append(Violation(
                        violation_id=self._generate_violation_id(),
                        violation_type=ViolationType.MISSING_VALUE,
                        severity=SeverityLevel.WARNING,
                        message=f"Component {component.reference} missing value",
                        component_id=component.component_id,
                        suggestion=f"Specify a value for {component.component_type} {component.reference}"
                    ))
            
            # Check footprint
            if not component.footprint or component.footprint == "GENERIC":
                violations.append(Violation(
                    violation_id=self._generate_violation_id(),
                    violation_type=ViolationType.INVALID_FOOTPRINT,
                    severity=SeverityLevel.INFO,
                    message=f"Component {component.reference} has generic footprint",
                    component_id=component.component_id,
                    suggestion="Specify a specific footprint for manufacturing"
                ))
        
        return violations

    def _check_reference_duplicates(self, schematic: Schematic) -> list[Violation]:
        """Check for duplicate reference designators."""
        violations: list[Violation] = []
        references: dict[str, list[str]] = {}
        
        for component in schematic.components:
            ref = component.reference
            if ref not in references:
                references[ref] = []
            references[ref].append(component.component_id)
        
        for ref, comp_ids in references.items():
            if len(comp_ids) > 1:
                violations.append(Violation(
                    violation_id=self._generate_violation_id(),
                    violation_type=ViolationType.REFERENCE_DUPLICATE,
                    severity=SeverityLevel.ERROR,
                    message=f"Duplicate reference designator '{ref}' found",
                    suggestion=f"Rename components to have unique references"
                ))
        
        return violations

    def _check_component_positions(self, schematic: Schematic) -> list[Violation]:
        """Check for component position issues like overlaps."""
        violations: list[Violation] = []
        
        # Simple overlap detection (for components at same position)
        positions: dict[tuple[float, float], list[str]] = {}
        
        for component in schematic.components:
            pos = component.position
            if pos not in positions:
                positions[pos] = []
            positions[pos].append(component.reference)
        
        for pos, refs in positions.items():
            if len(refs) > 1:
                violations.append(Violation(
                    violation_id=self._generate_violation_id(),
                    violation_type=ViolationType.COMPONENT_OVERLAP,
                    severity=SeverityLevel.WARNING,
                    message=f"Components at same position: {', '.join(refs)}",
                    location=pos,
                    suggestion="Adjust component positions to avoid overlap"
                ))
        
        return violations
