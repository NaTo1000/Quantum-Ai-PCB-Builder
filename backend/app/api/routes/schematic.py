"""API routes for schematic generation."""

from fastapi import APIRouter, HTTPException

from app.schemas.schematic import SchematicPrompt, SchematicResponse
from app.services.schematic_service import schematic_service

router = APIRouter()


@router.post("/generate", response_model=SchematicResponse)
async def generate_schematic(request: SchematicPrompt) -> SchematicResponse:
    """
    Generate a schematic from a natural language prompt.

    This endpoint accepts a natural language description of a desired chip or board
    and generates architecture, RTL, or analog schematics in real time.

    Args:
        request: SchematicPrompt with the design description

    Returns:
        SchematicResponse with generated components, nets, and SVG preview
    """
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    schematic = await schematic_service.generate_from_prompt(
        prompt=request.prompt,
        design_type=request.design_type,
        output_format=request.output_format,
    )

    return schematic


@router.get("/{schematic_id}", response_model=SchematicResponse)
async def get_schematic(schematic_id: str) -> SchematicResponse:
    """
    Get a previously generated schematic by ID.

    Args:
        schematic_id: The unique identifier of the schematic

    Returns:
        SchematicResponse with the schematic details
    """
    schematic = schematic_service.get_schematic(schematic_id)

    if not schematic:
        raise HTTPException(status_code=404, detail="Schematic not found")

    return schematic
