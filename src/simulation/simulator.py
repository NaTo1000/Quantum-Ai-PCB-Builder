"""Simulation engine interface for SPICE and timing analysis.

This module provides interfaces for running simulations on
generated netlists and behavioral models.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SimulationType(Enum):
    """Types of simulations."""

    TRANSIENT = "transient"
    DC = "dc"
    AC = "ac"
    NOISE = "noise"
    TIMING = "timing"
    POWER = "power"


@dataclass
class SimulationConfig:
    """Configuration for a simulation run."""

    sim_type: SimulationType
    duration: Optional[float] = None
    step_size: Optional[float] = None
    temperature: float = 27.0
    process_corner: str = "typical"
    parameters: dict = field(default_factory=dict)


@dataclass
class SimulationResult:
    """Result of a simulation run."""

    success: bool
    sim_type: SimulationType
    data: dict
    metrics: dict
    confidence_score: float = 0.0
    error_message: str = ""
    runtime_seconds: float = 0.0


class Simulator(ABC):
    """Abstract base class for simulation engines."""

    @abstractmethod
    def run(self, netlist: str, config: SimulationConfig) -> SimulationResult:
        """Run a simulation.

        Args:
            netlist: The netlist or model to simulate.
            config: Simulation configuration.

        Returns:
            SimulationResult with output data.
        """
        pass

    @abstractmethod
    def get_backend_name(self) -> str:
        """Return the name of the simulation backend."""
        pass


class SpiceSimulator(Simulator):
    """SPICE simulation engine.

    Supports ngspice, Xyce, and commercial SPICE backends.
    """

    def __init__(self, backend: str = "ngspice"):
        """Initialize the SPICE simulator.

        Args:
            backend: SPICE backend to use ("ngspice", "xyce", "hspice").
        """
        self.backend = backend

    def run(self, netlist: str, config: SimulationConfig) -> SimulationResult:
        """Run a SPICE simulation.

        Args:
            netlist: SPICE netlist to simulate.
            config: Simulation configuration.

        Returns:
            SimulationResult with waveform data.

        Note: This is a stub implementation.
        """
        # Stub implementation
        return SimulationResult(
            success=True,
            sim_type=config.sim_type,
            data={"waveforms": {}, "nodes": []},
            metrics={
                "peak_current": 0.0,
                "average_power": 0.0,
                "settling_time": 0.0,
            },
            confidence_score=0.85,
            runtime_seconds=0.0,
        )

    def get_backend_name(self) -> str:
        """Return the SPICE backend name."""
        return self.backend


class TimingSimulator(Simulator):
    """Static Timing Analysis (STA) engine.

    Supports OpenSTA and commercial timing tools.
    """

    def __init__(self, backend: str = "opensta"):
        """Initialize the timing simulator.

        Args:
            backend: Timing backend to use ("opensta", "primetime").
        """
        self.backend = backend

    def run(self, netlist: str, config: SimulationConfig) -> SimulationResult:
        """Run static timing analysis.

        Args:
            netlist: Verilog or gate-level netlist.
            config: Simulation configuration.

        Returns:
            SimulationResult with timing data.

        Note: This is a stub implementation.
        """
        # Stub implementation
        return SimulationResult(
            success=True,
            sim_type=SimulationType.TIMING,
            data={
                "critical_paths": [],
                "slack": {},
                "setup_violations": [],
                "hold_violations": [],
            },
            metrics={
                "worst_negative_slack": 0.0,
                "total_negative_slack": 0.0,
                "max_frequency_mhz": 1000.0,
            },
            confidence_score=0.90,
            runtime_seconds=0.0,
        )

    def get_backend_name(self) -> str:
        """Return the timing backend name."""
        return self.backend
