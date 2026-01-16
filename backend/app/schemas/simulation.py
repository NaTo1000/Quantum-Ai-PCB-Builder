"""Schemas for simulation."""

from typing import Optional
from pydantic import BaseModel


class SimulationRequest(BaseModel):
    """Input schema for running simulations."""

    schematic_id: str
    simulation_type: str = "spice"  # spice, timing, power
    parameters: dict = {}


class SimulationResult(BaseModel):
    """Schema for simulation results."""

    id: str
    simulation_type: str
    status: str  # running, completed, failed
    data: dict = {}
    waveforms: list[dict] = []
    timing_report: Optional[dict] = None
    power_report: Optional[dict] = None
    confidence_score: float = 0.0


class SimulationResponse(BaseModel):
    """Response schema for simulations."""

    schematic_id: str
    simulation_id: str
    result: SimulationResult
    visual_feedback: Optional[str] = None
