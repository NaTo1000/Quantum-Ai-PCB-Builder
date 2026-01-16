"""API routes for simulations."""

from fastapi import APIRouter, HTTPException

from app.schemas.simulation import SimulationRequest, SimulationResponse
from app.services.simulation_service import simulation_service
from app.services.schematic_service import schematic_service

router = APIRouter()


@router.post("/run", response_model=SimulationResponse)
async def run_simulation(request: SimulationRequest) -> SimulationResponse:
    """
    Run a simulation on a schematic.

    This endpoint runs SPICE, timing, or power simulations on a schematic
    with confidence scoring and visual feedback.

    Args:
        request: SimulationRequest with schematic_id and simulation type

    Returns:
        SimulationResponse with results and waveforms
    """
    schematic = schematic_service.get_schematic(request.schematic_id)

    if not schematic:
        raise HTTPException(status_code=404, detail="Schematic not found")

    result = await simulation_service.run_simulation(
        schematic=schematic,
        simulation_type=request.simulation_type,
        parameters=request.parameters,
    )

    return result


@router.get("/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(simulation_id: str) -> SimulationResponse:
    """
    Get simulation results by ID.

    Args:
        simulation_id: The unique identifier of the simulation

    Returns:
        SimulationResponse with the simulation results
    """
    result = simulation_service.get_simulation(simulation_id)

    if not result:
        raise HTTPException(status_code=404, detail="Simulation not found")

    return result
