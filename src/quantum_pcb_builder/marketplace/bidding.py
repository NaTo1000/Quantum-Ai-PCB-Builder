"""
Bidding System for PCB Products.

This module implements a bidding/auction system for PCB designs:
- Auction creation and management
- Bid placement and validation
- Winner determination
- Notification system
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class AuctionStatus(Enum):
    """Status of an auction."""

    DRAFT = auto()
    SCHEDULED = auto()
    ACTIVE = auto()
    ENDED = auto()
    CANCELLED = auto()
    SOLD = auto()


class BidStatus(Enum):
    """Status of a bid."""

    PENDING = auto()
    ACCEPTED = auto()
    OUTBID = auto()
    REJECTED = auto()
    WINNING = auto()


@dataclass
class Bid:
    """Represents a bid on an auction."""

    auction_id: str
    bidder_id: str
    amount: float
    timestamp: datetime = field(default_factory=datetime.now)
    status: BidStatus = BidStatus.PENDING
    uuid: str = field(default_factory=lambda: str(uuid4()))
    notes: str = ""

    def is_higher_than(self, other: "Bid") -> bool:
        """Check if this bid is higher than another."""
        return self.amount > other.amount


@dataclass
class Auction:
    """
    Represents an auction for a PCB product.

    Supports both traditional ascending auctions and
    sealed-bid auctions for manufacturing contracts.
    """

    product_id: str
    seller_id: str
    title: str
    description: str
    starting_price: float
    reserve_price: float | None = None
    buy_now_price: float | None = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=7))
    status: AuctionStatus = AuctionStatus.DRAFT
    bids: list[Bid] = field(default_factory=list)
    uuid: str = field(default_factory=lambda: str(uuid4()))
    minimum_increment: float = 1.0
    sealed_bid: bool = False
    category: str = "electronics"
    tags: list[str] = field(default_factory=list)

    @property
    def current_price(self) -> float:
        """Get the current highest bid or starting price."""
        if not self.bids:
            return self.starting_price
        return max(bid.amount for bid in self.bids)

    @property
    def highest_bid(self) -> Bid | None:
        """Get the highest bid."""
        if not self.bids:
            return None
        return max(self.bids, key=lambda b: b.amount)

    @property
    def bid_count(self) -> int:
        """Get the total number of bids."""
        return len(self.bids)

    @property
    def is_active(self) -> bool:
        """Check if auction is currently active."""
        now = datetime.now()
        return self.status == AuctionStatus.ACTIVE and self.start_time <= now < self.end_time

    @property
    def time_remaining(self) -> timedelta:
        """Get time remaining in auction."""
        if not self.is_active:
            return timedelta(0)
        return self.end_time - datetime.now()

    def meets_reserve(self) -> bool:
        """Check if current price meets reserve."""
        if self.reserve_price is None:
            return True
        return self.current_price >= self.reserve_price


class BiddingSystem:
    """
    Manages auctions and bidding operations.

    Provides functionality for:
    - Creating and managing auctions
    - Placing and validating bids
    - Automatic bid extensions
    - Winner notification
    """

    def __init__(
        self,
        auto_extend_minutes: int = 5,
        extension_threshold_minutes: int = 5,
    ) -> None:
        """
        Initialize bidding system.

        Args:
            auto_extend_minutes: Minutes to extend auction on late bids
            extension_threshold_minutes: Time before end to trigger extension
        """
        self.auctions: dict[str, Auction] = {}
        self.auto_extend_minutes = auto_extend_minutes
        self.extension_threshold_minutes = extension_threshold_minutes
        self._bid_callbacks: list[Callable[[Bid], None]] = []
        self._auction_end_callbacks: list[Callable[[Auction], None]] = []

    def create_auction(
        self,
        product_id: str,
        seller_id: str,
        title: str,
        description: str,
        starting_price: float,
        duration_days: int = 7,
        reserve_price: float | None = None,
        buy_now_price: float | None = None,
        sealed_bid: bool = False,
    ) -> Auction:
        """
        Create a new auction.

        Args:
            product_id: ID of the product being auctioned
            seller_id: ID of the seller
            title: Auction title
            description: Detailed description
            starting_price: Starting bid price
            duration_days: Auction duration in days
            reserve_price: Optional reserve price
            buy_now_price: Optional buy now price
            sealed_bid: Use sealed-bid format

        Returns:
            Created Auction object
        """
        start_time = datetime.now()
        end_time = start_time + timedelta(days=duration_days)

        auction = Auction(
            product_id=product_id,
            seller_id=seller_id,
            title=title,
            description=description,
            starting_price=starting_price,
            reserve_price=reserve_price,
            buy_now_price=buy_now_price,
            start_time=start_time,
            end_time=end_time,
            status=AuctionStatus.SCHEDULED,
            sealed_bid=sealed_bid,
        )

        self.auctions[auction.uuid] = auction
        return auction

    def start_auction(self, auction_id: str) -> bool:
        """
        Start an auction.

        Args:
            auction_id: ID of auction to start

        Returns:
            True if started successfully
        """
        if auction_id not in self.auctions:
            return False

        auction = self.auctions[auction_id]
        if auction.status != AuctionStatus.SCHEDULED:
            return False

        auction.status = AuctionStatus.ACTIVE
        auction.start_time = datetime.now()
        return True

    def place_bid(
        self,
        auction_id: str,
        bidder_id: str,
        amount: float,
        notes: str = "",
    ) -> tuple[bool, str]:
        """
        Place a bid on an auction.

        Args:
            auction_id: ID of the auction
            bidder_id: ID of the bidder
            amount: Bid amount
            notes: Optional notes

        Returns:
            Tuple of (success, message)
        """
        if auction_id not in self.auctions:
            return False, "Auction not found"

        auction = self.auctions[auction_id]

        # Validate auction status
        if not auction.is_active:
            return False, "Auction is not active"

        # Validate bid amount
        min_bid = auction.current_price + auction.minimum_increment
        if amount < min_bid:
            return False, f"Bid must be at least {min_bid}"

        # Prevent self-bidding
        if bidder_id == auction.seller_id:
            return False, "Cannot bid on own auction"

        # Mark previous highest bid as outbid
        if auction.highest_bid:
            auction.highest_bid.status = BidStatus.OUTBID

        # Create and add new bid
        bid = Bid(
            auction_id=auction_id,
            bidder_id=bidder_id,
            amount=amount,
            status=BidStatus.ACCEPTED,
            notes=notes,
        )
        auction.bids.append(bid)

        # Check for auto-extend
        self._check_auto_extend(auction)

        # Notify callbacks
        for callback in self._bid_callbacks:
            callback(bid)

        # Check for buy now
        if auction.buy_now_price and amount >= auction.buy_now_price:
            self._end_auction(auction, bid)
            return True, "Buy now price met - auction ended"

        return True, "Bid placed successfully"

    def buy_now(self, auction_id: str, buyer_id: str) -> tuple[bool, str]:
        """
        Execute buy now option.

        Args:
            auction_id: ID of the auction
            buyer_id: ID of the buyer

        Returns:
            Tuple of (success, message)
        """
        if auction_id not in self.auctions:
            return False, "Auction not found"

        auction = self.auctions[auction_id]

        if not auction.is_active:
            return False, "Auction is not active"

        if not auction.buy_now_price:
            return False, "Buy now not available"

        if buyer_id == auction.seller_id:
            return False, "Cannot buy own item"

        # Create buy now bid
        bid = Bid(
            auction_id=auction_id,
            bidder_id=buyer_id,
            amount=auction.buy_now_price,
            status=BidStatus.WINNING,
        )
        auction.bids.append(bid)

        self._end_auction(auction, bid)
        return True, "Purchase successful"

    def end_auction(self, auction_id: str) -> Auction | None:
        """
        Manually end an auction.

        Args:
            auction_id: ID of auction to end

        Returns:
            Ended auction or None if not found
        """
        if auction_id not in self.auctions:
            return None

        auction = self.auctions[auction_id]
        self._end_auction(auction)
        return auction

    def _end_auction(self, auction: Auction, winning_bid: Bid | None = None) -> None:
        """End an auction and determine winner."""
        if winning_bid is None:
            winning_bid = auction.highest_bid

        if winning_bid and auction.meets_reserve():
            auction.status = AuctionStatus.SOLD
            winning_bid.status = BidStatus.WINNING
        else:
            auction.status = AuctionStatus.ENDED

        # Notify callbacks
        for callback in self._auction_end_callbacks:
            callback(auction)

    def _check_auto_extend(self, auction: Auction) -> None:
        """Check if auction should be extended due to late bid."""
        time_remaining = auction.time_remaining
        threshold = timedelta(minutes=self.extension_threshold_minutes)

        if time_remaining < threshold:
            extension = timedelta(minutes=self.auto_extend_minutes)
            auction.end_time += extension

    def get_auction(self, auction_id: str) -> Auction | None:
        """Get an auction by ID."""
        return self.auctions.get(auction_id)

    def get_active_auctions(self) -> list[Auction]:
        """Get all active auctions."""
        self._update_auction_statuses()
        return [a for a in self.auctions.values() if a.status == AuctionStatus.ACTIVE]

    def get_auctions_by_category(self, category: str) -> list[Auction]:
        """Get auctions by category."""
        return [a for a in self.auctions.values() if a.category == category]

    def get_user_bids(self, user_id: str) -> list[Bid]:
        """Get all bids by a user."""
        bids = []
        for auction in self.auctions.values():
            for bid in auction.bids:
                if bid.bidder_id == user_id:
                    bids.append(bid)
        return bids

    def get_user_auctions(self, user_id: str) -> list[Auction]:
        """Get all auctions by a seller."""
        return [a for a in self.auctions.values() if a.seller_id == user_id]

    def _update_auction_statuses(self) -> None:
        """Update auction statuses based on time."""
        now = datetime.now()
        for auction in self.auctions.values():
            if auction.status == AuctionStatus.SCHEDULED and now >= auction.start_time:
                auction.status = AuctionStatus.ACTIVE
            elif auction.status == AuctionStatus.ACTIVE and now >= auction.end_time:
                self._end_auction(auction)

    def on_bid(self, callback: Callable[[Bid], None]) -> None:
        """Register a callback for new bids."""
        self._bid_callbacks.append(callback)

    def on_auction_end(self, callback: Callable[[Auction], None]) -> None:
        """Register a callback for auction endings."""
        self._auction_end_callbacks.append(callback)

    def get_statistics(self) -> dict[str, Any]:
        """Get bidding system statistics."""
        self._update_auction_statuses()

        total_auctions = len(self.auctions)
        active_auctions = len(
            [a for a in self.auctions.values() if a.status == AuctionStatus.ACTIVE]
        )
        completed_auctions = len(
            [
                a
                for a in self.auctions.values()
                if a.status in (AuctionStatus.SOLD, AuctionStatus.ENDED)
            ]
        )

        total_bids = sum(len(a.bids) for a in self.auctions.values())
        total_value = sum(
            a.current_price for a in self.auctions.values() if a.status == AuctionStatus.SOLD
        )

        return {
            "total_auctions": total_auctions,
            "active_auctions": active_auctions,
            "completed_auctions": completed_auctions,
            "total_bids": total_bids,
            "total_value": total_value,
        }
