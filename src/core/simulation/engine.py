"""
Simulation Engine

This module provides simulation capabilities for PCB/chip designs,
including power analysis, signal integrity, and thermal simulation.
"""

from dataclasses import dataclass
from typing import Any
from enum import Enum

from ..design.schematic_generator import Schematic, SchematicComponent, Net, NetType


class SimulationType(Enum):
    """Types of simulations available."""
    POWER_ANALYSIS = "power_analysis"
    SIGNAL_INTEGRITY = "signal_integrity"
    THERMAL = "thermal"
    TIMING = "timing"
    EMC = "emc"


class SimulationStatus(Enum):
    """Status of a simulation run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PowerAnalysisResult:
    """Results from power analysis simulation."""
    total_power_consumption_mw: float
    voltage_levels: dict[str, float]
    current_per_component: dict[str, float]
    efficiency_percent: float
    power_dissipation_mw: float


@dataclass
class SignalIntegrityResult:
    """Results from signal integrity simulation."""
    rise_time_ns: float
    fall_time_ns: float
    overshoot_percent: float
    undershoot_percent: float
    crosstalk_db: float
    impedance_ohms: float


@dataclass
class ThermalResult:
    """Results from thermal simulation."""
    max_temperature_c: float
    min_temperature_c: float
    average_temperature_c: float
    hot_spots: list[tuple[str, float]]
    thermal_gradient: float


@dataclass
class SimulationResult:
    """Complete simulation result."""
    simulation_id: str
    simulation_type: SimulationType
    status: SimulationStatus
    schematic_id: str
    results: dict[str, Any]
    warnings: list[str]
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert simulation result to dictionary."""
        return {
            "simulation_id": self.simulation_id,
            "type": self.simulation_type.value,
            "status": self.status.value,
            "schematic_id": self.schematic_id,
            "results": self.results,
            "warnings": self.warnings,
            "recommendations": self.recommendations
        }


class SimulationEngine:
    """
    Simulation engine for PCB/chip design analysis.
    
    Provides various simulation capabilities including:
    - Power consumption analysis
    - Signal integrity analysis
    - Thermal analysis
    - Timing analysis
    """
    
    # Typical component power consumption estimates (mW)
    COMPONENT_POWER: dict[str, float] = {
        "microcontroller": 150.0,
        "esp32": 200.0,
        "resistor": 0.1,
        "capacitor": 0.0,
        "inductor": 0.0,
        "led": 20.0,
        "sensor": 5.0,
        "regulator": 10.0,
        "crystal": 0.5,
        "connector": 0.0,
        "transistor": 1.0,
        "esd_protection": 0.1,
        "battery_charger": 50.0,
    }
    
    # Thermal resistance estimates (C/W)
    THERMAL_RESISTANCE: dict[str, float] = {
        "QFN-48": 30.0,
        "DIP-28": 50.0,
        "SOT-223": 40.0,
        "SOT-23": 100.0,
        "0805": 200.0,
        "1210": 150.0,
    }

    def __init__(self):
        """Initialize the simulation engine."""
        self._sim_counter = 0

    def run_simulation(
        self,
        schematic: Schematic,
        simulation_type: SimulationType
    ) -> SimulationResult:
        """
        Run a simulation on a schematic.
        
        Args:
            schematic: The schematic to simulate.
            simulation_type: Type of simulation to run.
            
        Returns:
            SimulationResult with analysis data.
        """
        self._sim_counter += 1
        sim_id = f"SIM-{self._sim_counter:04d}"
        
        if simulation_type == SimulationType.POWER_ANALYSIS:
            return self._run_power_analysis(schematic, sim_id)
        elif simulation_type == SimulationType.SIGNAL_INTEGRITY:
            return self._run_signal_integrity(schematic, sim_id)
        elif simulation_type == SimulationType.THERMAL:
            return self._run_thermal_analysis(schematic, sim_id)
        elif simulation_type == SimulationType.TIMING:
            return self._run_timing_analysis(schematic, sim_id)
        elif simulation_type == SimulationType.EMC:
            return self._run_emc_analysis(schematic, sim_id)
        else:
            return SimulationResult(
                simulation_id=sim_id,
                simulation_type=simulation_type,
                status=SimulationStatus.FAILED,
                schematic_id=schematic.schematic_id,
                results={"error": "Unknown simulation type"},
                warnings=[],
                recommendations=[]
            )

    def run_all_simulations(self, schematic: Schematic) -> list[SimulationResult]:
        """
        Run all available simulations on a schematic.
        
        Args:
            schematic: The schematic to simulate.
            
        Returns:
            List of SimulationResults for each simulation type.
        """
        results = []
        for sim_type in SimulationType:
            result = self.run_simulation(schematic, sim_type)
            results.append(result)
        return results

    def _run_power_analysis(self, schematic: Schematic, sim_id: str) -> SimulationResult:
        """Run power consumption analysis."""
        warnings = []
        recommendations = []
        current_per_component: dict[str, float] = {}
        total_power = 0.0
        
        # Get voltage from metadata
        power_req = schematic.metadata.get("power_requirements", {})
        voltage = power_req.get("voltage", 3.3)
        
        # Calculate power per component
        for component in schematic.components:
            comp_type = component.component_type
            base_power = self.COMPONENT_POWER.get(comp_type, 1.0)
            
            # Adjust for component value if applicable
            if comp_type == "led" and component.value:
                # LED power depends on current limiting
                base_power = 20.0
            
            total_power += base_power
            current_per_component[component.reference] = base_power / voltage
        
        # Efficiency calculation (simplified)
        efficiency = 85.0 if "regulator" in [c.component_type for c in schematic.components] else 70.0
        power_dissipation = total_power * (100 - efficiency) / 100
        
        # Generate warnings and recommendations
        if total_power > 500:
            warnings.append("High power consumption detected (>500mW)")
            recommendations.append("Consider using low-power component variants")
        
        if efficiency < 80:
            recommendations.append("Add a switching regulator for better efficiency")
        
        results = {
            "total_power_consumption_mw": round(total_power, 2),
            "voltage_levels": {"VCC": voltage, "GND": 0.0},
            "current_per_component": {k: round(v, 4) for k, v in current_per_component.items()},
            "efficiency_percent": round(efficiency, 1),
            "power_dissipation_mw": round(power_dissipation, 2)
        }
        
        return SimulationResult(
            simulation_id=sim_id,
            simulation_type=SimulationType.POWER_ANALYSIS,
            status=SimulationStatus.COMPLETED,
            schematic_id=schematic.schematic_id,
            results=results,
            warnings=warnings,
            recommendations=recommendations
        )

    def _run_signal_integrity(self, schematic: Schematic, sim_id: str) -> SimulationResult:
        """Run signal integrity analysis."""
        warnings = []
        recommendations = []
        
        # Analyze signal nets
        signal_nets = [n for n in schematic.nets if n.net_type == NetType.SIGNAL]
        
        # Simplified signal integrity metrics
        # In a real implementation, this would use SPICE simulation
        rise_time = 2.5  # ns
        fall_time = 2.5  # ns
        overshoot = 5.0  # %
        undershoot = 3.0  # %
        crosstalk = -40.0  # dB
        impedance = 50.0  # ohms
        
        # Check for high-speed signals
        features = schematic.metadata.get("features", [])
        if "usb" in features:
            recommendations.append("Use differential pair routing for USB signals")
            recommendations.append("Maintain 90 ohm differential impedance for USB")
        
        if "wifi" in features or "bluetooth" in features:
            recommendations.append("Keep RF traces short and use proper ground plane")
            warnings.append("Ensure proper antenna matching network")
        
        # Check trace count for crosstalk concerns
        if len(signal_nets) > 10:
            warnings.append("Multiple signal traces may cause crosstalk")
            recommendations.append("Increase spacing between high-speed traces")
        
        results = {
            "rise_time_ns": rise_time,
            "fall_time_ns": fall_time,
            "overshoot_percent": overshoot,
            "undershoot_percent": undershoot,
            "crosstalk_db": crosstalk,
            "impedance_ohms": impedance,
            "signal_net_count": len(signal_nets)
        }
        
        return SimulationResult(
            simulation_id=sim_id,
            simulation_type=SimulationType.SIGNAL_INTEGRITY,
            status=SimulationStatus.COMPLETED,
            schematic_id=schematic.schematic_id,
            results=results,
            warnings=warnings,
            recommendations=recommendations
        )

    def _run_thermal_analysis(self, schematic: Schematic, sim_id: str) -> SimulationResult:
        """Run thermal analysis."""
        warnings = []
        recommendations = []
        hot_spots: list[tuple[str, float]] = []
        
        ambient_temp = 25.0  # degrees C
        
        # Calculate temperature rise for each component
        for component in schematic.components:
            power = self.COMPONENT_POWER.get(component.component_type, 1.0) / 1000  # Convert to W
            thermal_r = self.THERMAL_RESISTANCE.get(component.footprint, 100.0)
            
            temp_rise = power * thermal_r
            comp_temp = ambient_temp + temp_rise
            
            if comp_temp > 60:
                hot_spots.append((component.reference, round(comp_temp, 1)))
            
            if comp_temp > 85:
                warnings.append(f"Component {component.reference} may overheat ({comp_temp:.1f}°C)")
        
        # Sort hot spots by temperature
        hot_spots.sort(key=lambda x: x[1], reverse=True)
        
        # Calculate overall thermal metrics
        if hot_spots:
            max_temp = max(t for _, t in hot_spots)
            min_temp = min(t for _, t in hot_spots)
            avg_temp = sum(t for _, t in hot_spots) / len(hot_spots)
            thermal_gradient = max_temp - min_temp
        else:
            max_temp = ambient_temp
            min_temp = ambient_temp
            avg_temp = ambient_temp
            thermal_gradient = 0
        
        if thermal_gradient > 30:
            recommendations.append("Consider better thermal management or heatsinks")
        
        if max_temp > 70:
            recommendations.append("Add thermal vias under high-power components")
            recommendations.append("Use copper pour for heat dissipation")
        
        results = {
            "max_temperature_c": round(max_temp, 1),
            "min_temperature_c": round(min_temp, 1),
            "average_temperature_c": round(avg_temp, 1),
            "hot_spots": hot_spots[:5],  # Top 5 hottest components
            "thermal_gradient_c": round(thermal_gradient, 1),
            "ambient_temperature_c": ambient_temp
        }
        
        return SimulationResult(
            simulation_id=sim_id,
            simulation_type=SimulationType.THERMAL,
            status=SimulationStatus.COMPLETED,
            schematic_id=schematic.schematic_id,
            results=results,
            warnings=warnings,
            recommendations=recommendations
        )

    def _run_timing_analysis(self, schematic: Schematic, sim_id: str) -> SimulationResult:
        """Run timing analysis."""
        warnings = []
        recommendations = []
        
        # Find crystal/oscillator components for clock analysis
        crystals = [c for c in schematic.components if c.component_type == "crystal"]
        
        clock_freq = 0.0
        if crystals:
            # Try to parse clock frequency from value
            for crystal in crystals:
                if crystal.value:
                    try:
                        # Parse values like "16MHz" or "8M"
                        value = crystal.value.upper().replace("MHZ", "").replace("M", "")
                        clock_freq = float(value) * 1e6
                    except ValueError:
                        clock_freq = 8e6  # Default to 8MHz
        else:
            # Estimate based on board type
            board_type = schematic.metadata.get("board_type", "generic")
            if board_type == "esp32":
                clock_freq = 240e6  # 240MHz
            elif board_type == "arduino":
                clock_freq = 16e6  # 16MHz
            else:
                clock_freq = 8e6  # Default 8MHz
        
        # Calculate timing parameters
        clock_period_ns = (1 / clock_freq) * 1e9 if clock_freq > 0 else 0
        setup_time_ns = clock_period_ns * 0.1  # 10% of period
        hold_time_ns = clock_period_ns * 0.05  # 5% of period
        
        # Check for timing issues
        if clock_freq > 100e6:
            recommendations.append("Use low-ESR capacitors for power decoupling")
            recommendations.append("Ensure short clock traces with controlled impedance")
        
        results = {
            "clock_frequency_mhz": round(clock_freq / 1e6, 2),
            "clock_period_ns": round(clock_period_ns, 2),
            "setup_time_ns": round(setup_time_ns, 3),
            "hold_time_ns": round(hold_time_ns, 3),
            "crystal_count": len(crystals)
        }
        
        return SimulationResult(
            simulation_id=sim_id,
            simulation_type=SimulationType.TIMING,
            status=SimulationStatus.COMPLETED,
            schematic_id=schematic.schematic_id,
            results=results,
            warnings=warnings,
            recommendations=recommendations
        )

    def _run_emc_analysis(self, schematic: Schematic, sim_id: str) -> SimulationResult:
        """Run electromagnetic compatibility (EMC) analysis."""
        warnings = []
        recommendations = []
        
        features = schematic.metadata.get("features", [])
        
        # EMC risk score (0-100)
        emc_risk = 20  # Base risk
        
        # Wireless features increase EMC concerns
        if "wifi" in features:
            emc_risk += 20
            recommendations.append("Use shielded RF module or add EMI shielding")
        
        if "bluetooth" in features:
            emc_risk += 15
            recommendations.append("Maintain clear antenna keep-out zone")
        
        # High-speed interfaces increase emissions
        if "usb" in features:
            emc_risk += 10
            recommendations.append("Add common-mode chokes on USB lines")
        
        if "ethernet" in features:
            emc_risk += 15
            recommendations.append("Use magnetics with integrated common-mode filtering")
        
        # Power circuitry considerations
        if "battery" in features:
            recommendations.append("Add input filtering on battery charging circuit")
        
        # General recommendations
        if emc_risk > 30:
            recommendations.append("Use 4-layer PCB with dedicated ground plane")
            recommendations.append("Add ferrite beads on power inputs")
        
        if emc_risk > 50:
            warnings.append("High EMC risk - consider EMC testing early in development")
        
        results = {
            "emc_risk_score": min(emc_risk, 100),
            "risk_level": "low" if emc_risk < 30 else "medium" if emc_risk < 60 else "high",
            "rf_features": [f for f in features if f in ["wifi", "bluetooth", "lora"]],
            "high_speed_interfaces": [f for f in features if f in ["usb", "ethernet"]]
        }
        
        return SimulationResult(
            simulation_id=sim_id,
            simulation_type=SimulationType.EMC,
            status=SimulationStatus.COMPLETED,
            schematic_id=schematic.schematic_id,
            results=results,
            warnings=warnings,
            recommendations=recommendations
        )
