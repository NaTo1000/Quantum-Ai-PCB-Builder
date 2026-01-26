"""Protocol definitions for the Quantum PCB Builder system.

This module defines the interfaces (protocols) that all components must implement
to ensure consistent behavior and integration across the system.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ComponentProtocol(Protocol):
    """Protocol for PCB components (chips, sensors, modules, etc.)."""

    @property
    def component_id(self) -> str:
        """Unique identifier for the component."""
        ...

    @property
    def component_type(self) -> str:
        """Type of component (e.g., 'microcontroller', 'sensor', 'module')."""
        ...

    @property
    def specifications(self) -> dict[str, Any]:
        """Component specifications and parameters."""
        ...

    def validate(self) -> bool:
        """Validate the component configuration."""
        ...

    def to_dict(self) -> dict[str, Any]:
        """Serialize component to dictionary."""
        ...


@runtime_checkable
class DesignProtocol(Protocol):
    """Protocol for PCB designs."""

    @property
    def design_id(self) -> str:
        """Unique identifier for the design."""
        ...

    @property
    def name(self) -> str:
        """Name of the design."""
        ...

    @property
    def components(self) -> list[ComponentProtocol]:
        """List of components in the design."""
        ...

    def add_component(self, component: ComponentProtocol) -> None:
        """Add a component to the design."""
        ...

    def remove_component(self, component_id: str) -> bool:
        """Remove a component from the design."""
        ...

    def validate(self) -> tuple[bool, list[str]]:
        """Validate the entire design. Returns (is_valid, list of issues)."""
        ...

    def to_dict(self) -> dict[str, Any]:
        """Serialize design to dictionary."""
        ...


@runtime_checkable
class MarketplaceProtocol(Protocol):
    """Protocol for marketplace operations."""

    @abstractmethod
    def list_design(self, design: DesignProtocol, min_price: float) -> str:
        """List a design for bidding. Returns listing ID."""
        ...

    @abstractmethod
    def place_bid(self, listing_id: str, bidder_id: str, amount: float) -> bool:
        """Place a bid on a listing."""
        ...

    @abstractmethod
    def get_highest_bid(self, listing_id: str) -> tuple[str, float] | None:
        """Get the highest bid for a listing. Returns (bidder_id, amount) or None."""
        ...

    @abstractmethod
    def close_listing(self, listing_id: str) -> tuple[bool, str]:
        """Close a listing and finalize the sale. Returns (success, message)."""
        ...


@runtime_checkable
class WorkflowProtocol(Protocol):
    """Protocol for workflow orchestration."""

    @property
    def workflow_id(self) -> str:
        """Unique identifier for the workflow."""
        ...

    @property
    def status(self) -> str:
        """Current status of the workflow."""
        ...

    @abstractmethod
    def start(self) -> bool:
        """Start the workflow execution."""
        ...

    @abstractmethod
    def pause(self) -> bool:
        """Pause the workflow execution."""
        ...

    @abstractmethod
    def resume(self) -> bool:
        """Resume a paused workflow."""
        ...

    @abstractmethod
    def cancel(self) -> bool:
        """Cancel the workflow execution."""
        ...

    @abstractmethod
    def get_progress(self) -> dict[str, Any]:
        """Get the current progress of the workflow."""
        ...
