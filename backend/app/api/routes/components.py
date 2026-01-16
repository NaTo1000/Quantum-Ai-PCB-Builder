"""API routes for components and BOM."""

from fastapi import APIRouter, HTTPException

from app.schemas.components import (
    BOMResponse,
    ComponentDrawingRequest,
    ComponentDrawingResponse,
    ComponentSpec,
)
from app.services.component_service import component_service
from app.services.schematic_service import schematic_service

router = APIRouter()


@router.post("/bom/{schematic_id}", response_model=BOMResponse)
async def generate_bom(schematic_id: str) -> BOMResponse:
    """
    Generate Bill of Materials for a schematic.

    This endpoint generates a complete BOM with component specifications,
    quantities, and estimated pricing.

    Args:
        schematic_id: The unique identifier of the schematic

    Returns:
        BOMResponse with component list and pricing
    """
    schematic = schematic_service.get_schematic(schematic_id)

    if not schematic:
        raise HTTPException(status_code=404, detail="Schematic not found")

    bom = await component_service.generate_bom(schematic)
    return bom


@router.post("/drawing", response_model=ComponentDrawingResponse)
async def generate_component_drawing(
    request: ComponentDrawingRequest,
) -> ComponentDrawingResponse:
    """
    Generate component-level drawing in SVG format.

    This endpoint auto-generates component drawings to spec with SVG previews.

    Args:
        request: ComponentDrawingRequest with component_id

    Returns:
        ComponentDrawingResponse with SVG data
    """
    drawing = await component_service.generate_drawing(
        component_id=request.component_id,
        output_format=request.output_format,
    )
    return drawing


@router.get("/{component_id}", response_model=ComponentSpec)
async def get_component(component_id: str) -> ComponentSpec:
    """
    Get component specification by ID.

    Args:
        component_id: The unique identifier of the component

    Returns:
        ComponentSpec with component details
    """
    spec = component_service.get_component_spec(component_id)

    if not spec:
        raise HTTPException(status_code=404, detail="Component not found")

    return spec
