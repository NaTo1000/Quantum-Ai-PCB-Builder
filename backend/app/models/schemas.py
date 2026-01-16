"""
Pydantic models for API request/response schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DesignType(str, Enum):
    """Type of PCB design"""
    PCB = "pcb"
    CHIP = "chip"
    ESP32 = "esp32"
    LORA = "lora"
    CUSTOM = "custom"

class DesignStatus(str, Enum):
    """Status of design processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DesignRequest(BaseModel):
    """Request model for creating a new design"""
    description: str = Field(..., description="Natural language description of the desired hardware")
    design_type: DesignType = Field(default=DesignType.PCB, description="Type of design to create")
    constraints: Optional[Dict[str, Any]] = Field(default=None, description="Design constraints and requirements")
    code_input: Optional[str] = Field(default=None, description="Optional code-based design specification")

class DesignResponse(BaseModel):
    """Response model for design creation"""
    design_id: str
    status: DesignStatus
    message: str
    created_at: datetime

class SchematicData(BaseModel):
    """Schematic information"""
    components: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]
    layout: Optional[str] = None

class DesignDetail(BaseModel):
    """Detailed design information"""
    design_id: str
    description: str
    design_type: DesignType
    status: DesignStatus
    schematic: Optional[SchematicData] = None
    created_at: datetime
    updated_at: datetime

class SimulationRequest(BaseModel):
    """Request model for running simulation"""
    design_id: str
    simulation_type: str = Field(default="full", description="Type of simulation to run")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Simulation parameters")

class SimulationResult(BaseModel):
    """Simulation result model"""
    simulation_id: str
    design_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    conflicts: List[str] = []
    warnings: List[str] = []
    timestamp: datetime

class VendorRequest(BaseModel):
    """Request model for vendor matching"""
    design_id: str
    quantity: int = Field(default=100, description="Number of units to manufacture")
    requirements: Optional[Dict[str, Any]] = Field(default=None, description="Manufacturing requirements")

class VendorInfo(BaseModel):
    """Vendor information"""
    vendor_id: str
    name: str
    price_per_unit: float
    lead_time_days: int
    capabilities: List[str]
    rating: float

class VendorMatchResponse(BaseModel):
    """Response model for vendor matching"""
    design_id: str
    vendors: List[VendorInfo]
    recommended_vendor: Optional[VendorInfo] = None
