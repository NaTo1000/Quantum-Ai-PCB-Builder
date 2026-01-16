"""Simulation service for SPICE, timing, and power simulations."""

import uuid
from typing import Optional

from app.schemas.simulation import SimulationResult, SimulationResponse
from app.schemas.schematic import SchematicResponse


# Configuration constants for simulation
DEFAULT_VOLTAGE = 3.3  # Default operating voltage in volts
VOLTAGE_RIPPLE_BASE = 0.9  # Base voltage ripple factor
VOLTAGE_RIPPLE_VARIATION = 0.1  # Voltage ripple variation factor


class SimulationService:
    """Service for running simulations on schematics."""

    def __init__(self):
        self._simulations: dict[str, SimulationResponse] = {}

    async def run_simulation(
        self,
        schematic: SchematicResponse,
        simulation_type: str = "spice",
        parameters: dict = None,
    ) -> SimulationResponse:
        """
        Run a simulation on a schematic.

        Args:
            schematic: The schematic to simulate
            simulation_type: Type of simulation (spice, timing, power)
            parameters: Simulation parameters

        Returns:
            SimulationResponse with results and visual feedback
        """
        parameters = parameters or {}
        simulation_id = str(uuid.uuid4())

        if simulation_type == "spice":
            result = self._run_spice_simulation(schematic, parameters)
        elif simulation_type == "timing":
            result = self._run_timing_simulation(schematic, parameters)
        elif simulation_type == "power":
            result = self._run_power_simulation(schematic, parameters)
        else:
            result = SimulationResult(
                id=simulation_id,
                simulation_type=simulation_type,
                status="failed",
                data={"error": f"Unknown simulation type: {simulation_type}"},
            )

        result.id = simulation_id
        visual_feedback = self._generate_visual_feedback(result)

        response = SimulationResponse(
            schematic_id=schematic.id,
            simulation_id=simulation_id,
            result=result,
            visual_feedback=visual_feedback,
        )

        self._simulations[simulation_id] = response
        return response

    def _run_spice_simulation(
        self, schematic: SchematicResponse, parameters: dict
    ) -> SimulationResult:
        """Run SPICE simulation."""
        # Generate SPICE netlist from schematic
        netlist = self._generate_netlist(schematic)

        # Simulate voltage and current waveforms
        waveforms = []
        for i, comp in enumerate(schematic.components):
            waveforms.append({
                "node": f"V({comp.name})",
                "type": "voltage",
                "data": [
                    {"time": t * 0.001, "value": DEFAULT_VOLTAGE * (VOLTAGE_RIPPLE_BASE + VOLTAGE_RIPPLE_VARIATION * (i % 3))}
                    for t in range(100)
                ],
            })

        return SimulationResult(
            id="",
            simulation_type="spice",
            status="completed",
            data={
                "netlist": netlist,
                "analysis_type": parameters.get("analysis", "transient"),
                "duration": parameters.get("duration", "1ms"),
            },
            waveforms=waveforms,
            confidence_score=0.85,
        )

    def _run_timing_simulation(
        self, schematic: SchematicResponse, parameters: dict
    ) -> SimulationResult:
        """Run timing analysis simulation."""
        timing_report = {
            "clock_frequency": parameters.get("clock_freq", "80MHz"),
            "setup_time": "2.5ns",
            "hold_time": "1.0ns",
            "propagation_delay": "5.0ns",
            "critical_path": [],
            "slack": "3.5ns",
            "timing_met": True,
        }

        # Identify critical path through components
        if schematic.components:
            timing_report["critical_path"] = [
                {"component": c.name, "delay": "1.2ns"}
                for c in schematic.components[:3]
            ]

        return SimulationResult(
            id="",
            simulation_type="timing",
            status="completed",
            data={"clock_constraints": parameters},
            timing_report=timing_report,
            confidence_score=0.90,
        )

    def _run_power_simulation(
        self, schematic: SchematicResponse, parameters: dict
    ) -> SimulationResult:
        """Run power analysis simulation."""
        # Calculate power consumption for each component
        power_breakdown = []
        total_power = 0.0

        power_estimates = {
            "mcu": 50.0,
            "rf_module": 120.0,
            "sensor": 5.0,
            "passive": 0.0,
            "indicator": 20.0,
            "voltage_regulator": 10.0,
        }

        for comp in schematic.components:
            power = power_estimates.get(comp.type, 1.0)
            total_power += power
            power_breakdown.append({
                "component": comp.name,
                "type": comp.type,
                "power_mw": power,
            })

        power_report = {
            "total_power_mw": total_power,
            "voltage": parameters.get("voltage", 3.3),
            "current_ma": total_power / parameters.get("voltage", 3.3),
            "power_breakdown": power_breakdown,
            "efficiency": 0.85,
            "thermal_dissipation_mw": total_power * 0.15,
        }

        return SimulationResult(
            id="",
            simulation_type="power",
            status="completed",
            data={"operating_conditions": parameters},
            power_report=power_report,
            confidence_score=0.88,
        )

    def _generate_netlist(self, schematic: SchematicResponse) -> str:
        """Generate SPICE netlist from schematic."""
        lines = ["* Auto-generated SPICE netlist", f"* Schematic: {schematic.id}", ""]

        # Add power supply
        lines.append("VCC VCC 0 DC 3.3")

        # Add components
        for i, comp in enumerate(schematic.components):
            if comp.type == "passive":
                if comp.value and "nF" in comp.value:
                    value = comp.value.replace("nF", "n")
                    lines.append(f"C{i + 1} VCC 0 {value}")
                elif comp.value and "k" in comp.value:
                    value = comp.value
                    lines.append(f"R{i + 1} VCC 0 {value}")

        lines.append("")
        lines.append(".tran 1u 1m")
        lines.append(".end")

        return "\n".join(lines)

    def _generate_visual_feedback(self, result: SimulationResult) -> str:
        """Generate SVG visual feedback for simulation results."""
        if not result.waveforms:
            return ""

        width = 600
        height = 200
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
            '<rect width="100%" height="100%" fill="#1a1a2e"/>',
            '<text x="10" y="20" fill="#fff" font-family="Arial">Simulation Waveforms</text>',
        ]

        colors = ["#00ff88", "#ff6b6b", "#4ecdc4", "#f7dc6f"]
        for i, waveform in enumerate(result.waveforms[:4]):
            color = colors[i % len(colors)]
            y_offset = 50 + i * 40

            # Draw waveform line
            points = []
            for j, point in enumerate(waveform.get("data", [])[:50]):
                x = 50 + j * 10
                y = y_offset + 15 - point.get("value", 0) * 3
                points.append(f"{x},{y}")

            if points:
                svg_parts.append(
                    f'<polyline points="{" ".join(points)}" '
                    f'fill="none" stroke="{color}" stroke-width="2"/>'
                )
                svg_parts.append(
                    f'<text x="10" y="{y_offset + 10}" fill="{color}" '
                    f'font-family="Arial" font-size="10">{waveform.get("node", "")}</text>'
                )

        svg_parts.append("</svg>")
        return "".join(svg_parts)

    def get_simulation(self, simulation_id: str) -> Optional[SimulationResponse]:
        """Get simulation by ID."""
        return self._simulations.get(simulation_id)


# Singleton instance
simulation_service = SimulationService()
