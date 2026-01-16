"""Schemas for components and BOM."""

from typing import Optional
from pydantic import BaseModel


class ComponentSpec(BaseModel):
    """Schema for component specification."""

    id: str
    name: str
    type: str
    manufacturer: Optional[str] = None
    part_number: Optional[str] = None
    description: Optional[str] = None
    datasheet_url: Optional[str] = None
    footprint: Optional[str] = None


class BOMItem(BaseModel):
    """Schema for a Bill of Materials item."""

    component_id: str
    quantity: int
    reference_designators: list[str]
    component_spec: ComponentSpec
    unit_price: Optional[float] = None
    total_price: Optional[float] = None


class BOMResponse(BaseModel):
    """Response schema for Bill of Materials."""

    schematic_id: str
    items: list[BOMItem]
    total_components: int
    estimated_cost: Optional[float] = None


class ComponentDrawingRequest(BaseModel):
    """Request schema for component drawing generation."""

    component_id: str
    output_format: str = "svg"


class ComponentDrawingResponse(BaseModel):
    """Response schema for component drawing."""

    component_id: str
    svg_data: str
    width: int
    height: int
