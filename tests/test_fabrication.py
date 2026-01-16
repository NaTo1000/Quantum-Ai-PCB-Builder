"""
Tests for the Fabrication Vendor module.
"""

import pytest
from datetime import datetime
from src.core.fabrication.vendor import (
    VendorRegistry, VendorInfo, QuoteEngine, OrderManager,
    PCBSpecification, Quote, Order, OrderStatus, VendorCapability
)


class TestVendorRegistry:
    """Test suite for the VendorRegistry class."""
    
    @pytest.fixture
    def registry(self):
        """Create a VendorRegistry instance for testing."""
        return VendorRegistry()
    
    def test_list_vendors_returns_list(self, registry):
        """Test that list_vendors returns a list."""
        vendors = registry.list_vendors()
        
        assert isinstance(vendors, list)
        assert len(vendors) > 0
    
    def test_get_vendor_by_id(self, registry):
        """Test getting vendor by ID."""
        vendors = registry.list_vendors()
        vendor_id = vendors[0].vendor_id
        
        vendor = registry.get_vendor(vendor_id)
        
        assert vendor is not None
        assert isinstance(vendor, VendorInfo)
    
    def test_get_nonexistent_vendor(self, registry):
        """Test getting a non-existent vendor returns None."""
        vendor = registry.get_vendor("nonexistent-vendor-id")
        
        assert vendor is None
    
    def test_filter_by_capability(self, registry):
        """Test filtering vendors by capability."""
        vendors = registry.list_vendors(capability=VendorCapability.PCB_PROTOTYPE)
        
        for vendor in vendors:
            assert VendorCapability.PCB_PROTOTYPE in vendor.capabilities
    
    def test_filter_by_country(self, registry):
        """Test filtering vendors by country."""
        vendors = registry.list_vendors(country="US")
        
        for vendor in vendors:
            assert "US" in vendor.countries_served
    
    def test_filter_by_rating(self, registry):
        """Test filtering vendors by minimum rating."""
        min_rating = 4.0
        vendors = registry.list_vendors(min_rating=min_rating)
        
        for vendor in vendors:
            assert vendor.rating >= min_rating
    
    def test_find_vendors_for_prototype(self, registry):
        """Test finding vendors for prototype designs."""
        vendors = registry.find_vendors_for_design(is_prototype=True)
        
        assert len(vendors) > 0
        for vendor in vendors:
            assert VendorCapability.PCB_PROTOTYPE in vendor.capabilities
    
    def test_find_vendors_with_assembly(self, registry):
        """Test finding vendors with assembly capability."""
        vendors = registry.find_vendors_for_design(
            is_prototype=True,
            needs_assembly=True
        )
        
        for vendor in vendors:
            assert VendorCapability.PCB_ASSEMBLY in vendor.capabilities
    
    def test_vendor_to_dict(self, registry):
        """Test VendorInfo conversion to dictionary."""
        vendor = registry.list_vendors()[0]
        vendor_dict = vendor.to_dict()
        
        assert isinstance(vendor_dict, dict)
        assert "vendor_id" in vendor_dict
        assert "name" in vendor_dict
        assert "capabilities" in vendor_dict


class TestPCBSpecification:
    """Test suite for PCBSpecification dataclass."""
    
    def test_specification_creation(self):
        """Test creating a PCBSpecification."""
        spec = PCBSpecification(
            board_size_mm=(50, 30),
            layers=4,
            quantity=20
        )
        
        assert spec.board_size_mm == (50, 30)
        assert spec.layers == 4
        assert spec.quantity == 20
    
    def test_specification_defaults(self):
        """Test PCBSpecification default values."""
        spec = PCBSpecification(board_size_mm=(100, 100))
        
        assert spec.layers == 2
        assert spec.thickness_mm == 1.6
        assert spec.copper_weight_oz == 1.0
        assert spec.surface_finish == "HASL"
        assert spec.solder_mask_color == "green"
    
    def test_specification_to_dict(self):
        """Test PCBSpecification conversion to dictionary."""
        spec = PCBSpecification(
            board_size_mm=(50, 30),
            layers=2
        )
        spec_dict = spec.to_dict()
        
        assert isinstance(spec_dict, dict)
        assert "board_size_mm" in spec_dict
        assert "layers" in spec_dict


class TestQuoteEngine:
    """Test suite for the QuoteEngine class."""
    
    @pytest.fixture
    def quote_engine(self):
        """Create a QuoteEngine instance for testing."""
        registry = VendorRegistry()
        return QuoteEngine(registry)
    
    @pytest.fixture
    def specification(self):
        """Create a test PCBSpecification."""
        return PCBSpecification(
            board_size_mm=(50, 30),
            layers=2,
            quantity=10
        )
    
    def test_generate_quote(self, quote_engine, specification):
        """Test generating a quote."""
        registry = VendorRegistry()
        vendors = registry.list_vendors(capability=VendorCapability.PCB_PROTOTYPE)
        vendor_id = vendors[0].vendor_id
        
        quote = quote_engine.generate_quote(vendor_id, specification)
        
        assert isinstance(quote, Quote)
        assert quote.vendor_id == vendor_id
        assert quote.unit_price_usd > 0
        assert quote.total_price_usd > 0
    
    def test_quote_has_lead_time(self, quote_engine, specification):
        """Test that quotes include lead time."""
        registry = VendorRegistry()
        vendors = registry.list_vendors(capability=VendorCapability.PCB_PROTOTYPE)
        vendor_id = vendors[0].vendor_id
        
        quote = quote_engine.generate_quote(vendor_id, specification)
        
        assert quote.lead_time_days > 0
    
    def test_quote_validity_period(self, quote_engine, specification):
        """Test that quotes have a validity period."""
        registry = VendorRegistry()
        vendors = registry.list_vendors(capability=VendorCapability.PCB_PROTOTYPE)
        vendor_id = vendors[0].vendor_id
        
        quote = quote_engine.generate_quote(vendor_id, specification)
        
        assert quote.valid_until > datetime.now()
    
    def test_compare_quotes(self, quote_engine, specification):
        """Test comparing quotes from multiple vendors."""
        quotes = quote_engine.compare_quotes(specification)
        
        assert len(quotes) > 0
        
        # Quotes should be sorted by total cost
        for i in range(len(quotes) - 1):
            cost_i = quotes[i].total_price_usd + quotes[i].tooling_cost_usd
            cost_j = quotes[i+1].total_price_usd + quotes[i+1].tooling_cost_usd
            assert cost_i <= cost_j
    
    def test_invalid_vendor_raises_error(self, quote_engine, specification):
        """Test that invalid vendor ID raises error."""
        with pytest.raises(ValueError):
            quote_engine.generate_quote("invalid-vendor", specification)
    
    def test_quote_to_dict(self, quote_engine, specification):
        """Test Quote conversion to dictionary."""
        registry = VendorRegistry()
        vendors = registry.list_vendors(capability=VendorCapability.PCB_PROTOTYPE)
        vendor_id = vendors[0].vendor_id
        
        quote = quote_engine.generate_quote(vendor_id, specification)
        quote_dict = quote.to_dict()
        
        assert isinstance(quote_dict, dict)
        assert "quote_id" in quote_dict
        assert "unit_price_usd" in quote_dict
        assert "total_price_usd" in quote_dict


class TestOrderManager:
    """Test suite for the OrderManager class."""
    
    @pytest.fixture
    def order_manager(self):
        """Create an OrderManager instance for testing."""
        return OrderManager()
    
    @pytest.fixture
    def quote(self):
        """Create a test Quote."""
        registry = VendorRegistry()
        quote_engine = QuoteEngine(registry)
        vendors = registry.list_vendors(capability=VendorCapability.PCB_PROTOTYPE)
        
        spec = PCBSpecification(board_size_mm=(50, 30))
        return quote_engine.generate_quote(vendors[0].vendor_id, spec)
    
    def test_create_order(self, order_manager, quote):
        """Test creating an order from a quote."""
        order = order_manager.create_order(quote)
        
        assert isinstance(order, Order)
        assert order.quote_id == quote.quote_id
        assert order.status == OrderStatus.PENDING_PAYMENT
    
    def test_get_order(self, order_manager, quote):
        """Test getting an order by ID."""
        order = order_manager.create_order(quote)
        
        retrieved = order_manager.get_order(order.order_id)
        
        assert retrieved is not None
        assert retrieved.order_id == order.order_id
    
    def test_update_order_status(self, order_manager, quote):
        """Test updating order status."""
        order = order_manager.create_order(quote)
        
        updated = order_manager.update_status(order.order_id, OrderStatus.PAID)
        
        assert updated.status == OrderStatus.PAID
    
    def test_add_tracking(self, order_manager, quote):
        """Test adding tracking information."""
        order = order_manager.create_order(quote)
        
        updated = order_manager.add_tracking(
            order.order_id,
            "TRACK123456",
            "DHL"
        )
        
        assert updated.tracking_number == "TRACK123456"
        assert updated.shipping_carrier == "DHL"
        assert updated.status == OrderStatus.SHIPPED
    
    def test_list_orders(self, order_manager, quote):
        """Test listing orders."""
        order1 = order_manager.create_order(quote)
        order2 = order_manager.create_order(quote)
        
        orders = order_manager.list_orders()
        
        assert len(orders) >= 2
    
    def test_list_orders_by_status(self, order_manager, quote):
        """Test listing orders filtered by status."""
        order = order_manager.create_order(quote)
        order_manager.update_status(order.order_id, OrderStatus.PAID)
        
        paid_orders = order_manager.list_orders(status=OrderStatus.PAID)
        
        for o in paid_orders:
            assert o.status == OrderStatus.PAID
    
    def test_order_to_dict(self, order_manager, quote):
        """Test Order conversion to dictionary."""
        order = order_manager.create_order(quote)
        order_dict = order.to_dict()
        
        assert isinstance(order_dict, dict)
        assert "order_id" in order_dict
        assert "status" in order_dict
        assert "created_at" in order_dict
