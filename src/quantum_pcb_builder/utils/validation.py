"""
Validation utilities for PCB designs.

Provides comprehensive validation for circuits, boards,
and design rules.
"""

from typing import Any

from quantum_pcb_builder.core.circuit import Circuit
from quantum_pcb_builder.core.pcb import PCBBoard


def validate_circuit(circuit: Circuit) -> tuple[bool, list[str]]:
    """
    Validate a circuit for design integrity.

    Args:
        circuit: Circuit to validate

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = circuit.validate()
    return len(errors) == 0, errors


def validate_board(board: PCBBoard) -> tuple[bool, list[str]]:
    """
    Validate a PCB board for manufacturing readiness.

    Args:
        board: Board to validate

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = board.check_design_rule_violations()
    return len(errors) == 0, errors


def validate_design_rules(
    board: PCBBoard,
    custom_rules: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """
    Validate board against design rules.

    Args:
        board: Board to validate
        custom_rules: Optional custom design rules

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    rules = board.design_rules
    if custom_rules:
        if "min_trace_width_mm" in custom_rules:
            rules.min_trace_width_mm = custom_rules["min_trace_width_mm"]
        if "min_clearance_mm" in custom_rules:
            rules.min_clearance_mm = custom_rules["min_clearance_mm"]

    # Check traces
    for trace in board.traces:
        if trace.width_mm < rules.min_trace_width_mm:
            errors.append(
                f"Trace at {trace.start} violates minimum width "
                f"({trace.width_mm}mm < {rules.min_trace_width_mm}mm)"
            )

    # Check vias
    for via in board.vias:
        if via.drill_mm < rules.min_via_drill_mm:
            errors.append(
                f"Via at {via.position} violates minimum drill size "
                f"({via.drill_mm}mm < {rules.min_via_drill_mm}mm)"
            )

        annular_ring = (via.diameter_mm - via.drill_mm) / 2
        if annular_ring < rules.min_annular_ring_mm:
            errors.append(
                f"Via at {via.position} violates minimum annular ring "
                f"({annular_ring:.3f}mm < {rules.min_annular_ring_mm}mm)"
            )

    return len(errors) == 0, errors
