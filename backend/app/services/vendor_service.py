"""Vendor matching and quoting service."""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from app.schemas.vendors import Quote, Vendor, VendorMatchResponse
from app.schemas.schematic import SchematicResponse


# Configuration constants for vendor matching
PRICE_WEIGHT = 0.7
LEAD_TIME_WEIGHT = 0.3


class VendorService:
    """Service for vendor matching and quoting."""

    def __init__(self):
        self._vendors = self._init_vendors()

    def _init_vendors(self) -> list[Vendor]:
        """Initialize vendor database."""
        return [
            Vendor(
                id="foundry-tsmc",
                name="TSMC",
                type="foundry",
                capabilities=["5nm", "7nm", "16nm", "28nm", "advanced_packaging"],
                location="Taiwan",
                min_order_quantity=10000,
                lead_time_days=90,
            ),
            Vendor(
                id="foundry-globalfoundries",
                name="GlobalFoundries",
                type="foundry",
                capabilities=["12nm", "22nm", "45nm", "rf", "embedded_memory"],
                location="USA",
                min_order_quantity=5000,
                lead_time_days=75,
            ),
            Vendor(
                id="pcb-jlcpcb",
                name="JLCPCB",
                type="assembler",
                capabilities=["2layer", "4layer", "6layer", "smt", "through_hole"],
                location="China",
                min_order_quantity=5,
                lead_time_days=7,
            ),
            Vendor(
                id="pcb-pcbway",
                name="PCBWay",
                type="assembler",
                capabilities=["multilayer", "flex", "rigid_flex", "hdi", "smt"],
                location="China",
                min_order_quantity=5,
                lead_time_days=10,
            ),
            Vendor(
                id="pcb-oshpark",
                name="OSH Park",
                type="assembler",
                capabilities=["2layer", "4layer", "prototype", "enig"],
                location="USA",
                min_order_quantity=3,
                lead_time_days=12,
            ),
            Vendor(
                id="packaging-amkor",
                name="Amkor Technology",
                type="packaging",
                capabilities=["bga", "qfn", "wafer_level", "sip", "fc_bga"],
                location="South Korea",
                min_order_quantity=1000,
                lead_time_days=45,
            ),
            Vendor(
                id="packaging-ase",
                name="ASE Group",
                type="packaging",
                capabilities=["fcbga", "wlcsp", "sip", "3d_packaging"],
                location="Taiwan",
                min_order_quantity=1000,
                lead_time_days=40,
            ),
        ]

    async def match_vendors(
        self,
        schematic: SchematicResponse,
        quantity: int = 1000,
        preferred_locations: list[str] = None,
        max_lead_time_days: Optional[int] = None,
    ) -> VendorMatchResponse:
        """
        Match vendors based on schematic requirements.

        Args:
            schematic: The schematic to find vendors for
            quantity: Order quantity
            preferred_locations: Preferred vendor locations
            max_lead_time_days: Maximum acceptable lead time

        Returns:
            VendorMatchResponse with matched vendors and quotes
        """
        preferred_locations = preferred_locations or []

        # Determine required vendor types based on schematic
        required_capabilities = self._analyze_requirements(schematic)

        # Filter and rank vendors
        matched_vendors = []
        for vendor in self._vendors:
            # Check if vendor meets requirements
            if max_lead_time_days and vendor.lead_time_days > max_lead_time_days:
                continue

            if vendor.min_order_quantity and vendor.min_order_quantity > quantity:
                continue

            # Check capability match
            capability_match = any(
                cap in vendor.capabilities for cap in required_capabilities
            )

            if capability_match:
                matched_vendors.append(vendor)

        # Sort by preference (location match first, then lead time)
        matched_vendors.sort(
            key=lambda v: (
                0 if v.location in preferred_locations else 1,
                v.lead_time_days,
            )
        )

        # Generate quotes
        quotes = self._generate_quotes(matched_vendors, schematic, quantity)

        # Determine recommended vendor
        recommended_id = None
        if quotes:
            # Recommend based on price-to-lead-time ratio
            best_quote = min(
                quotes,
                key=lambda q: q.price_per_unit * PRICE_WEIGHT + q.lead_time_days * LEAD_TIME_WEIGHT,
            )
            recommended_id = best_quote.vendor_id

        # Calculate estimated delivery
        estimated_delivery = None
        if recommended_id:
            recommended_vendor = next(
                (v for v in matched_vendors if v.id == recommended_id), None
            )
            if recommended_vendor:
                delivery_date = datetime.now() + timedelta(
                    days=recommended_vendor.lead_time_days
                )
                estimated_delivery = delivery_date.strftime("%Y-%m-%d")

        return VendorMatchResponse(
            schematic_id=schematic.id,
            matched_vendors=matched_vendors,
            quotes=quotes,
            recommended_vendor_id=recommended_id,
            estimated_delivery_date=estimated_delivery,
        )

    def _analyze_requirements(self, schematic: SchematicResponse) -> list[str]:
        """Analyze schematic to determine required capabilities."""
        capabilities = []

        component_types = {c.type for c in schematic.components}

        # Determine if this is a chip or PCB design
        if "mcu" in component_types or len(schematic.components) > 10:
            capabilities.extend(["smt", "multilayer"])

        if "rf_module" in component_types or "rf_component" in component_types:
            capabilities.extend(["rf", "impedance_control"])

        # Check complexity
        if len(schematic.components) > 50:
            capabilities.append("hdi")
        elif len(schematic.components) > 20:
            capabilities.append("4layer")
        else:
            capabilities.append("2layer")

        return capabilities

    def _generate_quotes(
        self,
        vendors: list[Vendor],
        schematic: SchematicResponse,
        quantity: int,
    ) -> list[Quote]:
        """Generate price quotes from vendors."""
        quotes = []

        # Base pricing factors
        component_count = len(schematic.components)
        complexity_factor = 1 + (component_count / 100)

        for vendor in vendors:
            # Calculate pricing based on vendor type
            if vendor.type == "foundry":
                base_price = 2.50 * complexity_factor
                setup_cost = 50000.0
            elif vendor.type == "assembler":
                base_price = 0.50 * complexity_factor
                setup_cost = 100.0 if quantity < 100 else 50.0
            else:  # packaging
                base_price = 0.30 * complexity_factor
                setup_cost = 5000.0

            # Quantity discount
            if quantity >= 10000:
                base_price *= 0.7
            elif quantity >= 1000:
                base_price *= 0.85

            quotes.append(
                Quote(
                    vendor_id=vendor.id,
                    vendor_name=vendor.name,
                    price_per_unit=round(base_price, 2),
                    setup_cost=setup_cost,
                    lead_time_days=vendor.lead_time_days,
                    minimum_quantity=vendor.min_order_quantity or 1,
                    currency="USD",
                )
            )

        return quotes

    def get_vendor(self, vendor_id: str) -> Optional[Vendor]:
        """Get vendor by ID."""
        return next((v for v in self._vendors if v.id == vendor_id), None)

    def list_vendors(self, vendor_type: Optional[str] = None) -> list[Vendor]:
        """List all vendors, optionally filtered by type."""
        if vendor_type:
            return [v for v in self._vendors if v.type == vendor_type]
        return self._vendors


# Singleton instance
vendor_service = VendorService()
