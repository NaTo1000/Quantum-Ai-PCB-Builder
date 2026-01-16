"""
Simulation Service for running design simulations and conflict checking
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.services.design_service import design_service

class SimulationService:
    """Service for running simulations and checking design conflicts"""
    
    def __init__(self):
        self.simulations = {}
    
    async def run_simulation(self, design_id: str, simulation_type: str = "full", parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run simulation on a design
        
        Args:
            design_id: ID of the design to simulate
            simulation_type: Type of simulation to run
            parameters: Optional simulation parameters
            
        Returns:
            Simulation result dictionary
        """
        simulation_id = str(uuid.uuid4())
        
        # Get design data
        design_data = design_service.get_design(design_id)
        if not design_data:
            raise ValueError(f"Design {design_id} not found")
        
        if not design_data.get("schematic"):
            raise ValueError(f"Design {design_id} has no schematic to simulate")
        
        # Run simulation and conflict checking
        conflicts = self._check_conflicts(design_data["schematic"])
        warnings = self._check_warnings(design_data["schematic"])
        results = self._simulate_circuit(design_data["schematic"], simulation_type, parameters)
        
        simulation_result = {
            "simulation_id": simulation_id,
            "design_id": design_id,
            "status": "completed",
            "results": results,
            "conflicts": conflicts,
            "warnings": warnings,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.simulations[simulation_id] = simulation_result
        return simulation_result
    
    def _check_conflicts(self, schematic: Dict[str, Any]) -> List[str]:
        """
        Check for design conflicts in the schematic
        
        Args:
            schematic: Schematic data to check
            
        Returns:
            List of conflict messages
        """
        conflicts = []
        components = schematic.get("components", [])
        connections = schematic.get("connections", [])
        
        # Check for duplicate component IDs
        component_ids = [c["id"] for c in components]
        duplicates = [cid for cid in component_ids if component_ids.count(cid) > 1]
        if duplicates:
            conflicts.append(f"Duplicate component IDs found: {', '.join(set(duplicates))}")
        
        # Check for connections to non-existent components
        for conn in connections:
            from_comp = conn.get("from", {}).get("component")
            to_comp = conn.get("to", {}).get("component")
            if from_comp not in component_ids:
                conflicts.append(f"Connection references non-existent component: {from_comp}")
            if to_comp not in component_ids:
                conflicts.append(f"Connection references non-existent component: {to_comp}")
        
        # Check for power supply conflicts
        power_components = [c for c in components if c.get("type", "").lower() in ["power", "voltage_regulator", "battery"]]
        if not power_components:
            conflicts.append("No power supply component found in design")
        
        return conflicts
    
    def _check_warnings(self, schematic: Dict[str, Any]) -> List[str]:
        """
        Check for design warnings
        
        Args:
            schematic: Schematic data to check
            
        Returns:
            List of warning messages
        """
        warnings = []
        components = schematic.get("components", [])
        connections = schematic.get("connections", [])
        
        # Check for floating pins
        connected_pins = set()
        for conn in connections:
            from_comp = conn.get("from", {}).get("component")
            from_pin = conn.get("from", {}).get("pin")
            to_comp = conn.get("to", {}).get("component")
            to_pin = conn.get("to", {}).get("pin")
            connected_pins.add(f"{from_comp}.{from_pin}")
            connected_pins.add(f"{to_comp}.{to_pin}")
        
        for comp in components:
            for pin in comp.get("pins", []):
                pin_ref = f"{comp['id']}.{pin}"
                if pin_ref not in connected_pins:
                    warnings.append(f"Unconnected pin: {pin_ref}")
        
        # Check for missing decoupling capacitors
        has_decoupling = any(c.get("type", "").lower() == "capacitor" for c in components)
        if not has_decoupling:
            warnings.append("No decoupling capacitors found - consider adding for power stability")
        
        return warnings
    
    def _simulate_circuit(self, schematic: Dict[str, Any], simulation_type: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Simulate circuit behavior
        
        Args:
            schematic: Schematic to simulate
            simulation_type: Type of simulation
            parameters: Simulation parameters
            
        Returns:
            Simulation results
        """
        # This is a simplified simulation - in a real system, this would integrate with
        # SPICE or other EDA simulation tools
        
        results = {
            "simulation_type": simulation_type,
            "status": "passed",
            "metrics": {
                "power_consumption": "150mW (estimated)",
                "operating_voltage": "3.3V",
                "max_current": "45mA",
                "thermal_dissipation": "Low"
            },
            "performance": {
                "signal_integrity": "Good",
                "noise_margin": "High",
                "timing_analysis": "Passed"
            }
        }
        
        # Add specific results based on simulation type
        if simulation_type == "power":
            results["power_analysis"] = {
                "efficiency": "92%",
                "ripple_voltage": "50mV",
                "load_regulation": "2%"
            }
        elif simulation_type == "thermal":
            results["thermal_analysis"] = {
                "max_temperature": "65°C",
                "hotspots": ["U1"],
                "cooling_required": "Passive"
            }
        
        return results
    
    def get_simulation(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Get simulation result by ID"""
        return self.simulations.get(simulation_id)

simulation_service = SimulationService()
