"""Bidding system for the marketplace."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from quantum_pcb_builder.marketplace.listings import Listing, ListingStatus


@dataclass
class Bid:
    """A bid on a marketplace listing."""

    bid_id: str = field(default_factory=lambda: str(uuid4()))
    listing_id: str = ""
    bidder_id: str = ""
    amount: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    is_winning: bool = False
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize bid to dictionary."""
        return {
            "bid_id": self.bid_id,
            "listing_id": self.listing_id,
            "bidder_id": self.bidder_id,
            "amount": self.amount,
            "timestamp": self.timestamp.isoformat(),
            "is_winning": self.is_winning,
            "message": self.message,
        }


class BiddingEngine:
    """Engine for managing bids on listings."""

    def __init__(self, min_bid_increment: float = 1.0) -> None:
        """Initialize the bidding engine."""
        self._bids: dict[str, list[Bid]] = {}  # listing_id -> list of bids
        self.min_bid_increment = min_bid_increment

    def place_bid(
        self,
        listing: Listing,
        bidder_id: str,
        amount: float,
        message: str = "",
    ) -> tuple[bool, str]:
        """Place a bid on a listing.

        Returns (success, message).
        """
        # Validate listing status
        if listing.status != ListingStatus.ACTIVE:
            return (False, "Listing is not active")

        if listing.is_expired():
            return (False, "Listing has expired")

        # Validate bid amount
        if amount < listing.min_price:
            return (False, f"Bid must be at least {listing.min_price}")

        current_high = self.get_highest_bid(listing.listing_id)
        if current_high and amount <= current_high.amount:
            return (
                False,
                f"Bid must be higher than current bid of {current_high.amount}",
            )

        if current_high and (amount - current_high.amount) < self.min_bid_increment:
            return (
                False,
                f"Minimum bid increment is {self.min_bid_increment}",
            )

        # Prevent seller from bidding
        if bidder_id == listing.seller_id:
            return (False, "Seller cannot bid on own listing")

        # Create and record bid
        bid = Bid(
            listing_id=listing.listing_id,
            bidder_id=bidder_id,
            amount=amount,
            message=message,
            is_winning=True,
        )

        # Mark previous winning bid as not winning
        if current_high:
            current_high.is_winning = False

        # Store bid
        if listing.listing_id not in self._bids:
            self._bids[listing.listing_id] = []
        self._bids[listing.listing_id].append(bid)

        # Update listing price
        listing.current_price = amount

        return (True, f"Bid of {amount} placed successfully")

    def get_highest_bid(self, listing_id: str) -> Bid | None:
        """Get the highest bid for a listing."""
        bids = self._bids.get(listing_id, [])
        if not bids:
            return None
        return max(bids, key=lambda b: b.amount)

    def get_bids(self, listing_id: str, limit: int | None = None) -> list[Bid]:
        """Get all bids for a listing, sorted by amount descending."""
        bids = self._bids.get(listing_id, [])
        sorted_bids = sorted(bids, key=lambda b: b.amount, reverse=True)
        if limit:
            return sorted_bids[:limit]
        return sorted_bids

    def get_bid_count(self, listing_id: str) -> int:
        """Get the number of bids on a listing."""
        return len(self._bids.get(listing_id, []))

    def get_bidder_history(self, bidder_id: str) -> list[Bid]:
        """Get all bids by a specific bidder."""
        all_bids = []
        for bids in self._bids.values():
            for bid in bids:
                if bid.bidder_id == bidder_id:
                    all_bids.append(bid)
        return sorted(all_bids, key=lambda b: b.timestamp, reverse=True)

    def retract_bid(self, bid_id: str, bidder_id: str) -> tuple[bool, str]:
        """Retract a bid (only allowed for non-winning bids)."""
        for _listing_id, bids in self._bids.items():
            for i, bid in enumerate(bids):
                if bid.bid_id == bid_id:
                    if bid.bidder_id != bidder_id:
                        return (False, "Not authorized to retract this bid")
                    if bid.is_winning:
                        return (False, "Cannot retract winning bid")
                    bids.pop(i)
                    return (True, "Bid retracted successfully")
        return (False, "Bid not found")

    def get_auction_summary(self, listing: Listing) -> dict[str, Any]:
        """Get a summary of the auction for a listing."""
        bids = self._bids.get(listing.listing_id, [])
        highest = self.get_highest_bid(listing.listing_id)

        unique_bidders = {bid.bidder_id for bid in bids}

        return {
            "listing_id": listing.listing_id,
            "title": listing.title,
            "status": listing.status.value,
            "min_price": listing.min_price,
            "current_price": listing.current_price,
            "bid_count": len(bids),
            "unique_bidders": len(unique_bidders),
            "highest_bid": highest.to_dict() if highest else None,
            "is_expired": listing.is_expired(),
        }
