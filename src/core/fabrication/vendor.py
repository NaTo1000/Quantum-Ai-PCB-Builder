"""
Fabrication Vendor Integration

This module provides integration with PCB fabrication vendors,
enabling quote requests, order placement, and status tracking.
"""

from dataclasses import dataclass, field
from typing import Any
from enum import Enum
from datetime import datetime, timedelta
import uuid


class VendorCapability(Enum):
    """Fabrication capabilities offered by vendors."""
    PCB_PROTOTYPE = "pcb_prototype"
    PCB_PRODUCTION = "pcb_production"
    PCB_ASSEMBLY = "pcb_assembly"
    CHIP_FABRICATION = "chip_fabrication"
    CHIP_PACKAGING = "chip_packaging"
    COMPONENT_SOURCING = "component_sourcing"
    STENCIL = "stencil"
    FLEX_PCB = "flex_pcb"
    RIGID_FLEX = "rigid_flex"
    HDI = "hdi"


class OrderStatus(Enum):
    """Status of a fabrication order."""
    QUOTE_REQUESTED = "quote_requested"
    QUOTE_RECEIVED = "quote_received"
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    IN_PRODUCTION = "in_production"
    QUALITY_CHECK = "quality_check"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PCBLayerCount(Enum):
    """Standard PCB layer configurations."""
    SINGLE = 1
    DOUBLE = 2
    FOUR = 4
    SIX = 6
    EIGHT = 8


@dataclass
class VendorInfo:
    """Information about a fabrication vendor."""
    vendor_id: str
    name: str
    website: str
    capabilities: list[VendorCapability]
    min_lead_time_days: int
    countries_served: list[str]
    certifications: list[str]
    rating: float = 0.0
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert vendor info to dictionary."""
        return {
            "vendor_id": self.vendor_id,
            "name": self.name,
            "website": self.website,
            "capabilities": [c.value for c in self.capabilities],
            "min_lead_time_days": self.min_lead_time_days,
            "countries_served": self.countries_served,
            "certifications": self.certifications,
            "rating": self.rating,
            "description": self.description
        }


@dataclass
class PCBSpecification:
    """Specifications for PCB fabrication."""
    board_size_mm: tuple[float, float]
    layers: int = 2
    thickness_mm: float = 1.6
    copper_weight_oz: float = 1.0
    surface_finish: str = "HASL"
    solder_mask_color: str = "green"
    silkscreen_color: str = "white"
    min_trace_width_mm: float = 0.15
    min_drill_size_mm: float = 0.3
    quantity: int = 10
    panelization: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert specification to dictionary."""
        return {
            "board_size_mm": self.board_size_mm,
            "layers": self.layers,
            "thickness_mm": self.thickness_mm,
            "copper_weight_oz": self.copper_weight_oz,
            "surface_finish": self.surface_finish,
            "solder_mask_color": self.solder_mask_color,
            "silkscreen_color": self.silkscreen_color,
            "min_trace_width_mm": self.min_trace_width_mm,
            "min_drill_size_mm": self.min_drill_size_mm,
            "quantity": self.quantity,
            "panelization": self.panelization
        }


@dataclass
class Quote:
    """A price quote from a vendor."""
    quote_id: str
    vendor_id: str
    specification: PCBSpecification
    unit_price_usd: float
    total_price_usd: float
    tooling_cost_usd: float
    shipping_cost_usd: float
    lead_time_days: int
    valid_until: datetime
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert quote to dictionary."""
        return {
            "quote_id": self.quote_id,
            "vendor_id": self.vendor_id,
            "specification": self.specification.to_dict(),
            "unit_price_usd": self.unit_price_usd,
            "total_price_usd": self.total_price_usd,
            "tooling_cost_usd": self.tooling_cost_usd,
            "shipping_cost_usd": self.shipping_cost_usd,
            "lead_time_days": self.lead_time_days,
            "valid_until": self.valid_until.isoformat(),
            "notes": self.notes
        }


@dataclass
class Order:
    """A fabrication order."""
    order_id: str
    quote_id: str
    vendor_id: str
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    tracking_number: str | None = None
    shipping_carrier: str | None = None
    estimated_delivery: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert order to dictionary."""
        return {
            "order_id": self.order_id,
            "quote_id": self.quote_id,
            "vendor_id": self.vendor_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tracking_number": self.tracking_number,
            "shipping_carrier": self.shipping_carrier,
            "estimated_delivery": self.estimated_delivery.isoformat() if self.estimated_delivery else None
        }


class VendorRegistry:
    """
    Registry of fabrication vendors with their capabilities and pricing.
    
    This class manages vendor information and provides vendor matching
    based on design requirements and user preferences.
    """
    
    def __init__(self):
        """Initialize the vendor registry with default vendors."""
        self._vendors: dict[str, VendorInfo] = {}
        self._load_default_vendors()
    
    def _load_default_vendors(self):
        """Load default vendor configurations."""
        # Note: These are example vendors for demonstration
        # In production, this would connect to a real vendor database
        self._vendors = {
            "vendor_001": VendorInfo(
                vendor_id="vendor_001",
                name="PCB Prototype Express",
                website="https://example-pcb-proto.com",
                capabilities=[
                    VendorCapability.PCB_PROTOTYPE,
                    VendorCapability.PCB_ASSEMBLY,
                    VendorCapability.STENCIL
                ],
                min_lead_time_days=3,
                countries_served=["US", "CA", "EU"],
                certifications=["ISO9001", "UL"],
                rating=4.5,
                description="Fast prototype PCB manufacturing with quick-turn assembly"
            ),
            "vendor_002": VendorInfo(
                vendor_id="vendor_002",
                name="Global PCB Solutions",
                website="https://example-global-pcb.com",
                capabilities=[
                    VendorCapability.PCB_PROTOTYPE,
                    VendorCapability.PCB_PRODUCTION,
                    VendorCapability.PCB_ASSEMBLY,
                    VendorCapability.COMPONENT_SOURCING,
                    VendorCapability.HDI
                ],
                min_lead_time_days=7,
                countries_served=["US", "CA", "EU", "UK", "AU", "JP"],
                certifications=["ISO9001", "ISO14001", "IATF16949"],
                rating=4.8,
                description="Full-service PCB manufacturing with global shipping"
            ),
            "vendor_003": VendorInfo(
                vendor_id="vendor_003",
                name="FlexCircuit Technologies",
                website="https://example-flex-tech.com",
                capabilities=[
                    VendorCapability.PCB_PROTOTYPE,
                    VendorCapability.FLEX_PCB,
                    VendorCapability.RIGID_FLEX
                ],
                min_lead_time_days=10,
                countries_served=["US", "EU"],
                certifications=["ISO9001", "AS9100"],
                rating=4.3,
                description="Specialized in flexible and rigid-flex PCB solutions"
            ),
            "vendor_004": VendorInfo(
                vendor_id="vendor_004",
                name="ChipWorks Fabrication",
                website="https://example-chipworks.com",
                capabilities=[
                    VendorCapability.CHIP_FABRICATION,
                    VendorCapability.CHIP_PACKAGING
                ],
                min_lead_time_days=30,
                countries_served=["US", "TW", "KR"],
                certifications=["ISO9001", "JEDEC"],
                rating=4.6,
                description="Custom chip fabrication and advanced packaging"
            ),
        }
    
    def get_vendor(self, vendor_id: str) -> VendorInfo | None:
        """Get vendor information by ID."""
        return self._vendors.get(vendor_id)
    
    def list_vendors(
        self,
        capability: VendorCapability | None = None,
        country: str | None = None,
        min_rating: float = 0.0
    ) -> list[VendorInfo]:
        """
        List vendors matching the given criteria.
        
        Args:
            capability: Filter by required capability.
            country: Filter by country served.
            min_rating: Minimum rating threshold.
            
        Returns:
            List of matching vendors.
        """
        vendors = list(self._vendors.values())
        
        if capability:
            vendors = [v for v in vendors if capability in v.capabilities]
        
        if country:
            vendors = [v for v in vendors if country.upper() in v.countries_served]
        
        vendors = [v for v in vendors if v.rating >= min_rating]
        
        return sorted(vendors, key=lambda v: v.rating, reverse=True)
    
    def find_vendors_for_design(
        self,
        is_prototype: bool = True,
        needs_assembly: bool = False,
        is_flex: bool = False,
        is_chip: bool = False
    ) -> list[VendorInfo]:
        """
        Find vendors suitable for a specific design type.
        
        Args:
            is_prototype: Whether this is a prototype run.
            needs_assembly: Whether PCB assembly is needed.
            is_flex: Whether this is a flex or rigid-flex PCB.
            is_chip: Whether this is a chip (not PCB) fabrication.
            
        Returns:
            List of suitable vendors.
        """
        suitable = []
        
        for vendor in self._vendors.values():
            caps = vendor.capabilities
            
            # Check chip fabrication
            if is_chip:
                if VendorCapability.CHIP_FABRICATION in caps:
                    suitable.append(vendor)
                continue
            
            # Check flex PCB
            if is_flex:
                if VendorCapability.FLEX_PCB in caps or VendorCapability.RIGID_FLEX in caps:
                    suitable.append(vendor)
                continue
            
            # Check regular PCB
            if is_prototype:
                if VendorCapability.PCB_PROTOTYPE not in caps:
                    continue
            else:
                if VendorCapability.PCB_PRODUCTION not in caps:
                    continue
            
            # Check assembly requirement
            if needs_assembly and VendorCapability.PCB_ASSEMBLY not in caps:
                continue
            
            suitable.append(vendor)
        
        return sorted(suitable, key=lambda v: v.rating, reverse=True)


class QuoteEngine:
    """
    Engine for generating and managing fabrication quotes.
    
    Calculates pricing based on PCB specifications and vendor rates.
    """
    
    # Base pricing per square cm (simplified model)
    BASE_PRICE_PER_CM2 = {
        1: 0.05,  # Single layer
        2: 0.08,  # Double layer
        4: 0.15,  # 4 layer
        6: 0.25,  # 6 layer
        8: 0.40,  # 8 layer
    }
    
    # Surface finish multipliers
    FINISH_MULTIPLIERS = {
        "HASL": 1.0,
        "HASL-LF": 1.1,
        "ENIG": 1.5,
        "OSP": 0.9,
        "Immersion Silver": 1.3,
        "Immersion Tin": 1.2,
    }
    
    # Tooling costs
    TOOLING_COST = 50.0  # Base tooling cost

    def __init__(self, vendor_registry: VendorRegistry):
        """Initialize the quote engine."""
        self.vendor_registry = vendor_registry
    
    def generate_quote(
        self,
        vendor_id: str,
        specification: PCBSpecification
    ) -> Quote:
        """
        Generate a quote for PCB fabrication.
        
        Args:
            vendor_id: The vendor to get a quote from.
            specification: PCB specifications.
            
        Returns:
            A Quote object with pricing details.
        """
        vendor = self.vendor_registry.get_vendor(vendor_id)
        if not vendor:
            raise ValueError(f"Vendor not found: {vendor_id}")
        
        # Calculate board area
        area_cm2 = (specification.board_size_mm[0] / 10) * (specification.board_size_mm[1] / 10)
        
        # Base price calculation
        layer_price = self.BASE_PRICE_PER_CM2.get(specification.layers, 0.50)
        base_unit_price = area_cm2 * layer_price
        
        # Apply finish multiplier
        finish_mult = self.FINISH_MULTIPLIERS.get(specification.surface_finish, 1.0)
        unit_price = base_unit_price * finish_mult
        
        # Apply copper weight multiplier
        if specification.copper_weight_oz > 1:
            unit_price *= 1 + (specification.copper_weight_oz - 1) * 0.2
        
        # Volume discount
        if specification.quantity >= 100:
            unit_price *= 0.7
        elif specification.quantity >= 50:
            unit_price *= 0.8
        elif specification.quantity >= 20:
            unit_price *= 0.9
        
        # Calculate totals
        total_price = unit_price * specification.quantity
        tooling = self.TOOLING_COST if specification.quantity < 100 else 0
        
        # Estimate shipping
        shipping = 15.0 + (specification.quantity * 0.1)
        
        # Lead time based on vendor
        lead_time = vendor.min_lead_time_days
        if specification.layers > 4:
            lead_time += 3
        if specification.quantity > 50:
            lead_time += 2
        
        # Quote valid for 30 days
        valid_until = datetime.now() + timedelta(days=30)
        
        return Quote(
            quote_id=str(uuid.uuid4()),
            vendor_id=vendor_id,
            specification=specification,
            unit_price_usd=round(unit_price, 2),
            total_price_usd=round(total_price, 2),
            tooling_cost_usd=tooling,
            shipping_cost_usd=round(shipping, 2),
            lead_time_days=lead_time,
            valid_until=valid_until
        )
    
    def compare_quotes(
        self,
        specification: PCBSpecification,
        vendor_ids: list[str] | None = None
    ) -> list[Quote]:
        """
        Get and compare quotes from multiple vendors.
        
        Args:
            specification: PCB specifications.
            vendor_ids: Specific vendors to quote, or None for all.
            
        Returns:
            List of quotes sorted by total price.
        """
        if vendor_ids is None:
            # Get all vendors with PCB capability
            vendors = self.vendor_registry.list_vendors(
                capability=VendorCapability.PCB_PROTOTYPE
            )
            vendor_ids = [v.vendor_id for v in vendors]
        
        quotes = []
        for vid in vendor_ids:
            try:
                quote = self.generate_quote(vid, specification)
                quotes.append(quote)
            except ValueError:
                continue
        
        # Sort by total cost (price + tooling + shipping)
        quotes.sort(key=lambda q: q.total_price_usd + q.tooling_cost_usd + q.shipping_cost_usd)
        
        return quotes


class OrderManager:
    """
    Manages fabrication orders from placement to delivery.
    """
    
    def __init__(self):
        """Initialize the order manager."""
        self._orders: dict[str, Order] = {}
    
    def create_order(self, quote: Quote) -> Order:
        """
        Create a new order from an accepted quote.
        
        Args:
            quote: The accepted quote.
            
        Returns:
            A new Order object.
        """
        now = datetime.now()
        order = Order(
            order_id=str(uuid.uuid4()),
            quote_id=quote.quote_id,
            vendor_id=quote.vendor_id,
            status=OrderStatus.PENDING_PAYMENT,
            created_at=now,
            updated_at=now
        )
        
        self._orders[order.order_id] = order
        return order
    
    def get_order(self, order_id: str) -> Order | None:
        """Get an order by ID."""
        return self._orders.get(order_id)
    
    def update_status(self, order_id: str, status: OrderStatus) -> Order | None:
        """Update the status of an order."""
        order = self._orders.get(order_id)
        if order:
            order.status = status
            order.updated_at = datetime.now()
        return order
    
    def add_tracking(
        self,
        order_id: str,
        tracking_number: str,
        carrier: str
    ) -> Order | None:
        """Add tracking information to an order."""
        order = self._orders.get(order_id)
        if order:
            order.tracking_number = tracking_number
            order.shipping_carrier = carrier
            order.status = OrderStatus.SHIPPED
            order.updated_at = datetime.now()
        return order
    
    def list_orders(
        self,
        status: OrderStatus | None = None
    ) -> list[Order]:
        """List all orders, optionally filtered by status."""
        orders = list(self._orders.values())
        if status:
            orders = [o for o in orders if o.status == status]
        return sorted(orders, key=lambda o: o.created_at, reverse=True)
