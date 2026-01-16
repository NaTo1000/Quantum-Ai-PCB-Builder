"""
Vendor Matching Service for finding manufacturing vendors
"""
import uuid
from typing import Dict, Any, List
from app.models.schemas import VendorInfo

class VendorService:
    """Service for matching designs with manufacturing vendors"""
    
    def __init__(self):
        # Mock vendor database
        self.vendors = [
            {
                "vendor_id": "vendor_001",
                "name": "JLCPCB",
                "capabilities": ["PCB", "SMT Assembly", "2-layer", "4-layer", "6-layer"],
                "base_price_per_unit": 2.0,
                "base_lead_time_days": 5,
                "rating": 4.8,
                "location": "China"
            },
            {
                "vendor_id": "vendor_002",
                "name": "PCBWay",
                "capabilities": ["PCB", "SMT Assembly", "2-layer", "4-layer", "Flexible PCB"],
                "base_price_per_unit": 2.5,
                "base_lead_time_days": 7,
                "rating": 4.7,
                "location": "China"
            },
            {
                "vendor_id": "vendor_003",
                "name": "OSH Park",
                "capabilities": ["PCB", "2-layer", "4-layer", "High Quality"],
                "base_price_per_unit": 5.0,
                "base_lead_time_days": 12,
                "rating": 4.9,
                "location": "USA"
            },
            {
                "vendor_id": "vendor_004",
                "name": "Seeed Studio",
                "capabilities": ["PCB", "SMT Assembly", "Prototyping", "IoT Devices"],
                "base_price_per_unit": 3.0,
                "base_lead_time_days": 10,
                "rating": 4.6,
                "location": "China"
            },
            {
                "vendor_id": "vendor_005",
                "name": "Eurocircuits",
                "capabilities": ["PCB", "HDI", "High-Frequency", "4-layer", "6-layer", "8-layer"],
                "base_price_per_unit": 8.0,
                "base_lead_time_days": 8,
                "rating": 4.8,
                "location": "Europe"
            }
        ]
    
    async def match_vendors(self, design_id: str, quantity: int = 100, requirements: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Match design with suitable manufacturing vendors
        
        Args:
            design_id: ID of the design
            quantity: Number of units to manufacture
            requirements: Optional manufacturing requirements
            
        Returns:
            Dictionary with matched vendors and recommendation
        """
        # Filter vendors based on requirements
        matched_vendors = []
        
        for vendor in self.vendors:
            # Calculate price based on quantity
            price_per_unit = self._calculate_price(vendor, quantity)
            lead_time = self._calculate_lead_time(vendor, quantity)
            
            vendor_info = VendorInfo(
                vendor_id=vendor["vendor_id"],
                name=vendor["name"],
                price_per_unit=price_per_unit,
                lead_time_days=lead_time,
                capabilities=vendor["capabilities"],
                rating=vendor["rating"]
            )
            
            # Check if vendor meets requirements
            if self._meets_requirements(vendor, requirements):
                matched_vendors.append(vendor_info)
        
        # Sort by rating and price
        matched_vendors.sort(key=lambda v: (-v.rating, v.price_per_unit))
        
        # Recommend best vendor
        recommended = matched_vendors[0] if matched_vendors else None
        
        return {
            "design_id": design_id,
            "vendors": [v.dict() for v in matched_vendors],
            "recommended_vendor": recommended.dict() if recommended else None,
            "total_quantity": quantity
        }
    
    def _calculate_price(self, vendor: Dict[str, Any], quantity: int) -> float:
        """Calculate price per unit based on quantity (bulk discount)"""
        base_price = vendor["base_price_per_unit"]
        
        if quantity >= 1000:
            return base_price * 0.6  # 40% discount
        elif quantity >= 500:
            return base_price * 0.7  # 30% discount
        elif quantity >= 100:
            return base_price * 0.8  # 20% discount
        elif quantity >= 50:
            return base_price * 0.9  # 10% discount
        else:
            return base_price
    
    def _calculate_lead_time(self, vendor: Dict[str, Any], quantity: int) -> int:
        """Calculate lead time based on quantity"""
        base_lead_time = vendor["base_lead_time_days"]
        
        if quantity >= 1000:
            return base_lead_time + 7
        elif quantity >= 500:
            return base_lead_time + 5
        elif quantity >= 100:
            return base_lead_time + 3
        else:
            return base_lead_time
    
    def _meets_requirements(self, vendor: Dict[str, Any], requirements: Dict[str, Any] = None) -> bool:
        """Check if vendor meets specified requirements"""
        if not requirements:
            return True
        
        # Check capability requirements
        required_capabilities = requirements.get("capabilities", [])
        vendor_capabilities = vendor["capabilities"]
        
        for req_cap in required_capabilities:
            if req_cap not in vendor_capabilities:
                return False
        
        # Check location requirement
        required_location = requirements.get("location")
        if required_location and vendor.get("location") != required_location:
            return False
        
        # Check minimum rating
        min_rating = requirements.get("min_rating", 0)
        if vendor["rating"] < min_rating:
            return False
        
        return True

vendor_service = VendorService()
