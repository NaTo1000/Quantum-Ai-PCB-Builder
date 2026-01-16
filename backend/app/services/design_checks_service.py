"""Design checks service for DRC, LVS, thermal, and signal integrity."""

import uuid
from typing import Optional

from app.schemas.design_checks import CheckViolation, DesignCheckResponse
from app.schemas.schematic import SchematicResponse


class DesignChecksService:
    """Service for running automated design checks."""

    def __init__(self):
        self._results: dict[str, DesignCheckResponse] = {}

    async def run_checks(
        self,
        schematic: SchematicResponse,
        check_types: list[str],
    ) -> DesignCheckResponse:
        """
        Run design checks on a schematic.

        Args:
            schematic: The schematic to check
            check_types: List of check types to run

        Returns:
            DesignCheckResponse with violations and pass/fail status
        """
        violations = []
        drc_passed = True
        lvs_passed = True
        thermal_passed = True
        signal_integrity_passed = True

        if "drc" in check_types:
            drc_violations = self._run_drc(schematic)
            violations.extend(drc_violations)
            drc_passed = len(drc_violations) == 0

        if "lvs" in check_types:
            lvs_violations = self._run_lvs(schematic)
            violations.extend(lvs_violations)
            lvs_passed = len(lvs_violations) == 0

        if "thermal" in check_types:
            thermal_violations = self._run_thermal_check(schematic)
            violations.extend(thermal_violations)
            thermal_passed = len(thermal_violations) == 0

        if "signal_integrity" in check_types:
            si_violations = self._run_signal_integrity_check(schematic)
            violations.extend(si_violations)
            signal_integrity_passed = len(si_violations) == 0

        errors = [v for v in violations if v.severity == "error"]
        passed = len(errors) == 0

        result = DesignCheckResponse(
            schematic_id=schematic.id,
            passed=passed,
            violations=violations,
            drc_passed=drc_passed,
            lvs_passed=lvs_passed,
            thermal_passed=thermal_passed,
            signal_integrity_passed=signal_integrity_passed,
            summary={
                "total_violations": len(violations),
                "errors": len(errors),
                "warnings": len([v for v in violations if v.severity == "warning"]),
                "info": len([v for v in violations if v.severity == "info"]),
            },
        )

        self._results[schematic.id] = result
        return result

    def _run_drc(self, schematic: SchematicResponse) -> list[CheckViolation]:
        """Run Design Rule Check."""
        violations = []

        # Check for minimum component spacing
        components = schematic.components
        for i, comp1 in enumerate(components):
            for comp2 in components[i + 1 :]:
                x1, y1 = comp1.position.get("x", 0), comp1.position.get("y", 0)
                x2, y2 = comp2.position.get("x", 0), comp2.position.get("y", 0)

                distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                if distance < 50:
                    violations.append(
                        CheckViolation(
                            id=str(uuid.uuid4())[:8],
                            check_type="drc",
                            severity="warning",
                            message=f"Components {comp1.name} and {comp2.name} are too close (spacing: {distance:.1f})",
                            location={"x": x1, "y": y1},
                            component_id=comp1.id,
                        )
                    )

        # Check for required decoupling capacitors
        has_mcu = any(c.type == "mcu" for c in components)
        has_decoupling = any(
            c.type == "passive" and c.value and "nF" in c.value for c in components
        )

        if has_mcu and not has_decoupling:
            violations.append(
                CheckViolation(
                    id=str(uuid.uuid4())[:8],
                    check_type="drc",
                    severity="warning",
                    message="MCU detected without decoupling capacitors",
                )
            )

        return violations

    def _run_lvs(self, schematic: SchematicResponse) -> list[CheckViolation]:
        """Run Layout vs Schematic check."""
        violations = []

        # Check for unconnected pins
        for comp in schematic.components:
            if comp.type == "mcu":
                # MCUs should have power connections
                power_nets = [n for n in schematic.nets if n.net_class == "power"]
                if len(power_nets) < 2:
                    violations.append(
                        CheckViolation(
                            id=str(uuid.uuid4())[:8],
                            check_type="lvs",
                            severity="error",
                            message=f"Component {comp.name} missing power connections",
                            component_id=comp.id,
                        )
                    )

        return violations

    def _run_thermal_check(
        self, schematic: SchematicResponse
    ) -> list[CheckViolation]:
        """Run thermal analysis check."""
        violations = []

        # Check for power components that may need thermal relief
        power_components = [
            c for c in schematic.components if c.type in ["voltage_regulator", "power_supply"]
        ]

        for comp in power_components:
            violations.append(
                CheckViolation(
                    id=str(uuid.uuid4())[:8],
                    check_type="thermal",
                    severity="info",
                    message=f"Component {comp.name} may require thermal relief or heatsink",
                    component_id=comp.id,
                )
            )

        return violations

    def _run_signal_integrity_check(
        self, schematic: SchematicResponse
    ) -> list[CheckViolation]:
        """Run signal integrity check."""
        violations = []

        # Check for RF components that may need impedance matching
        rf_components = [
            c for c in schematic.components if c.type in ["rf_module", "rf_component"]
        ]

        for comp in rf_components:
            violations.append(
                CheckViolation(
                    id=str(uuid.uuid4())[:8],
                    check_type="signal_integrity",
                    severity="info",
                    message=f"RF component {comp.name} - verify impedance matching",
                    component_id=comp.id,
                )
            )

        # Check for high-speed signals
        signal_nets = [n for n in schematic.nets if n.net_class == "signal"]
        if len(signal_nets) > 5:
            violations.append(
                CheckViolation(
                    id=str(uuid.uuid4())[:8],
                    check_type="signal_integrity",
                    severity="info",
                    message="Multiple signal nets detected - consider adding termination resistors",
                )
            )

        return violations

    def get_result(self, schematic_id: str) -> Optional[DesignCheckResponse]:
        """Get check results by schematic ID."""
        return self._results.get(schematic_id)


# Singleton instance
design_checks_service = DesignChecksService()
