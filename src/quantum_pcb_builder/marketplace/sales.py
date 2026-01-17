"""Sales and production management for the marketplace."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from quantum_pcb_builder.core.base import BaseDesign
from quantum_pcb_builder.marketplace.listings import Listing


class ProductionStatus(Enum):
    """Status of a production order."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PRODUCTION = "in_production"
    QUALITY_CHECK = "quality_check"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(Enum):
    """Status of payment for a sale."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REFUNDED = "refunded"
    FAILED = "failed"


@dataclass
class ProductionOrder:
    """Order for PCB production."""

    order_id: str = field(default_factory=lambda: str(uuid4()))
    design_id: str = ""
    quantity: int = 1
    manufacturer_id: str = ""
    status: ProductionStatus = ProductionStatus.PENDING
    estimated_completion: datetime | None = None
    actual_completion: datetime | None = None
    specifications: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    tracking_number: str = ""
    notes: list[str] = field(default_factory=list)

    def update_status(self, new_status: ProductionStatus) -> None:
        """Update the production status."""
        self.status = new_status
        if new_status == ProductionStatus.DELIVERED:
            self.actual_completion = datetime.utcnow()

    def add_note(self, note: str) -> None:
        """Add a note to the order."""
        timestamp = datetime.utcnow().isoformat()
        self.notes.append(f"[{timestamp}] {note}")

    def to_dict(self) -> dict[str, Any]:
        """Serialize order to dictionary."""
        return {
            "order_id": self.order_id,
            "design_id": self.design_id,
            "quantity": self.quantity,
            "manufacturer_id": self.manufacturer_id,
            "status": self.status.value,
            "estimated_completion": (
                self.estimated_completion.isoformat() if self.estimated_completion else None
            ),
            "actual_completion": (
                self.actual_completion.isoformat() if self.actual_completion else None
            ),
            "specifications": self.specifications,
            "created_at": self.created_at.isoformat(),
            "tracking_number": self.tracking_number,
            "notes": self.notes,
        }


@dataclass
class Sale:
    """Record of a completed sale."""

    sale_id: str = field(default_factory=lambda: str(uuid4()))
    listing_id: str = ""
    design_id: str = ""
    seller_id: str = ""
    buyer_id: str = ""
    final_price: float = 0.0
    payment_status: PaymentStatus = PaymentStatus.PENDING
    completed_at: datetime = field(default_factory=datetime.utcnow)
    production_order: ProductionOrder | None = None
    license_type: str = "single"  # single, multi, exclusive
    royalty_percent: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize sale to dictionary."""
        return {
            "sale_id": self.sale_id,
            "listing_id": self.listing_id,
            "design_id": self.design_id,
            "seller_id": self.seller_id,
            "buyer_id": self.buyer_id,
            "final_price": self.final_price,
            "payment_status": self.payment_status.value,
            "completed_at": self.completed_at.isoformat(),
            "production_order": (
                self.production_order.to_dict() if self.production_order else None
            ),
            "license_type": self.license_type,
            "royalty_percent": self.royalty_percent,
            "metadata": self.metadata,
        }


class SalesManager:
    """Manager for sales and production orders."""

    def __init__(self) -> None:
        """Initialize the sales manager."""
        self._sales: dict[str, Sale] = {}
        self._orders: dict[str, ProductionOrder] = {}
        self._manufacturers: dict[str, dict[str, Any]] = {}
        self._load_default_manufacturers()

    def _load_default_manufacturers(self) -> None:
        """Load default in-house and partner manufacturers."""
        self._manufacturers["in_house"] = {
            "name": "In-House Production",
            "capabilities": ["2-layer", "4-layer", "prototype", "small-batch"],
            "lead_time_days": 5,
            "min_quantity": 1,
        }
        self._manufacturers["partner_a"] = {
            "name": "Partner Manufacturing A",
            "capabilities": ["2-layer", "4-layer", "6-layer", "mass-production"],
            "lead_time_days": 14,
            "min_quantity": 100,
        }

    def complete_sale(
        self,
        listing: Listing,
        buyer_id: str,
        final_price: float,
        license_type: str = "single",
    ) -> Sale:
        """Complete a sale from a listing."""
        # Mark listing as sold
        listing.mark_sold(final_price)

        # Create sale record
        sale = Sale(
            listing_id=listing.listing_id,
            design_id=listing.design.design_id if listing.design else "",
            seller_id=listing.seller_id,
            buyer_id=buyer_id,
            final_price=final_price,
            license_type=license_type,
        )

        self._sales[sale.sale_id] = sale
        return sale

    def create_production_order(
        self,
        design: BaseDesign,
        quantity: int = 1,
        manufacturer_id: str = "in_house",
        specifications: dict[str, Any] | None = None,
    ) -> ProductionOrder:
        """Create a production order for a design."""
        manufacturer = self._manufacturers.get(manufacturer_id)
        if not manufacturer:
            manufacturer_id = "in_house"
            manufacturer = self._manufacturers["in_house"]

        lead_time = manufacturer.get("lead_time_days", 14)

        order = ProductionOrder(
            design_id=design.design_id,
            quantity=quantity,
            manufacturer_id=manufacturer_id,
            specifications=specifications or {},
            estimated_completion=datetime.utcnow()
            + __import__("datetime").timedelta(days=lead_time),
        )

        self._orders[order.order_id] = order
        return order

    def get_sale(self, sale_id: str) -> Sale | None:
        """Get a sale by ID."""
        return self._sales.get(sale_id)

    def get_order(self, order_id: str) -> ProductionOrder | None:
        """Get a production order by ID."""
        return self._orders.get(order_id)

    def get_sales_by_seller(self, seller_id: str) -> list[Sale]:
        """Get all sales by a seller."""
        return [sale for sale in self._sales.values() if sale.seller_id == seller_id]

    def get_sales_by_buyer(self, buyer_id: str) -> list[Sale]:
        """Get all sales by a buyer."""
        return [sale for sale in self._sales.values() if sale.buyer_id == buyer_id]

    def get_orders_by_status(self, status: ProductionStatus) -> list[ProductionOrder]:
        """Get all orders with a specific status."""
        return [order for order in self._orders.values() if order.status == status]

    def update_order_status(
        self, order_id: str, new_status: ProductionStatus, note: str = ""
    ) -> bool:
        """Update a production order status."""
        order = self._orders.get(order_id)
        if order:
            order.update_status(new_status)
            if note:
                order.add_note(note)
            return True
        return False

    def get_manufacturers(self) -> dict[str, dict[str, Any]]:
        """Get all available manufacturers."""
        return self._manufacturers.copy()

    def add_manufacturer(self, manufacturer_id: str, details: dict[str, Any]) -> None:
        """Add a new manufacturer."""
        self._manufacturers[manufacturer_id] = details

    def get_revenue_report(self, seller_id: str | None = None) -> dict[str, Any]:
        """Generate a revenue report."""
        sales_list = list(self._sales.values())
        if seller_id:
            sales_list = [s for s in sales_list if s.seller_id == seller_id]

        total_revenue = sum(s.final_price for s in sales_list)
        completed_sales = [s for s in sales_list if s.payment_status == PaymentStatus.COMPLETED]
        pending_sales = [s for s in sales_list if s.payment_status == PaymentStatus.PENDING]

        return {
            "total_sales": len(sales_list),
            "total_revenue": total_revenue,
            "completed_sales": len(completed_sales),
            "completed_revenue": sum(s.final_price for s in completed_sales),
            "pending_sales": len(pending_sales),
            "pending_revenue": sum(s.final_price for s in pending_sales),
        }
