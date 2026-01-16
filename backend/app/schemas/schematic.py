"""Schemas for schematic generation."""

from typing import Optional
from pydantic import BaseModel


class SchematicPrompt(BaseModel):
    """Input schema for generating schematics from natural language."""

    prompt: str
    design_type: str = "pcb"  # pcb, chip, analog, digital
    output_format: str = "rtl"  # rtl, analog, mixed-signal


class Component(BaseModel):
    """Schema for a single component in a schematic."""

    id: str
    name: str
    type: str
    value: Optional[str] = None
    package: Optional[str] = None
    pins: list[dict] = []
    position: dict = {"x": 0, "y": 0}


class Net(BaseModel):
    """Schema for a net connecting components."""

    id: str
    name: str
    source: dict
    destination: dict
    net_class: str = "signal"


class SchematicResponse(BaseModel):
    """Response schema for generated schematic."""

    id: str
    components: list[Component]
    nets: list[Net]
    metadata: dict = {}
    svg_preview: Optional[str] = None
    confidence_score: float = 0.0
