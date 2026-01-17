"""Tests for marketplace module."""

from datetime import datetime, timedelta

from quantum_pcb_builder.core.base import BaseDesign
from quantum_pcb_builder.marketplace.bidding import Bid, BiddingEngine
from quantum_pcb_builder.marketplace.listings import (
    Listing,
    ListingManager,
    ListingStatus,
)
from quantum_pcb_builder.marketplace.sales import (
    PaymentStatus,
    ProductionOrder,
    ProductionStatus,
    Sale,
    SalesManager,
)


class TestListing:
    """Tests for Listing class."""

    def test_create_listing(self) -> None:
        """Test creating a listing."""
        design = BaseDesign(name="Test Design")
        listing = Listing(
            design=design,
            seller_id="seller1",
            title="Great PCB",
            min_price=100.0,
        )
        assert listing.title == "Great PCB"
        assert listing.min_price == 100.0
        assert listing.status == ListingStatus.DRAFT

    def test_activate_listing(self) -> None:
        """Test activating a listing."""
        listing = Listing(title="Test", min_price=50.0)
        assert listing.activate()
        assert listing.status == ListingStatus.ACTIVE

    def test_close_listing(self) -> None:
        """Test closing a listing."""
        listing = Listing(title="Test", min_price=50.0)
        listing.activate()
        assert listing.close()
        assert listing.status == ListingStatus.CLOSED

    def test_mark_sold(self) -> None:
        """Test marking a listing as sold."""
        listing = Listing(title="Test", min_price=50.0)
        listing.activate()
        assert listing.mark_sold(150.0)
        assert listing.status == ListingStatus.SOLD
        assert listing.current_price == 150.0

    def test_expiration(self) -> None:
        """Test listing expiration."""
        listing = Listing(
            title="Test",
            min_price=50.0,
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        assert listing.is_expired()


class TestListingManager:
    """Tests for ListingManager."""

    def test_create_listing(self) -> None:
        """Test creating a listing through manager."""
        manager = ListingManager()
        design = BaseDesign(name="Test")

        listing = manager.create_listing(
            design=design,
            seller_id="seller1",
            title="Test Listing",
            min_price=100.0,
        )

        assert listing.title == "Test Listing"
        assert listing.design == design

    def test_get_listing(self) -> None:
        """Test getting a listing."""
        manager = ListingManager()
        design = BaseDesign(name="Test")
        created = manager.create_listing(
            design=design,
            seller_id="seller1",
            title="Test",
            min_price=50.0,
        )

        found = manager.get_listing(created.listing_id)
        assert found is not None
        assert found.listing_id == created.listing_id

    def test_list_active(self) -> None:
        """Test listing active listings."""
        manager = ListingManager()
        design = BaseDesign(name="Test")

        listing1 = manager.create_listing(
            design=design,
            seller_id="seller1",
            title="Test 1",
            min_price=50.0,
        )
        listing1.activate()

        manager.create_listing(
            design=design,
            seller_id="seller1",
            title="Test 2",
            min_price=100.0,
        )
        # Not activated

        active = manager.list_active()
        assert len(active) == 1
        assert active[0].listing_id == listing1.listing_id

    def test_search_listings(self) -> None:
        """Test searching listings."""
        manager = ListingManager()
        design = BaseDesign(name="Test")

        manager.create_listing(
            design=design,
            seller_id="seller1",
            title="IoT Sensor Board",
            min_price=50.0,
            tags=["iot", "sensor"],
        )

        manager.create_listing(
            design=design,
            seller_id="seller1",
            title="Power Controller",
            min_price=100.0,
            tags=["power"],
        )

        results = manager.search(query="sensor")
        assert len(results) == 1
        assert "Sensor" in results[0].title

        results = manager.search(tags=["iot"])
        assert len(results) == 1


class TestBid:
    """Tests for Bid class."""

    def test_create_bid(self) -> None:
        """Test creating a bid."""
        bid = Bid(
            listing_id="listing1",
            bidder_id="bidder1",
            amount=100.0,
        )
        assert bid.amount == 100.0
        assert bid.bidder_id == "bidder1"

    def test_serialize_bid(self) -> None:
        """Test serializing a bid."""
        bid = Bid(
            listing_id="listing1",
            bidder_id="bidder1",
            amount=100.0,
        )
        data = bid.to_dict()
        assert data["amount"] == 100.0


class TestBiddingEngine:
    """Tests for BiddingEngine."""

    def test_place_bid(self) -> None:
        """Test placing a bid."""
        engine = BiddingEngine()
        listing = Listing(
            seller_id="seller1",
            title="Test",
            min_price=50.0,
        )
        listing.activate()

        success, message = engine.place_bid(listing, "bidder1", 60.0)
        assert success
        assert listing.current_price == 60.0

    def test_bid_below_minimum(self) -> None:
        """Test bidding below minimum price."""
        engine = BiddingEngine()
        listing = Listing(
            seller_id="seller1",
            title="Test",
            min_price=100.0,
        )
        listing.activate()

        success, message = engine.place_bid(listing, "bidder1", 50.0)
        assert not success
        assert "at least" in message.lower()

    def test_bid_below_current(self) -> None:
        """Test bidding below current bid."""
        engine = BiddingEngine()
        listing = Listing(
            seller_id="seller1",
            title="Test",
            min_price=50.0,
        )
        listing.activate()

        engine.place_bid(listing, "bidder1", 100.0)
        success, message = engine.place_bid(listing, "bidder2", 80.0)
        assert not success

    def test_seller_cannot_bid(self) -> None:
        """Test that seller cannot bid on own listing."""
        engine = BiddingEngine()
        listing = Listing(
            seller_id="seller1",
            title="Test",
            min_price=50.0,
        )
        listing.activate()

        success, message = engine.place_bid(listing, "seller1", 100.0)
        assert not success
        assert "seller" in message.lower()

    def test_get_highest_bid(self) -> None:
        """Test getting highest bid."""
        engine = BiddingEngine()
        listing = Listing(
            seller_id="seller1",
            title="Test",
            min_price=50.0,
        )
        listing.activate()

        engine.place_bid(listing, "bidder1", 60.0)
        engine.place_bid(listing, "bidder2", 75.0)
        engine.place_bid(listing, "bidder1", 100.0)

        highest = engine.get_highest_bid(listing.listing_id)
        assert highest is not None
        assert highest.amount == 100.0
        assert highest.bidder_id == "bidder1"


class TestSale:
    """Tests for Sale class."""

    def test_create_sale(self) -> None:
        """Test creating a sale."""
        sale = Sale(
            listing_id="listing1",
            seller_id="seller1",
            buyer_id="buyer1",
            final_price=150.0,
        )
        assert sale.final_price == 150.0
        assert sale.payment_status == PaymentStatus.PENDING


class TestProductionOrder:
    """Tests for ProductionOrder class."""

    def test_create_order(self) -> None:
        """Test creating a production order."""
        order = ProductionOrder(
            design_id="design1",
            quantity=10,
            manufacturer_id="in_house",
        )
        assert order.quantity == 10
        assert order.status == ProductionStatus.PENDING

    def test_update_status(self) -> None:
        """Test updating order status."""
        order = ProductionOrder(design_id="design1", quantity=5)
        order.update_status(ProductionStatus.IN_PRODUCTION)
        assert order.status == ProductionStatus.IN_PRODUCTION

        order.update_status(ProductionStatus.DELIVERED)
        assert order.status == ProductionStatus.DELIVERED
        assert order.actual_completion is not None

    def test_add_note(self) -> None:
        """Test adding notes to order."""
        order = ProductionOrder(design_id="design1", quantity=5)
        order.add_note("Started production")
        assert len(order.notes) == 1


class TestSalesManager:
    """Tests for SalesManager."""

    def test_complete_sale(self) -> None:
        """Test completing a sale."""
        manager = SalesManager()
        design = BaseDesign(name="Test")
        listing = Listing(
            design=design,
            seller_id="seller1",
            title="Test",
            min_price=100.0,
        )
        listing.activate()

        sale = manager.complete_sale(listing, "buyer1", 150.0)
        assert sale.final_price == 150.0
        assert sale.buyer_id == "buyer1"
        assert listing.status == ListingStatus.SOLD

    def test_create_production_order(self) -> None:
        """Test creating a production order."""
        manager = SalesManager()
        design = BaseDesign(name="Test")

        order = manager.create_production_order(
            design=design,
            quantity=5,
            manufacturer_id="in_house",
        )

        assert order.quantity == 5
        assert order.manufacturer_id == "in_house"
        assert order.estimated_completion is not None

    def test_get_manufacturers(self) -> None:
        """Test getting available manufacturers."""
        manager = SalesManager()
        manufacturers = manager.get_manufacturers()
        assert "in_house" in manufacturers
        assert "partner_a" in manufacturers

    def test_revenue_report(self) -> None:
        """Test generating revenue report."""
        manager = SalesManager()
        design = BaseDesign(name="Test")

        listing1 = Listing(
            design=design,
            seller_id="seller1",
            title="Test 1",
            min_price=100.0,
        )
        listing1.activate()
        manager.complete_sale(listing1, "buyer1", 150.0)

        listing2 = Listing(
            design=design,
            seller_id="seller1",
            title="Test 2",
            min_price=200.0,
        )
        listing2.activate()
        manager.complete_sale(listing2, "buyer2", 300.0)

        report = manager.get_revenue_report()
        assert report["total_sales"] == 2
        assert report["total_revenue"] == 450.0
