"""Schemas for vendor matching and quoting."""

from typing import Optional
from pydantic import BaseModel


class Vendor(BaseModel):
    """Schema for a vendor."""

    id: str
    name: str
    type: str  # foundry, packaging, assembler
    capabilities: list[str] = []
    location: Optional[str] = None
    min_order_quantity: Optional[int] = None
    lead_time_days: Optional[int] = None


class Quote(BaseModel):
    """Schema for a vendor quote."""

    vendor_id: str
    vendor_name: str
    price_per_unit: float
    setup_cost: float
    lead_time_days: int
    minimum_quantity: int
    currency: str = "USD"


class VendorMatchRequest(BaseModel):
    """Request schema for vendor matching."""

    schematic_id: str
    quantity: int = 1000
    preferred_locations: list[str] = []
    max_lead_time_days: Optional[int] = None


class VendorMatchResponse(BaseModel):
    """Response schema for vendor matching."""

    schematic_id: str
    matched_vendors: list[Vendor]
    quotes: list[Quote]
    recommended_vendor_id: Optional[str] = None
    estimated_delivery_date: Optional[str] = None
