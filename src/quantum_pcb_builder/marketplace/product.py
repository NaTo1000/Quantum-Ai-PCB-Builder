"""
Product Management for PCB Marketplace.

This module provides product listing and management for the
PCB marketplace, including copyright and licensing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any
from uuid import uuid4


class ProductCategory(Enum):
    """Product categories in the marketplace."""

    IOT_DEVICE = auto()
    SENSOR_MODULE = auto()
    COMMUNICATION_MODULE = auto()
    POWER_MANAGEMENT = auto()
    MOTOR_CONTROL = auto()
    DISPLAY_MODULE = auto()
    AUDIO_MODULE = auto()
    DEVELOPMENT_BOARD = auto()
    CUSTOM_DESIGN = auto()


class LicenseType(Enum):
    """License types for PCB designs."""

    PROPRIETARY = auto()
    OPEN_SOURCE = auto()
    CREATIVE_COMMONS = auto()
    MIT = auto()
    GPL = auto()
    COMMERCIAL = auto()


class ProductStatus(Enum):
    """Status of a product listing."""

    DRAFT = auto()
    PENDING_REVIEW = auto()
    PUBLISHED = auto()
    ARCHIVED = auto()
    REJECTED = auto()


@dataclass
class DesignFile:
    """Represents a design file attached to a product."""

    filename: str
    file_type: str
    file_size_bytes: int
    description: str = ""
    version: str = "1.0"
    uuid: str = field(default_factory=lambda: str(uuid4()))
    uploaded_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProductListing:
    """
    Detailed product listing for marketplace.

    Contains all information needed for displaying and
    selling a PCB product.
    """

    title: str
    description: str
    category: ProductCategory
    price: float
    seller_id: str

    # Design information
    board_dimensions: tuple[float, float] = (0.0, 0.0)
    layer_count: int = 2
    component_count: int = 0

    # Files and documentation
    design_files: list[DesignFile] = field(default_factory=list)
    documentation_url: str = ""
    images: list[str] = field(default_factory=list)

    # Licensing
    license_type: LicenseType = LicenseType.PROPRIETARY
    license_terms: str = ""

    # Metadata
    status: ProductStatus = ProductStatus.DRAFT
    uuid: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: list[str] = field(default_factory=list)
    views: int = 0
    sales: int = 0
    rating: float = 0.0
    review_count: int = 0


@dataclass
class Product:
    """
    Core product representation for a PCB design.

    Contains essential product information and references
    to associated design data.
    """

    name: str
    description: str
    category: ProductCategory
    seller_id: str
    circuit_id: str | None = None
    board_id: str | None = None
    uuid: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    status: ProductStatus = ProductStatus.DRAFT

    # Specifications
    specifications: dict[str, Any] = field(default_factory=dict)

    # Pricing
    base_price: float = 0.0
    manufacturing_cost: float = 0.0

    def update_version(self, new_version: str) -> None:
        """Update product version."""
        self.version = new_version
        self.updated_at = datetime.now()

    @property
    def updated_at(self) -> datetime:
        """Get last update time."""
        return getattr(self, "_updated_at", self.created_at)

    @updated_at.setter
    def updated_at(self, value: datetime) -> None:
        """Set last update time."""
        self._updated_at = value


class ProductCatalog:
    """
    Manages product catalog for the marketplace.

    Provides CRUD operations and search functionality
    for products.
    """

    def __init__(self) -> None:
        """Initialize product catalog."""
        self.products: dict[str, Product] = {}
        self.listings: dict[str, ProductListing] = {}

    def add_product(self, product: Product) -> str:
        """
        Add a product to the catalog.

        Args:
            product: Product to add

        Returns:
            Product UUID
        """
        self.products[product.uuid] = product
        return product.uuid

    def get_product(self, product_id: str) -> Product | None:
        """Get a product by ID."""
        return self.products.get(product_id)

    def update_product(self, product: Product) -> bool:
        """
        Update an existing product.

        Args:
            product: Product with updates

        Returns:
            True if updated successfully
        """
        if product.uuid not in self.products:
            return False

        product.updated_at = datetime.now()
        self.products[product.uuid] = product
        return True

    def delete_product(self, product_id: str) -> bool:
        """
        Delete a product from the catalog.

        Args:
            product_id: ID of product to delete

        Returns:
            True if deleted successfully
        """
        if product_id not in self.products:
            return False

        del self.products[product_id]

        # Also remove listing if exists
        if product_id in self.listings:
            del self.listings[product_id]

        return True

    def create_listing(
        self,
        product: Product,
        price: float,
        description: str = "",
    ) -> ProductListing:
        """
        Create a marketplace listing for a product.

        Args:
            product: Product to list
            price: Listing price
            description: Extended description

        Returns:
            Created ProductListing
        """
        listing = ProductListing(
            title=product.name,
            description=description or product.description,
            category=product.category,
            price=price,
            seller_id=product.seller_id,
            uuid=product.uuid,
        )

        self.listings[product.uuid] = listing
        return listing

    def publish_listing(self, listing_id: str) -> bool:
        """
        Publish a listing to the marketplace.

        Args:
            listing_id: ID of listing to publish

        Returns:
            True if published successfully
        """
        if listing_id not in self.listings:
            return False

        listing = self.listings[listing_id]
        listing.status = ProductStatus.PUBLISHED
        listing.updated_at = datetime.now()
        return True

    def search_products(
        self,
        query: str | None = None,
        category: ProductCategory | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        tags: list[str] | None = None,
    ) -> list[ProductListing]:
        """
        Search for products in the catalog.

        Args:
            query: Search query string
            category: Filter by category
            min_price: Minimum price filter
            max_price: Maximum price filter
            tags: Filter by tags

        Returns:
            List of matching ProductListings
        """
        results = []

        for listing in self.listings.values():
            if listing.status != ProductStatus.PUBLISHED:
                continue

            # Query filter
            if query:
                query_lower = query.lower()
                if (
                    query_lower not in listing.title.lower()
                    and query_lower not in listing.description.lower()
                ):
                    continue

            # Category filter
            if category and listing.category != category:
                continue

            # Price filters
            if min_price is not None and listing.price < min_price:
                continue
            if max_price is not None and listing.price > max_price:
                continue

            # Tags filter
            if tags and not any(tag in listing.tags for tag in tags):
                continue

            results.append(listing)

        return results

    def get_featured_products(self, limit: int = 10) -> list[ProductListing]:
        """
        Get featured products based on rating and sales.

        Args:
            limit: Maximum number of products to return

        Returns:
            List of featured ProductListings
        """
        published = [
            listing
            for listing in self.listings.values()
            if listing.status == ProductStatus.PUBLISHED
        ]

        # Sort by rating * sales score
        scored = [(listing, listing.rating * (1 + listing.sales / 10)) for listing in published]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [listing for listing, _ in scored[:limit]]

    def get_products_by_seller(self, seller_id: str) -> list[Product]:
        """Get all products by a seller."""
        return [p for p in self.products.values() if p.seller_id == seller_id]

    def get_catalog_statistics(self) -> dict[str, Any]:
        """Get catalog statistics."""
        total_products = len(self.products)
        published_listings = len(
            [
                listing
                for listing in self.listings.values()
                if listing.status == ProductStatus.PUBLISHED
            ]
        )
        total_sales = sum(listing.sales for listing in self.listings.values())
        avg_rating = (
            sum(listing.rating for listing in self.listings.values()) / len(self.listings)
            if self.listings
            else 0.0
        )

        # Category breakdown
        categories: dict[str, int] = {}
        for listing in self.listings.values():
            cat_name = listing.category.name
            categories[cat_name] = categories.get(cat_name, 0) + 1

        return {
            "total_products": total_products,
            "published_listings": published_listings,
            "total_sales": total_sales,
            "average_rating": round(avg_rating, 2),
            "categories": categories,
        }
