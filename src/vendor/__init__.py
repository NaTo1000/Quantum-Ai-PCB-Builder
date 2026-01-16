"""Vendor matching module for foundry and assembly services."""

from .matcher import (
    VendorMatcher,
    VendorQuote,
    VendorCapability,
    VendorType,
    PackagingType,
    DesignRequirements,
)

__all__ = [
    "VendorMatcher",
    "VendorQuote",
    "VendorCapability",
    "VendorType",
    "PackagingType",
    "DesignRequirements",
]
