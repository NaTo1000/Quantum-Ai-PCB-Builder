"""Design listings for the marketplace."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4

from quantum_pcb_builder.core.base import BaseDesign


class ListingStatus(Enum):
    """Status of a marketplace listing."""

    DRAFT = "draft"
    ACTIVE = "active"
    PENDING_REVIEW = "pending_review"
    CLOSED = "closed"
    SOLD = "sold"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class Listing:
    """A marketplace listing for a PCB design."""

    listing_id: str = field(default_factory=lambda: str(uuid4()))
    design: BaseDesign | None = None
    seller_id: str = ""
    title: str = ""
    description: str = ""
    min_price: float = 0.0
    current_price: float = 0.0
    status: ListingStatus = ListingStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    tags: list[str] = field(default_factory=list)
    views: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Set default expiration if not provided."""
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(days=30)
        if self.current_price == 0.0:
            self.current_price = self.min_price

    def activate(self) -> bool:
        """Activate the listing."""
        if self.status in [ListingStatus.DRAFT, ListingStatus.PENDING_REVIEW]:
            self.status = ListingStatus.ACTIVE
            return True
        return False

    def close(self) -> bool:
        """Close the listing."""
        if self.status == ListingStatus.ACTIVE:
            self.status = ListingStatus.CLOSED
            return True
        return False

    def mark_sold(self, final_price: float) -> bool:
        """Mark the listing as sold."""
        if self.status in [ListingStatus.ACTIVE, ListingStatus.CLOSED]:
            self.status = ListingStatus.SOLD
            self.current_price = final_price
            return True
        return False

    def is_expired(self) -> bool:
        """Check if the listing has expired."""
        return bool(self.expires_at and datetime.utcnow() > self.expires_at)

    def increment_views(self) -> None:
        """Increment view count."""
        self.views += 1

    def to_dict(self) -> dict[str, Any]:
        """Serialize listing to dictionary."""
        return {
            "listing_id": self.listing_id,
            "design_id": self.design.design_id if self.design else None,
            "seller_id": self.seller_id,
            "title": self.title,
            "description": self.description,
            "min_price": self.min_price,
            "current_price": self.current_price,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "tags": self.tags,
            "views": self.views,
            "metadata": self.metadata,
        }


class ListingManager:
    """Manager for marketplace listings."""

    def __init__(self) -> None:
        """Initialize the listing manager."""
        self._listings: dict[str, Listing] = {}

    def create_listing(
        self,
        design: BaseDesign,
        seller_id: str,
        title: str,
        min_price: float,
        description: str = "",
        tags: list[str] | None = None,
        duration_days: int = 30,
    ) -> Listing:
        """Create a new listing."""
        listing = Listing(
            design=design,
            seller_id=seller_id,
            title=title,
            description=description,
            min_price=min_price,
            tags=tags or [],
            expires_at=datetime.utcnow() + timedelta(days=duration_days),
        )
        self._listings[listing.listing_id] = listing
        return listing

    def get_listing(self, listing_id: str) -> Listing | None:
        """Get a listing by ID."""
        return self._listings.get(listing_id)

    def list_active(self) -> list[Listing]:
        """Get all active listings."""
        self._check_expirations()
        return [
            listing for listing in self._listings.values() if listing.status == ListingStatus.ACTIVE
        ]

    def list_by_seller(self, seller_id: str) -> list[Listing]:
        """Get all listings by a specific seller."""
        return [listing for listing in self._listings.values() if listing.seller_id == seller_id]

    def search(
        self,
        query: str = "",
        tags: list[str] | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        status: ListingStatus | None = None,
    ) -> list[Listing]:
        """Search listings with filters."""
        results = list(self._listings.values())

        if query:
            query_lower = query.lower()
            results = [
                listing
                for listing in results
                if query_lower in listing.title.lower()
                or query_lower in listing.description.lower()
            ]

        if tags:
            results = [listing for listing in results if any(tag in listing.tags for tag in tags)]

        if min_price is not None:
            results = [listing for listing in results if listing.current_price >= min_price]

        if max_price is not None:
            results = [listing for listing in results if listing.current_price <= max_price]

        if status:
            results = [listing for listing in results if listing.status == status]

        return results

    def _check_expirations(self) -> int:
        """Check and update expired listings."""
        expired_count = 0
        for listing in self._listings.values():
            if listing.status == ListingStatus.ACTIVE and listing.is_expired():
                listing.status = ListingStatus.EXPIRED
                expired_count += 1
        return expired_count

    def delete_listing(self, listing_id: str) -> bool:
        """Delete a listing."""
        if listing_id in self._listings:
            del self._listings[listing_id]
            return True
        return False

    def get_statistics(self) -> dict[str, Any]:
        """Get marketplace statistics."""
        total = len(self._listings)
        by_status: dict[str, int] = {}
        total_value = 0.0

        for listing in self._listings.values():
            status_key = listing.status.value
            by_status[status_key] = by_status.get(status_key, 0) + 1
            if listing.status == ListingStatus.ACTIVE:
                total_value += listing.current_price

        return {
            "total_listings": total,
            "by_status": by_status,
            "total_active_value": total_value,
        }
