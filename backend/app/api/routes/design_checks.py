"""API routes for design checks."""

from fastapi import APIRouter, HTTPException

from app.schemas.design_checks import DesignCheckRequest, DesignCheckResponse
from app.services.design_checks_service import design_checks_service
from app.services.schematic_service import schematic_service

router = APIRouter()


@router.post("/run", response_model=DesignCheckResponse)
async def run_design_checks(request: DesignCheckRequest) -> DesignCheckResponse:
    """
    Run design checks on a schematic.

    This endpoint runs automated design checks including DRC (Design Rule Check),
    LVS (Layout vs Schematic), thermal analysis, and signal integrity checks.

    Args:
        request: DesignCheckRequest with schematic_id and check types

    Returns:
        DesignCheckResponse with violations and pass/fail status
    """
    schematic = schematic_service.get_schematic(request.schematic_id)

    if not schematic:
        raise HTTPException(status_code=404, detail="Schematic not found")

    result = await design_checks_service.run_checks(
        schematic=schematic,
        check_types=request.check_types,
    )

    return result


@router.get("/{schematic_id}", response_model=DesignCheckResponse)
async def get_check_results(schematic_id: str) -> DesignCheckResponse:
    """
    Get previous design check results for a schematic.

    Args:
        schematic_id: The unique identifier of the schematic

    Returns:
        DesignCheckResponse with the check results
    """
    result = design_checks_service.get_result(schematic_id)

    if not result:
        raise HTTPException(status_code=404, detail="Check results not found")

    return result
