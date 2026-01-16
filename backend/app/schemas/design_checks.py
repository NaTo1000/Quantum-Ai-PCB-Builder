"""Schemas for design checks."""

from typing import Optional
from pydantic import BaseModel


class DesignCheckRequest(BaseModel):
    """Input schema for running design checks."""

    schematic_id: str
    check_types: list[str] = ["drc", "lvs", "thermal", "signal_integrity"]


class CheckViolation(BaseModel):
    """Schema for a design check violation."""

    id: str
    check_type: str
    severity: str  # error, warning, info
    message: str
    location: Optional[dict] = None
    component_id: Optional[str] = None


class DesignCheckResponse(BaseModel):
    """Response schema for design checks."""

    schematic_id: str
    passed: bool
    violations: list[CheckViolation] = []
    drc_passed: bool = True
    lvs_passed: bool = True
    thermal_passed: bool = True
    signal_integrity_passed: bool = True
    summary: dict = {}
