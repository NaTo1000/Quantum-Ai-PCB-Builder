"""API routes for vendor matching and quoting."""

from typing import Optional

from fastapi import APIRouter, HTTPException

from app.schemas.vendors import Vendor, VendorMatchRequest, VendorMatchResponse
from app.services.vendor_service import vendor_service
from app.services.schematic_service import schematic_service

router = APIRouter()


@router.post("/match", response_model=VendorMatchResponse)
async def match_vendors(request: VendorMatchRequest) -> VendorMatchResponse:
    """
    Match vendors for a schematic based on requirements.

    This endpoint suggests compatible foundries, packaging houses, and PCB assemblers
    with estimated price-per-unit and delivery timelines.

    Args:
        request: VendorMatchRequest with schematic_id and preferences

    Returns:
        VendorMatchResponse with matched vendors and quotes
    """
    schematic = schematic_service.get_schematic(request.schematic_id)

    if not schematic:
        raise HTTPException(status_code=404, detail="Schematic not found")

    result = await vendor_service.match_vendors(
        schematic=schematic,
        quantity=request.quantity,
        preferred_locations=request.preferred_locations,
        max_lead_time_days=request.max_lead_time_days,
    )

    return result


@router.get("/", response_model=list[Vendor])
async def list_vendors(vendor_type: Optional[str] = None) -> list[Vendor]:
    """
    List available vendors.

    Args:
        vendor_type: Optional filter by vendor type (foundry, assembler, packaging)

    Returns:
        List of vendors
    """
    return vendor_service.list_vendors(vendor_type)


@router.get("/{vendor_id}", response_model=Vendor)
async def get_vendor(vendor_id: str) -> Vendor:
    """
    Get vendor by ID.

    Args:
        vendor_id: The unique identifier of the vendor

    Returns:
        Vendor details
    """
    vendor = vendor_service.get_vendor(vendor_id)

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    return vendor
