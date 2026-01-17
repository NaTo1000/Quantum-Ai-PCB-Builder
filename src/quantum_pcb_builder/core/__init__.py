"""Core module containing base classes and protocols."""

from quantum_pcb_builder.core.base import (
    BaseComponent,
    BaseDesign,
    ValidationResult,
)
from quantum_pcb_builder.core.events import (
    Event,
    EventBus,
    EventHandler,
)
from quantum_pcb_builder.core.protocols import (
    ComponentProtocol,
    DesignProtocol,
    MarketplaceProtocol,
    WorkflowProtocol,
)

__all__ = [
    "ComponentProtocol",
    "DesignProtocol",
    "MarketplaceProtocol",
    "WorkflowProtocol",
    "BaseComponent",
    "BaseDesign",
    "ValidationResult",
    "Event",
    "EventBus",
    "EventHandler",
]
