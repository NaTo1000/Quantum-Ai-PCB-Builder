"""Custom exceptions for the Quantum PCB Builder system.

This module provides a comprehensive exception hierarchy for precise error handling
across all modules of the system.
"""

from __future__ import annotations

from typing import Any


class QuantumPCBError(Exception):
    """Base exception for all Quantum PCB Builder errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "QPB_UNKNOWN"
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize exception to dictionary for logging/API responses."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


# ============================================================================
# Validation Errors
# ============================================================================


class ValidationError(QuantumPCBError):
    """Raised when validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="QPB_VALIDATION",
            details={"field": field, "value": str(value), **(details or {})},
        )
        self.field = field
        self.value = value


class ComponentValidationError(ValidationError):
    """Raised when component validation fails."""

    def __init__(
        self,
        message: str,
        component_id: str | None = None,
        component_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            details={
                "component_id": component_id,
                "component_type": component_type,
                **kwargs,
            },
        )
        self.component_id = component_id
        self.component_type = component_type


class DesignValidationError(ValidationError):
    """Raised when design validation fails."""

    def __init__(
        self,
        message: str,
        design_id: str | None = None,
        issues: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            details={"design_id": design_id, "issues": issues or [], **kwargs},
        )
        self.design_id = design_id
        self.issues = issues or []


class LayoutValidationError(ValidationError):
    """Raised when layout validation fails."""

    def __init__(
        self,
        message: str,
        layout_id: str | None = None,
        violations: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            details={"layout_id": layout_id, "violations": violations or [], **kwargs},
        )
        self.layout_id = layout_id
        self.violations = violations or []


# ============================================================================
# Component Errors
# ============================================================================


class ComponentError(QuantumPCBError):
    """Base exception for component-related errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message=message, error_code="QPB_COMPONENT", details=kwargs)


class ComponentNotFoundError(ComponentError):
    """Raised when a component cannot be found."""

    def __init__(self, component_id: str) -> None:
        super().__init__(
            message=f"Component not found: {component_id}",
            component_id=component_id,
        )
        self.component_id = component_id


class ComponentAlreadyExistsError(ComponentError):
    """Raised when attempting to add a duplicate component."""

    def __init__(self, component_id: str) -> None:
        super().__init__(
            message=f"Component already exists: {component_id}",
            component_id=component_id,
        )
        self.component_id = component_id


class IncompatibleComponentsError(ComponentError):
    """Raised when components are incompatible."""

    def __init__(
        self,
        component_a_id: str,
        component_b_id: str,
        reason: str,
    ) -> None:
        super().__init__(
            message=f"Incompatible components: {component_a_id} and {component_b_id}. {reason}",
            component_a_id=component_a_id,
            component_b_id=component_b_id,
            reason=reason,
        )


# ============================================================================
# Design Errors
# ============================================================================


class DesignError(QuantumPCBError):
    """Base exception for design-related errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message=message, error_code="QPB_DESIGN", details=kwargs)


class DesignNotFoundError(DesignError):
    """Raised when a design cannot be found."""

    def __init__(self, design_id: str) -> None:
        super().__init__(
            message=f"Design not found: {design_id}",
            design_id=design_id,
        )
        self.design_id = design_id


class DesignLockedError(DesignError):
    """Raised when attempting to modify a locked design."""

    def __init__(self, design_id: str, reason: str = "Design is locked") -> None:
        super().__init__(
            message=f"Cannot modify design {design_id}: {reason}",
            design_id=design_id,
            reason=reason,
        )


# ============================================================================
# Layout Errors
# ============================================================================


class LayoutError(QuantumPCBError):
    """Base exception for layout-related errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message=message, error_code="QPB_LAYOUT", details=kwargs)


class PlacementError(LayoutError):
    """Raised when component placement fails."""

    def __init__(
        self,
        component_id: str,
        position: tuple[float, float] | None = None,
        reason: str = "Invalid placement",
    ) -> None:
        super().__init__(
            message=f"Cannot place component {component_id}: {reason}",
            component_id=component_id,
            position=position,
            reason=reason,
        )


class OutOfBoundsError(LayoutError):
    """Raised when placement is outside layout bounds."""

    def __init__(
        self,
        x: float,
        y: float,
        bounds: tuple[float, float, float, float],
    ) -> None:
        super().__init__(
            message=f"Position ({x}, {y}) is outside bounds {bounds}",
            x=x,
            y=y,
            bounds=bounds,
        )


class ConnectionError(LayoutError):
    """Raised when component connection fails."""

    def __init__(
        self,
        source_id: str,
        target_id: str,
        reason: str = "Cannot establish connection",
    ) -> None:
        super().__init__(
            message=f"Cannot connect {source_id} to {target_id}: {reason}",
            source_id=source_id,
            target_id=target_id,
            reason=reason,
        )


# ============================================================================
# Marketplace Errors
# ============================================================================


class MarketplaceError(QuantumPCBError):
    """Base exception for marketplace-related errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message=message, error_code="QPB_MARKETPLACE", details=kwargs)


class ListingNotFoundError(MarketplaceError):
    """Raised when a listing cannot be found."""

    def __init__(self, listing_id: str) -> None:
        super().__init__(
            message=f"Listing not found: {listing_id}",
            listing_id=listing_id,
        )


class BidError(MarketplaceError):
    """Raised when a bid operation fails."""

    def __init__(self, message: str, listing_id: str, **kwargs: Any) -> None:
        super().__init__(message=message, listing_id=listing_id, **kwargs)


class InvalidBidError(BidError):
    """Raised when a bid is invalid."""

    def __init__(
        self,
        listing_id: str,
        bid_amount: float,
        reason: str,
    ) -> None:
        super().__init__(
            message=f"Invalid bid of {bid_amount} on listing {listing_id}: {reason}",
            listing_id=listing_id,
            bid_amount=bid_amount,
            reason=reason,
        )


class ListingExpiredError(MarketplaceError):
    """Raised when attempting to interact with an expired listing."""

    def __init__(self, listing_id: str) -> None:
        super().__init__(
            message=f"Listing has expired: {listing_id}",
            listing_id=listing_id,
        )


# ============================================================================
# Workflow Errors
# ============================================================================


class WorkflowError(QuantumPCBError):
    """Base exception for workflow-related errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message=message, error_code="QPB_WORKFLOW", details=kwargs)


class WorkflowNotFoundError(WorkflowError):
    """Raised when a workflow cannot be found."""

    def __init__(self, workflow_id: str) -> None:
        super().__init__(
            message=f"Workflow not found: {workflow_id}",
            workflow_id=workflow_id,
        )


class WorkflowStepError(WorkflowError):
    """Raised when a workflow step fails."""

    def __init__(
        self,
        step_name: str,
        workflow_id: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message=f"Workflow step '{step_name}' failed",
            step_name=step_name,
            workflow_id=workflow_id,
            cause=str(cause) if cause else None,
        )
        self.step_name = step_name
        self.__cause__ = cause


class PipelineError(WorkflowError):
    """Raised when a pipeline operation fails."""

    def __init__(
        self,
        stage: str,
        pipeline_id: str | None = None,
        reason: str = "Pipeline stage failed",
    ) -> None:
        super().__init__(
            message=f"Pipeline stage '{stage}' failed: {reason}",
            stage=stage,
            pipeline_id=pipeline_id,
            reason=reason,
        )


# ============================================================================
# AI/Optimizer Errors
# ============================================================================


class AIError(QuantumPCBError):
    """Base exception for AI-related errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message=message, error_code="QPB_AI", details=kwargs)


class DesignGenerationError(AIError):
    """Raised when AI design generation fails."""

    def __init__(
        self,
        reason: str,
        requirements: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"Failed to generate design: {reason}",
            reason=reason,
            requirements=requirements,
        )


class OptimizationError(AIError):
    """Raised when layout optimization fails."""

    def __init__(
        self,
        goal: str,
        reason: str,
        layout_id: str | None = None,
    ) -> None:
        super().__init__(
            message=f"Optimization for '{goal}' failed: {reason}",
            goal=goal,
            reason=reason,
            layout_id=layout_id,
        )


# ============================================================================
# Configuration Errors
# ============================================================================


class ConfigurationError(QuantumPCBError):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        expected: str | None = None,
        actual: str | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="QPB_CONFIG",
            details={
                "config_key": config_key,
                "expected": expected,
                "actual": actual,
            },
        )


# ============================================================================
# I/O Errors
# ============================================================================


class IOError(QuantumPCBError):
    """Base exception for I/O-related errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message=message, error_code="QPB_IO", details=kwargs)


class SerializationError(IOError):
    """Raised when serialization fails."""

    def __init__(
        self,
        message: str,
        object_type: str | None = None,
    ) -> None:
        super().__init__(
            message=f"Serialization error: {message}",
            object_type=object_type,
        )


class DeserializationError(IOError):
    """Raised when deserialization fails."""

    def __init__(
        self,
        message: str,
        target_type: str | None = None,
        data_sample: str | None = None,
    ) -> None:
        super().__init__(
            message=f"Deserialization error: {message}",
            target_type=target_type,
            data_sample=data_sample,
        )
