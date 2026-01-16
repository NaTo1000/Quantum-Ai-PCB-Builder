"""
Simulation API endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import SimulationRequest, SimulationResult
from app.services.simulation_service import simulation_service
from datetime import datetime

router = APIRouter()

@router.post("/run", response_model=SimulationResult)
async def run_simulation(simulation_request: SimulationRequest, background_tasks: BackgroundTasks):
    """
    Run simulation on a design
    
    Args:
        simulation_request: Simulation request with design ID and parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        Simulation results including conflicts and warnings
    """
    try:
        result = await simulation_service.run_simulation(
            design_id=simulation_request.design_id,
            simulation_type=simulation_request.simulation_type,
            parameters=simulation_request.parameters
        )
        
        return SimulationResult(
            simulation_id=result["simulation_id"],
            design_id=result["design_id"],
            status=result["status"],
            results=result.get("results"),
            conflicts=result.get("conflicts", []),
            warnings=result.get("warnings", []),
            timestamp=datetime.fromisoformat(result["timestamp"])
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running simulation: {str(e)}")

@router.get("/{simulation_id}", response_model=SimulationResult)
async def get_simulation(simulation_id: str):
    """
    Get simulation results by ID
    
    Args:
        simulation_id: ID of the simulation
        
    Returns:
        Simulation results
    """
    result = simulation_service.get_simulation(simulation_id)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")
    
    return SimulationResult(
        simulation_id=result["simulation_id"],
        design_id=result["design_id"],
        status=result["status"],
        results=result.get("results"),
        conflicts=result.get("conflicts", []),
        warnings=result.get("warnings", []),
        timestamp=datetime.fromisoformat(result["timestamp"])
    )
