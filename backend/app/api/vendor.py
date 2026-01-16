"""
Vendor API endpoints
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import VendorRequest, VendorMatchResponse, VendorInfo
from app.services.vendor_service import vendor_service

router = APIRouter()

@router.post("/match", response_model=VendorMatchResponse)
async def match_vendors(vendor_request: VendorRequest):
    """
    Find and match manufacturing vendors for a design
    
    Args:
        vendor_request: Vendor matching request with design ID and requirements
        
    Returns:
        List of matched vendors with pricing and recommendation
    """
    try:
        result = await vendor_service.match_vendors(
            design_id=vendor_request.design_id,
            quantity=vendor_request.quantity,
            requirements=vendor_request.requirements
        )
        
        return VendorMatchResponse(
            design_id=result["design_id"],
            vendors=[VendorInfo(**v) for v in result["vendors"]],
            recommended_vendor=VendorInfo(**result["recommended_vendor"]) if result["recommended_vendor"] else None
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error matching vendors: {str(e)}")
