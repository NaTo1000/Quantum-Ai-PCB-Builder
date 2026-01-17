"""
Manufacturing Cost Estimation.

This module provides cost estimation for PCB manufacturing including:
- PCB fabrication costs
- Assembly costs
- Component costs
- Tooling costs
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from quantum_pcb_builder.core.pcb import PCBBoard


class FinishType(Enum):
    """PCB surface finish types."""

    HASL = auto()
    HASL_LEAD_FREE = auto()
    ENIG = auto()
    OSP = auto()
    IMMERSION_SILVER = auto()
    IMMERSION_TIN = auto()


class SolderMaskColor(Enum):
    """Solder mask color options."""

    GREEN = auto()
    RED = auto()
    BLUE = auto()
    BLACK = auto()
    WHITE = auto()
    YELLOW = auto()
    MATTE_BLACK = auto()


@dataclass
class ManufacturingSpecs:
    """Manufacturing specifications for PCB."""

    quantity: int = 10
    finish: FinishType = FinishType.HASL_LEAD_FREE
    solder_mask: SolderMaskColor = SolderMaskColor.GREEN
    silkscreen_color: str = "white"
    copper_weight_oz: float = 1.0
    impedance_control: bool = False
    flying_probe_test: bool = True
    panelization: bool = False
    stencil_required: bool = False
    lead_time_days: int = 7


@dataclass
class CostBreakdown:
    """Detailed cost breakdown for manufacturing."""

    pcb_base_cost: float = 0.0
    layer_cost: float = 0.0
    area_cost: float = 0.0
    drill_cost: float = 0.0
    finish_cost: float = 0.0
    test_cost: float = 0.0
    stencil_cost: float = 0.0
    tooling_cost: float = 0.0
    shipping_cost: float = 0.0

    @property
    def subtotal(self) -> float:
        """Calculate subtotal before any discounts."""
        return (
            self.pcb_base_cost
            + self.layer_cost
            + self.area_cost
            + self.drill_cost
            + self.finish_cost
            + self.test_cost
            + self.stencil_cost
            + self.tooling_cost
            + self.shipping_cost
        )


@dataclass
class ManufacturingQuote:
    """Complete manufacturing quote."""

    board_name: str
    specs: ManufacturingSpecs
    breakdown: CostBreakdown
    quantity: int = 1
    unit_price: float = 0.0
    total_price: float = 0.0
    lead_time_days: int = 7
    valid_days: int = 30
    notes: list[str] = field(default_factory=list)
    manufacturer: str = ""


class CostEstimator:
    """
    Manufacturing cost estimation engine.

    Calculates estimated costs based on board specifications
    and manufacturing requirements.
    """

    def __init__(
        self,
        currency: str = "USD",
        markup_percent: float = 0.0,
    ) -> None:
        """
        Initialize cost estimator.

        Args:
            currency: Currency for quotes
            markup_percent: Additional markup percentage
        """
        self.currency = currency
        self.markup_percent = markup_percent

        # Base pricing (per unit)
        self.pricing = {
            "base_cost": 2.00,
            "per_layer": 0.50,
            "per_cm2": 0.02,
            "per_via": 0.01,
            "per_drill_size": 0.50,
            "finish": {
                FinishType.HASL: 0.0,
                FinishType.HASL_LEAD_FREE: 1.00,
                FinishType.ENIG: 5.00,
                FinishType.OSP: 1.50,
                FinishType.IMMERSION_SILVER: 3.00,
                FinishType.IMMERSION_TIN: 2.50,
            },
            "color": {
                SolderMaskColor.GREEN: 0.0,
                SolderMaskColor.RED: 1.00,
                SolderMaskColor.BLUE: 1.00,
                SolderMaskColor.BLACK: 2.00,
                SolderMaskColor.WHITE: 2.00,
                SolderMaskColor.YELLOW: 1.50,
                SolderMaskColor.MATTE_BLACK: 3.00,
            },
            "test_cost": 1.00,
            "tooling_cost": 10.00,
            "stencil_cost": 15.00,
            "impedance_control": 20.00,
        }

        # Quantity discounts
        self.quantity_discounts = [
            (10, 0.0),
            (50, 0.10),
            (100, 0.15),
            (500, 0.25),
            (1000, 0.35),
        ]

    def estimate(
        self,
        board: PCBBoard,
        specs: ManufacturingSpecs | None = None,
    ) -> ManufacturingQuote:
        """
        Generate manufacturing cost estimate.

        Args:
            board: PCB board to estimate
            specs: Manufacturing specifications

        Returns:
            ManufacturingQuote with cost breakdown
        """
        if specs is None:
            specs = ManufacturingSpecs()

        breakdown = self._calculate_breakdown(board, specs)
        discount = self._get_quantity_discount(specs.quantity)

        subtotal = breakdown.subtotal
        discounted = subtotal * (1 - discount)
        with_markup = discounted * (1 + self.markup_percent / 100)

        total_price = with_markup * specs.quantity
        unit_price = with_markup

        notes = self._generate_notes(board, specs)

        return ManufacturingQuote(
            board_name=board.name,
            specs=specs,
            breakdown=breakdown,
            quantity=specs.quantity,
            unit_price=round(unit_price, 2),
            total_price=round(total_price, 2),
            lead_time_days=specs.lead_time_days,
            notes=notes,
            manufacturer="Quantum PCB Manufacturing",
        )

    def _calculate_breakdown(self, board: PCBBoard, specs: ManufacturingSpecs) -> CostBreakdown:
        """Calculate detailed cost breakdown."""
        breakdown = CostBreakdown()

        # Base cost
        breakdown.pcb_base_cost = self.pricing["base_cost"]

        # Layer cost
        breakdown.layer_cost = board.layer_count * self.pricing["per_layer"]

        # Area cost
        area_cm2 = (board.width_mm * board.height_mm) / 100
        breakdown.area_cost = area_cm2 * self.pricing["per_cm2"]

        # Drill cost
        via_count = len(board.vias)
        drill_sizes = len({v.drill_mm for v in board.vias})
        breakdown.drill_cost = (
            via_count * self.pricing["per_via"] + drill_sizes * self.pricing["per_drill_size"]
        )

        # Finish cost
        breakdown.finish_cost = self.pricing["finish"].get(specs.finish, 0.0)

        # Test cost
        if specs.flying_probe_test:
            breakdown.test_cost = self.pricing["test_cost"]

        # Stencil cost
        if specs.stencil_required:
            breakdown.stencil_cost = self.pricing["stencil_cost"]

        # Tooling cost (one-time)
        breakdown.tooling_cost = self.pricing["tooling_cost"] / specs.quantity

        # Add impedance control if needed
        if specs.impedance_control:
            breakdown.tooling_cost += self.pricing["impedance_control"] / specs.quantity

        return breakdown

    def _get_quantity_discount(self, quantity: int) -> float:
        """Get discount based on quantity."""
        discount = 0.0
        for threshold, disc in self.quantity_discounts:
            if quantity >= threshold:
                discount = disc
        return discount

    def _generate_notes(self, board: PCBBoard, specs: ManufacturingSpecs) -> list[str]:
        """Generate notes for the quote."""
        notes = []

        # Design checks
        if board.layer_count > 4:
            notes.append("Multi-layer board - extended fabrication time may apply")

        if len(board.vias) > 100:
            notes.append("High via count - consider via-in-pad or HDI process")

        density = board.get_component_density()
        if density > 0.6:
            notes.append("High component density - assembly yield may be affected")

        # Spec notes
        if specs.impedance_control:
            notes.append("Impedance control requires stackup review")

        if specs.finish == FinishType.ENIG:
            notes.append("ENIG finish provides excellent solderability")

        return notes

    def compare_manufacturers(
        self,
        board: PCBBoard,
        specs: ManufacturingSpecs,
        manufacturers: list[str] | None = None,
    ) -> list[ManufacturingQuote]:
        """
        Compare quotes from multiple manufacturers.

        Args:
            board: PCB board to quote
            specs: Manufacturing specifications
            manufacturers: List of manufacturer names

        Returns:
            List of quotes sorted by price
        """
        if manufacturers is None:
            manufacturers = [
                "Quantum PCB Manufacturing",
                "PCB Express",
                "FastPCB Global",
            ]

        quotes = []

        # Generate quotes with simulated variance
        base_quote = self.estimate(board, specs)

        for i, mfr in enumerate(manufacturers):
            variance = 1.0 + (i - 1) * 0.15
            quote = ManufacturingQuote(
                board_name=board.name,
                specs=specs,
                breakdown=base_quote.breakdown,
                quantity=specs.quantity,
                unit_price=round(base_quote.unit_price * variance, 2),
                total_price=round(base_quote.total_price * variance, 2),
                lead_time_days=specs.lead_time_days + i * 2,
                notes=base_quote.notes,
                manufacturer=mfr,
            )
            quotes.append(quote)

        # Sort by total price
        quotes.sort(key=lambda q: q.total_price)

        return quotes


class AssemblyCostEstimator:
    """
    PCB Assembly cost estimation.

    Calculates costs for component placement and soldering.
    """

    def __init__(self) -> None:
        """Initialize assembly cost estimator."""
        self.pricing = {
            "setup_cost": 50.00,
            "per_smd_component": 0.02,
            "per_through_hole": 0.05,
            "per_bga": 0.50,
            "per_qfn": 0.10,
            "inspection_cost": 5.00,
        }

    def estimate_assembly(
        self,
        board: PCBBoard,
        quantity: int = 10,
    ) -> dict[str, Any]:
        """
        Estimate assembly costs.

        Args:
            board: PCB board with components
            quantity: Number of boards to assemble

        Returns:
            Dictionary with assembly cost breakdown
        """
        smd_count = 0
        th_count = 0
        bga_count = 0
        qfn_count = 0

        for component in board.components.values():
            if component.footprint:
                if component.footprint.smd:
                    if "BGA" in component.package.upper():
                        bga_count += 1
                    elif "QFN" in component.package.upper():
                        qfn_count += 1
                    else:
                        smd_count += 1
                else:
                    th_count += 1
            else:
                smd_count += 1

        # Calculate costs
        setup = self.pricing["setup_cost"]
        component_cost = (
            smd_count * self.pricing["per_smd_component"]
            + th_count * self.pricing["per_through_hole"]
            + bga_count * self.pricing["per_bga"]
            + qfn_count * self.pricing["per_qfn"]
        )
        inspection = self.pricing["inspection_cost"]

        per_board = component_cost + inspection
        total = setup + (per_board * quantity)

        return {
            "setup_cost": setup,
            "per_board_cost": round(per_board, 2),
            "total_cost": round(total, 2),
            "quantity": quantity,
            "component_counts": {
                "smd": smd_count,
                "through_hole": th_count,
                "bga": bga_count,
                "qfn": qfn_count,
            },
        }
