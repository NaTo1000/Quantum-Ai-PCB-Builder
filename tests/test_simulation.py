"""
Tests for the Simulation Engine module.
"""

import pytest
from src.core.nlp.intent_parser import IntentParser
from src.core.design.schematic_generator import SchematicGenerator
from src.core.simulation.engine import (
    SimulationEngine, SimulationResult, SimulationType, SimulationStatus
)


class TestSimulationEngine:
    """Test suite for the SimulationEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create a SimulationEngine instance for testing."""
        return SimulationEngine()
    
    @pytest.fixture
    def schematic(self):
        """Create a test schematic."""
        parser = IntentParser()
        generator = SchematicGenerator()
        
        prompt = "ESP32 board with WiFi, battery, and temperature sensor"
        design_intent = parser.parse(prompt)
        return generator.generate(design_intent)
    
    def test_run_power_analysis(self, engine, schematic):
        """Test running power analysis simulation."""
        result = engine.run_simulation(schematic, SimulationType.POWER_ANALYSIS)
        
        assert isinstance(result, SimulationResult)
        assert result.simulation_type == SimulationType.POWER_ANALYSIS
        assert result.status == SimulationStatus.COMPLETED
        assert "total_power_consumption_mw" in result.results
    
    def test_run_signal_integrity(self, engine, schematic):
        """Test running signal integrity simulation."""
        result = engine.run_simulation(schematic, SimulationType.SIGNAL_INTEGRITY)
        
        assert result.simulation_type == SimulationType.SIGNAL_INTEGRITY
        assert result.status == SimulationStatus.COMPLETED
        assert "rise_time_ns" in result.results
        assert "impedance_ohms" in result.results
    
    def test_run_thermal_analysis(self, engine, schematic):
        """Test running thermal analysis simulation."""
        result = engine.run_simulation(schematic, SimulationType.THERMAL)
        
        assert result.simulation_type == SimulationType.THERMAL
        assert result.status == SimulationStatus.COMPLETED
        assert "max_temperature_c" in result.results
        assert "hot_spots" in result.results
    
    def test_run_timing_analysis(self, engine, schematic):
        """Test running timing analysis simulation."""
        result = engine.run_simulation(schematic, SimulationType.TIMING)
        
        assert result.simulation_type == SimulationType.TIMING
        assert result.status == SimulationStatus.COMPLETED
        assert "clock_frequency_mhz" in result.results
    
    def test_run_emc_analysis(self, engine, schematic):
        """Test running EMC analysis simulation."""
        result = engine.run_simulation(schematic, SimulationType.EMC)
        
        assert result.simulation_type == SimulationType.EMC
        assert result.status == SimulationStatus.COMPLETED
        assert "emc_risk_score" in result.results
        assert "risk_level" in result.results
    
    def test_run_all_simulations(self, engine, schematic):
        """Test running all simulations at once."""
        results = engine.run_all_simulations(schematic)
        
        assert len(results) == len(SimulationType)
        for result in results:
            assert isinstance(result, SimulationResult)
            assert result.status == SimulationStatus.COMPLETED
    
    def test_simulation_generates_recommendations(self, engine, schematic):
        """Test that simulations generate recommendations."""
        result = engine.run_simulation(schematic, SimulationType.POWER_ANALYSIS)
        
        # Results should have recommendations list
        assert "recommendations" in result.__dict__
        assert isinstance(result.recommendations, list)
    
    def test_simulation_result_to_dict(self, engine, schematic):
        """Test SimulationResult conversion to dictionary."""
        result = engine.run_simulation(schematic, SimulationType.POWER_ANALYSIS)
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert "simulation_id" in result_dict
        assert "type" in result_dict
        assert "status" in result_dict
        assert "results" in result_dict
    
    def test_simulation_ids_unique(self, engine, schematic):
        """Test that simulation IDs are unique."""
        results = engine.run_all_simulations(schematic)
        
        sim_ids = [r.simulation_id for r in results]
        assert len(sim_ids) == len(set(sim_ids))
    
    def test_power_analysis_values_reasonable(self, engine, schematic):
        """Test that power analysis values are reasonable."""
        result = engine.run_simulation(schematic, SimulationType.POWER_ANALYSIS)
        
        power = result.results["total_power_consumption_mw"]
        efficiency = result.results["efficiency_percent"]
        
        assert power >= 0
        assert 0 <= efficiency <= 100
    
    def test_thermal_temperatures_reasonable(self, engine, schematic):
        """Test that thermal simulation temperatures are reasonable."""
        result = engine.run_simulation(schematic, SimulationType.THERMAL)
        
        max_temp = result.results["max_temperature_c"]
        min_temp = result.results["min_temperature_c"]
        ambient = result.results["ambient_temperature_c"]
        
        assert min_temp >= ambient
        assert max_temp >= min_temp
    
    def test_emc_risk_score_bounded(self, engine, schematic):
        """Test that EMC risk score is properly bounded."""
        result = engine.run_simulation(schematic, SimulationType.EMC)
        
        risk_score = result.results["emc_risk_score"]
        risk_level = result.results["risk_level"]
        
        assert 0 <= risk_score <= 100
        assert risk_level in ["low", "medium", "high"]
