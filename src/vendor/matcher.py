"""Vendor matching logic for foundries and PCB assemblers.

This module surfaces compatible vendors based on design requirements
including process node, packaging type, and cost constraints.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PackagingType(Enum):
    """Packaging types supported by vendors."""

    STANDARD = "standard"
    BGA = "bga"
    QFN = "qfn"
    WLCSP = "wlcsp"
    FCBGA = "fcbga"
    COWOS = "cowos"
    CHIPLET_2D = "2d_chiplet"
    CHIPLET_25D = "2.5d_chiplet"
    CHIPLET_3D = "3d_chiplet"


class VendorType(Enum):
    """Types of vendors in the supply chain."""

    FOUNDRY = "foundry"
    PACKAGING = "packaging"
    PCB_ASSEMBLY = "pcb_assembly"
    TESTING = "testing"


@dataclass
class VendorCapability:
    """Capabilities of a vendor."""

    process_nodes: list[str]
    packaging_types: list[PackagingType]
    min_volume: int
    max_volume: int
    lead_time_weeks: int
    certifications: list[str] = field(default_factory=list)


@dataclass
class VendorQuote:
    """Quote from a vendor."""

    vendor_name: str
    vendor_type: VendorType
    unit_cost_usd: float
    nre_cost_usd: float
    lead_time_weeks: int
    min_order_quantity: int
    valid_until: str
    notes: str = ""


@dataclass
class DesignRequirements:
    """Requirements for vendor matching."""

    process_node: str
    packaging_type: PackagingType
    estimated_volume: int
    target_cost_usd: Optional[float] = None
    required_certifications: list[str] = field(default_factory=list)


class VendorMatcher:
    """Matches designs with compatible vendors.

    This class surfaces vendors based on design requirements
    and provides quotes for fabrication and assembly.
    """

    def __init__(self):
        """Initialize the vendor matcher with vendor database."""
        self._vendors = self._load_vendor_database()

    def _load_vendor_database(self) -> dict:
        """Load the vendor database.

        Returns:
            Dictionary of vendors and their capabilities.

        Note: This is a stub with example data.
        Real implementation would load from database or API.
        """
        return {
            "TSMC": VendorCapability(
                process_nodes=["3nm", "5nm", "7nm", "12nm", "16nm"],
                packaging_types=[
                    PackagingType.COWOS,
                    PackagingType.CHIPLET_25D,
                    PackagingType.CHIPLET_3D,
                ],
                min_volume=10000,
                max_volume=10000000,
                lead_time_weeks=12,
                certifications=["ISO9001", "IATF16949"],
            ),
            "Samsung": VendorCapability(
                process_nodes=["3nm", "5nm", "7nm", "14nm"],
                packaging_types=[
                    PackagingType.FCBGA,
                    PackagingType.CHIPLET_25D,
                ],
                min_volume=5000,
                max_volume=5000000,
                lead_time_weeks=10,
                certifications=["ISO9001"],
            ),
            "GlobalFoundries": VendorCapability(
                process_nodes=["12nm", "14nm", "22nm", "45nm"],
                packaging_types=[
                    PackagingType.BGA,
                    PackagingType.FCBGA,
                ],
                min_volume=1000,
                max_volume=1000000,
                lead_time_weeks=8,
                certifications=["ISO9001", "AS9100"],
            ),
            "JLCPCB": VendorCapability(
                process_nodes=["pcb"],
                packaging_types=[PackagingType.STANDARD],
                min_volume=5,
                max_volume=100000,
                lead_time_weeks=1,
                certifications=["ISO9001"],
            ),
        }

    def find_vendors(
        self, requirements: DesignRequirements
    ) -> list[tuple[str, VendorCapability]]:
        """Find vendors matching the requirements.

        Args:
            requirements: Design requirements for matching.

        Returns:
            List of (vendor_name, capability) tuples for matching vendors.
        """
        matching = []

        for name, capability in self._vendors.items():
            # Check process node
            if requirements.process_node not in capability.process_nodes:
                continue

            # Check packaging type
            if requirements.packaging_type not in capability.packaging_types:
                continue

            # Check volume
            if not (
                capability.min_volume
                <= requirements.estimated_volume
                <= capability.max_volume
            ):
                continue

            # Check certifications
            if requirements.required_certifications:
                if not all(
                    cert in capability.certifications
                    for cert in requirements.required_certifications
                ):
                    continue

            matching.append((name, capability))

        return matching

    def get_quotes(self, requirements: DesignRequirements) -> list[VendorQuote]:
        """Get quotes from matching vendors.

        Args:
            requirements: Design requirements.

        Returns:
            List of VendorQuote objects.

        Note: This is a stub implementation.
        Real implementation would call vendor APIs.
        """
        matching_vendors = self.find_vendors(requirements)
        quotes = []

        for vendor_name, capability in matching_vendors:
            # Stub: Generate placeholder quote
            quote = VendorQuote(
                vendor_name=vendor_name,
                vendor_type=VendorType.FOUNDRY,
                unit_cost_usd=self._estimate_cost(requirements, capability),
                nre_cost_usd=50000.0,
                lead_time_weeks=capability.lead_time_weeks,
                min_order_quantity=capability.min_volume,
                valid_until="2025-12-31",
                notes="Stub quote - contact vendor for actual pricing",
            )
            quotes.append(quote)

        return quotes

    def _estimate_cost(
        self, requirements: DesignRequirements, capability: VendorCapability
    ) -> float:
        """Estimate unit cost based on requirements.

        Args:
            requirements: Design requirements.
            capability: Vendor capability.

        Returns:
            Estimated unit cost in USD.
        """
        # Stub cost estimation based on process node
        base_costs = {
            "3nm": 100.0,
            "5nm": 50.0,
            "7nm": 25.0,
            "12nm": 10.0,
            "14nm": 8.0,
            "16nm": 7.0,
            "22nm": 5.0,
            "45nm": 2.0,
            "pcb": 0.50,
        }

        return base_costs.get(requirements.process_node, 10.0)
