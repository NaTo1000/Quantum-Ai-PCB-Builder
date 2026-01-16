"""
Data models for the Quantum-Ai-PCB-Builder API.
"""

from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class DesignStatus(str, Enum):
    """Status of a design job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DesignRequest(BaseModel):
    """Request model for creating a new design."""
    description: str
    design_type: str = "pcb"
    parameters: Optional[dict] = None


class DesignResponse(BaseModel):
    """Response model for a design job."""
    id: str
    status: DesignStatus
    description: str
    schematic_url: Optional[str] = None
    simulation_results: Optional[dict] = None
    vendor_matches: Optional[List[dict]] = None


class SimulationResult(BaseModel):
    """Model for simulation results."""
    success: bool
    metrics: dict
    warnings: Optional[List[str]] = None
    errors: Optional[List[str]] = None


class VendorMatch(BaseModel):
    """Model for vendor matching results."""
    vendor_name: str
    price_estimate: float
    lead_time_days: int
    capabilities: List[str]
