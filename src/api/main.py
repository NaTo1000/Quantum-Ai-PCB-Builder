"""
Main FastAPI Application

This module provides the REST API endpoints for the Quantum AI PCB Builder platform.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any

from ..core.nlp.intent_parser import IntentParser
from ..core.design.schematic_generator import (
    SchematicGenerator, Schematic, SchematicComponent, Net, Pin, PinType, NetType
)
from ..core.design.validator import DesignValidator
from ..core.simulation.engine import SimulationEngine, SimulationType
from ..core.fabrication.vendor import (
    VendorRegistry, QuoteEngine, OrderManager,
    PCBSpecification, VendorCapability
)


# Initialize FastAPI app
app = FastAPI(
    title="Quantum AI PCB Builder",
    description=(
        "AI-Orchestrated Chip and PCB Design Platform - "
        "Transform natural language into manufacturable schematics"
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
intent_parser = IntentParser()
schematic_generator = SchematicGenerator()
design_validator = DesignValidator()
simulation_engine = SimulationEngine()
vendor_registry = VendorRegistry()
quote_engine = QuoteEngine(vendor_registry)
order_manager = OrderManager()


def _reconstruct_schematic(schematic_dict: dict[str, Any]) -> Schematic:
    """
    Reconstruct a Schematic object from a dictionary representation.
    
    Args:
        schematic_dict: Dictionary containing schematic data.
        
    Returns:
        Reconstructed Schematic object.
    """
    components = []
    for c in schematic_dict.get("components", []):
        pins = [
            Pin(
                pin_id=p["id"],
                name=p["name"],
                pin_type=PinType(p["type"]),
                number=p["number"]
            )
            for p in c.get("pins", [])
        ]
        components.append(SchematicComponent(
            component_id=c["id"],
            reference=c["reference"],
            component_type=c["type"],
            value=c.get("value"),
            footprint=c["footprint"],
            pins=pins,
            position=tuple(c.get("position", [0, 0])),
            rotation=c.get("rotation", 0),
            properties=c.get("properties", {})
        ))
    
    nets = [
        Net(
            net_id=n["id"],
            name=n["name"],
            net_type=NetType(n["type"]),
            connections=[(conn[0], conn[1]) for conn in n["connections"]]
        )
        for n in schematic_dict.get("nets", [])
    ]
    
    return Schematic(
        schematic_id=schematic_dict["schematic_id"],
        name=schematic_dict["name"],
        version=schematic_dict["version"],
        components=components,
        nets=nets,
        metadata=schematic_dict.get("metadata", {})
    )


# Request/Response Models
class DesignRequest(BaseModel):
    """Request model for design generation from natural language."""
    prompt: str = Field(..., description="Natural language description of the design")
    run_validation: bool = Field(True, description="Whether to run design validation")
    run_simulation: bool = Field(False, description="Whether to run simulations")


class DesignResponse(BaseModel):
    """Response model for generated design."""
    design_intent: dict[str, Any]
    schematic: dict[str, Any]
    validation: dict[str, Any] | None = None
    simulations: list[dict[str, Any]] | None = None


class QuoteRequest(BaseModel):
    """Request model for fabrication quote."""
    width_mm: float = Field(..., description="Board width in mm")
    height_mm: float = Field(..., description="Board height in mm")
    layers: int = Field(2, description="Number of PCB layers")
    quantity: int = Field(10, description="Number of boards to manufacture")
    surface_finish: str = Field("HASL", description="Surface finish type")
    thickness_mm: float = Field(1.6, description="Board thickness in mm")


class QuoteResponse(BaseModel):
    """Response model for fabrication quotes."""
    quotes: list[dict[str, Any]]


class ValidationRequest(BaseModel):
    """Request model for design validation."""
    schematic: dict[str, Any]


class SimulationRequest(BaseModel):
    """Request model for simulation."""
    schematic: dict[str, Any]
    simulation_types: list[str] | None = None


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Quantum AI PCB Builder",
        "version": "0.1.0",
        "description": "AI-Orchestrated Chip and PCB Design Platform",
        "endpoints": {
            "design": "/api/v1/design",
            "validate": "/api/v1/validate",
            "simulate": "/api/v1/simulate",
            "vendors": "/api/v1/vendors",
            "quote": "/api/v1/quote"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "quantum-ai-pcb-builder"}


@app.post("/api/v1/design", response_model=DesignResponse)
async def generate_design(request: DesignRequest):
    """
    Generate a PCB/chip design from a natural language prompt.
    
    This endpoint:
    1. Parses the natural language prompt to extract design intent
    2. Generates a schematic based on the intent
    3. Optionally validates the design
    4. Optionally runs simulations
    """
    try:
        # Parse the natural language prompt
        design_intent = intent_parser.parse(request.prompt)
        
        # Generate schematic
        schematic = schematic_generator.generate(design_intent)
        
        response_data: dict[str, Any] = {
            "design_intent": design_intent.to_dict(),
            "schematic": schematic.to_dict()
        }
        
        # Run validation if requested
        if request.run_validation:
            validation_result = design_validator.validate(schematic)
            response_data["validation"] = validation_result.to_dict()
        
        # Run simulations if requested
        if request.run_simulation:
            sim_results = simulation_engine.run_all_simulations(schematic)
            response_data["simulations"] = [s.to_dict() for s in sim_results]
        
        return DesignResponse(**response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/parse")
async def parse_prompt(prompt: str):
    """
    Parse a natural language prompt without generating a full design.
    
    Useful for understanding what the system extracts from user input.
    """
    try:
        design_intent = intent_parser.parse(prompt)
        return design_intent.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/validate")
async def validate_design(request: ValidationRequest):
    """
    Validate an existing schematic design.
    
    Performs electrical rule checks (ERC) and design rule checks (DRC).
    """
    try:
        schematic = _reconstruct_schematic(request.schematic)
        validation_result = design_validator.validate(schematic)
        return validation_result.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/simulate")
async def run_simulation(request: SimulationRequest):
    """
    Run simulations on a schematic design.
    
    Available simulation types:
    - power_analysis: Analyze power consumption
    - signal_integrity: Analyze signal quality
    - thermal: Thermal analysis
    - timing: Timing analysis
    - emc: EMC/EMI analysis
    """
    try:
        schematic = _reconstruct_schematic(request.schematic)
        
        # Run requested simulations
        results = []
        sim_types = request.simulation_types
        
        if sim_types is None:
            # Run all simulations
            results = simulation_engine.run_all_simulations(schematic)
        else:
            for sim_type_str in sim_types:
                try:
                    sim_type = SimulationType(sim_type_str)
                    result = simulation_engine.run_simulation(schematic, sim_type)
                    results.append(result)
                except ValueError:
                    continue
        
        return {"simulations": [r.to_dict() for r in results]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/vendors")
async def list_vendors(
    capability: str | None = None,
    country: str | None = None,
    min_rating: float = 0.0
):
    """
    List available fabrication vendors.
    
    Optionally filter by capability, country, or minimum rating.
    """
    try:
        cap = VendorCapability(capability) if capability else None
        vendors = vendor_registry.list_vendors(
            capability=cap,
            country=country,
            min_rating=min_rating
        )
        return {"vendors": [v.to_dict() for v in vendors]}
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid capability: {capability}")


@app.get("/api/v1/vendors/{vendor_id}")
async def get_vendor(vendor_id: str):
    """Get detailed information about a specific vendor."""
    vendor = vendor_registry.get_vendor(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor.to_dict()


@app.post("/api/v1/quote", response_model=QuoteResponse)
async def get_quotes(request: QuoteRequest):
    """
    Get fabrication quotes from multiple vendors.
    
    Returns quotes sorted by total cost.
    """
    try:
        spec = PCBSpecification(
            board_size_mm=(request.width_mm, request.height_mm),
            layers=request.layers,
            quantity=request.quantity,
            surface_finish=request.surface_finish,
            thickness_mm=request.thickness_mm
        )
        
        quotes = quote_engine.compare_quotes(spec)
        return QuoteResponse(quotes=[q.to_dict() for q in quotes])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/quote/{vendor_id}")
async def get_vendor_quote(
    vendor_id: str,
    width_mm: float,
    height_mm: float,
    layers: int = 2,
    quantity: int = 10,
    surface_finish: str = "HASL"
):
    """Get a quote from a specific vendor."""
    try:
        spec = PCBSpecification(
            board_size_mm=(width_mm, height_mm),
            layers=layers,
            quantity=quantity,
            surface_finish=surface_finish
        )
        
        quote = quote_engine.generate_quote(vendor_id, spec)
        return quote.to_dict()
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run with: uvicorn src.api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
