"""Tests for manufacturing and marketplace modules."""

import pytest

from quantum_pcb_builder.core.component import Component, ComponentType, Footprint
from quantum_pcb_builder.core.pcb import PCBBoard, Via
from quantum_pcb_builder.manufacturing.cost_estimator import (
    CostEstimator,
    FinishType,
    ManufacturingSpecs,
)
from quantum_pcb_builder.manufacturing.exporter import (
    BOMExporter,
    ExportFormat,
    GerberExporter,
)
from quantum_pcb_builder.marketplace.bidding import (
    AuctionStatus,
    BiddingSystem,
)
from quantum_pcb_builder.marketplace.product import (
    Product,
    ProductCatalog,
    ProductCategory,
)


class TestGerberExporter:
    """Tests for Gerber exporter."""

    @pytest.fixture
    def sample_board(self) -> PCBBoard:
        """Create a sample board for testing."""
        board = PCBBoard(
            name="TestBoard",
            width_mm=100.0,
            height_mm=80.0,
            layer_count=2,
        )
        comp = Component(
            name="U1",
            component_type=ComponentType.IC,
            footprint=Footprint("QFN-32", 5.0, 5.0, 32),
        )
        board.place_component(comp, (50.0, 40.0))
        return board

    def test_exporter_creation(self) -> None:
        """Test Gerber exporter initialization."""
        exporter = GerberExporter(precision=6, units="mm")
        assert exporter.precision == 6
        assert exporter.units == "mm"

    def test_export_generates_files(self, sample_board: PCBBoard) -> None:
        """Test export generates expected files."""
        exporter = GerberExporter()
        result = exporter.export(sample_board)

        assert result.success is True
        assert len(result.files) > 0
        assert any("Top_Cu" in name for name in result.files)
        assert any("Bottom_Cu" in name for name in result.files)
        assert any("Drill" in name for name in result.files)

    def test_export_gerber_format(self, sample_board: PCBBoard) -> None:
        """Test Gerber file format."""
        exporter = GerberExporter()
        result = exporter.export(sample_board)

        for filename, content in result.files.items():
            if filename.endswith(".gbr"):
                assert "G04" in content
                assert "M02*" in content


class TestBOMExporter:
    """Tests for BOM exporter."""

    @pytest.fixture
    def sample_board(self) -> PCBBoard:
        """Create a sample board for testing."""
        board = PCBBoard(name="TestBoard")
        board.place_component(
            Component(name="R1", component_type=ComponentType.RESISTOR, value="10k"),
            (10.0, 10.0),
        )
        board.place_component(
            Component(name="R2", component_type=ComponentType.RESISTOR, value="10k"),
            (20.0, 10.0),
        )
        board.place_component(
            Component(name="C1", component_type=ComponentType.CAPACITOR, value="100nF"),
            (30.0, 10.0),
        )
        return board

    def test_export_csv(self, sample_board: PCBBoard) -> None:
        """Test CSV BOM export."""
        exporter = BOMExporter(format=ExportFormat.BOM_CSV)
        result = exporter.export(sample_board)

        assert result.success is True
        assert any(name.endswith(".csv") for name in result.files)

    def test_export_json(self, sample_board: PCBBoard) -> None:
        """Test JSON BOM export."""
        exporter = BOMExporter(format=ExportFormat.BOM_JSON)
        result = exporter.export(sample_board)

        assert result.success is True
        assert any(name.endswith(".json") for name in result.files)

    def test_grouped_bom(self, sample_board: PCBBoard) -> None:
        """Test grouped BOM contains consolidated entries."""
        exporter = BOMExporter(format=ExportFormat.BOM_CSV, group_by_value=True)
        result = exporter.export(sample_board)

        csv_content = list(result.files.values())[0]
        lines = csv_content.strip().split("\n")
        assert len(lines) == 3


class TestCostEstimator:
    """Tests for cost estimation."""

    @pytest.fixture
    def sample_board(self) -> PCBBoard:
        """Create a sample board."""
        board = PCBBoard(
            name="Test",
            width_mm=100.0,
            height_mm=80.0,
            layer_count=4,
        )
        board.vias.append(Via(position=(10.0, 10.0), diameter_mm=0.6, drill_mm=0.3))
        board.vias.append(Via(position=(20.0, 20.0), diameter_mm=0.6, drill_mm=0.3))
        return board

    def test_basic_estimate(self, sample_board: PCBBoard) -> None:
        """Test basic cost estimation."""
        estimator = CostEstimator()
        quote = estimator.estimate(sample_board)

        assert quote.board_name == "Test"
        assert quote.unit_price > 0
        assert quote.total_price > 0

    def test_quantity_affects_price(self, sample_board: PCBBoard) -> None:
        """Test quantity pricing."""
        estimator = CostEstimator()

        quote_10 = estimator.estimate(sample_board, ManufacturingSpecs(quantity=10))
        quote_100 = estimator.estimate(sample_board, ManufacturingSpecs(quantity=100))

        assert quote_100.unit_price < quote_10.unit_price

    def test_finish_affects_cost(self, sample_board: PCBBoard) -> None:
        """Test surface finish cost."""
        estimator = CostEstimator()

        quote_hasl = estimator.estimate(sample_board, ManufacturingSpecs(finish=FinishType.HASL))
        quote_enig = estimator.estimate(sample_board, ManufacturingSpecs(finish=FinishType.ENIG))

        assert quote_enig.unit_price > quote_hasl.unit_price

    def test_compare_manufacturers(self, sample_board: PCBBoard) -> None:
        """Test manufacturer comparison."""
        estimator = CostEstimator()
        specs = ManufacturingSpecs(quantity=50)

        quotes = estimator.compare_manufacturers(sample_board, specs)

        assert len(quotes) > 1
        assert quotes[0].total_price <= quotes[-1].total_price


class TestBiddingSystem:
    """Tests for bidding system."""

    def test_create_auction(self) -> None:
        """Test auction creation."""
        system = BiddingSystem()

        auction = system.create_auction(
            product_id="prod-1",
            seller_id="seller-1",
            title="ESP32 Dev Board Design",
            description="Complete PCB design for ESP32",
            starting_price=50.0,
            duration_days=7,
        )

        assert auction.title == "ESP32 Dev Board Design"
        assert auction.starting_price == 50.0
        assert auction.status == AuctionStatus.SCHEDULED

    def test_start_auction(self) -> None:
        """Test starting an auction."""
        system = BiddingSystem()
        auction = system.create_auction(
            product_id="prod-1",
            seller_id="seller-1",
            title="Test",
            description="Test",
            starting_price=10.0,
        )

        result = system.start_auction(auction.uuid)

        assert result is True
        assert auction.status == AuctionStatus.ACTIVE

    def test_place_bid(self) -> None:
        """Test placing a bid."""
        system = BiddingSystem()
        auction = system.create_auction(
            product_id="prod-1",
            seller_id="seller-1",
            title="Test",
            description="Test",
            starting_price=10.0,
        )
        system.start_auction(auction.uuid)

        success, message = system.place_bid(auction.uuid, "bidder-1", 15.0)

        assert success is True
        assert auction.current_price == 15.0
        assert len(auction.bids) == 1

    def test_bid_must_be_higher(self) -> None:
        """Test bid must be higher than current."""
        system = BiddingSystem()
        auction = system.create_auction(
            product_id="prod-1",
            seller_id="seller-1",
            title="Test",
            description="Test",
            starting_price=10.0,
        )
        auction.minimum_increment = 1.0
        system.start_auction(auction.uuid)
        system.place_bid(auction.uuid, "bidder-1", 15.0)

        success, message = system.place_bid(auction.uuid, "bidder-2", 14.0)

        assert success is False
        assert "at least" in message

    def test_buy_now(self) -> None:
        """Test buy now functionality."""
        system = BiddingSystem()
        auction = system.create_auction(
            product_id="prod-1",
            seller_id="seller-1",
            title="Test",
            description="Test",
            starting_price=10.0,
            buy_now_price=100.0,
        )
        system.start_auction(auction.uuid)

        success, message = system.buy_now(auction.uuid, "buyer-1")

        assert success is True
        assert auction.status == AuctionStatus.SOLD


class TestProductCatalog:
    """Tests for product catalog."""

    def test_add_product(self) -> None:
        """Test adding a product."""
        catalog = ProductCatalog()
        product = Product(
            name="IoT Sensor Board",
            description="Temperature and humidity sensor",
            category=ProductCategory.IOT_DEVICE,
            seller_id="seller-1",
        )

        uuid = catalog.add_product(product)

        assert uuid == product.uuid
        assert product.uuid in catalog.products

    def test_create_listing(self) -> None:
        """Test creating a listing."""
        catalog = ProductCatalog()
        product = Product(
            name="Motor Controller",
            description="BLDC motor controller",
            category=ProductCategory.MOTOR_CONTROL,
            seller_id="seller-1",
        )
        catalog.add_product(product)

        listing = catalog.create_listing(product, price=99.99)

        assert listing.price == 99.99
        assert listing.title == "Motor Controller"

    def test_search_products(self) -> None:
        """Test product search."""
        catalog = ProductCatalog()

        for i, name in enumerate(["IoT Sensor", "Motor Driver", "Power Module"]):
            product = Product(
                name=name,
                description=f"Description for {name}",
                category=ProductCategory.IOT_DEVICE,
                seller_id="seller-1",
            )
            catalog.add_product(product)
            listing = catalog.create_listing(product, price=50.0 + i * 10)
            catalog.publish_listing(listing.uuid)

        results = catalog.search_products(query="sensor")

        assert len(results) == 1
        assert "Sensor" in results[0].title

    def test_search_by_category(self) -> None:
        """Test search by category."""
        catalog = ProductCatalog()

        product1 = Product(
            name="Sensor",
            description="Test",
            category=ProductCategory.SENSOR_MODULE,
            seller_id="s1",
        )
        product2 = Product(
            name="Motor",
            description="Test",
            category=ProductCategory.MOTOR_CONTROL,
            seller_id="s1",
        )

        catalog.add_product(product1)
        catalog.add_product(product2)
        catalog.create_listing(product1, 50.0)
        catalog.create_listing(product2, 60.0)
        catalog.publish_listing(product1.uuid)
        catalog.publish_listing(product2.uuid)

        results = catalog.search_products(category=ProductCategory.SENSOR_MODULE)

        assert len(results) == 1
        assert results[0].title == "Sensor"
