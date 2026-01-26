"""Tests for the exceptions module."""

from __future__ import annotations

from quantum_pcb_builder.core.exceptions import (
    ComponentNotFoundError,
    ComponentValidationError,
    ConfigurationError,
    DesignGenerationError,
    DesignValidationError,
    InvalidBidError,
    LayoutValidationError,
    ListingExpiredError,
    OptimizationError,
    OutOfBoundsError,
    PipelineError,
    PlacementError,
    QuantumPCBError,
    SerializationError,
    ValidationError,
    WorkflowStepError,
)


class TestQuantumPCBError:
    """Tests for the base exception class."""

    def test_basic_exception(self) -> None:
        """Test creating a basic exception."""
        error = QuantumPCBError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.error_code == "QPB_UNKNOWN"
        assert error.details == {}

    def test_exception_with_code(self) -> None:
        """Test exception with custom error code."""
        error = QuantumPCBError("Error", error_code="CUSTOM_CODE")
        assert error.error_code == "CUSTOM_CODE"

    def test_exception_with_details(self) -> None:
        """Test exception with details."""
        error = QuantumPCBError("Error", details={"key": "value"})
        assert error.details["key"] == "value"

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        error = QuantumPCBError("Error", error_code="TEST", details={"x": 1})
        data = error.to_dict()
        assert data["error_type"] == "QuantumPCBError"
        assert data["error_code"] == "TEST"
        assert data["message"] == "Error"
        assert data["details"]["x"] == 1

    def test_str_representation(self) -> None:
        """Test string representation."""
        error = QuantumPCBError("Error message", error_code="ERR001")
        assert str(error) == "[ERR001] Error message"


class TestValidationErrors:
    """Tests for validation error classes."""

    def test_validation_error(self) -> None:
        """Test basic validation error."""
        error = ValidationError("Invalid value", field="name", value="")
        assert error.field == "name"
        assert error.value == ""
        assert "field" in error.details

    def test_component_validation_error(self) -> None:
        """Test component validation error."""
        error = ComponentValidationError(
            "Invalid component",
            component_id="abc123",
            component_type="sensor",
        )
        assert error.component_id == "abc123"
        assert error.component_type == "sensor"

    def test_design_validation_error(self) -> None:
        """Test design validation error."""
        issues = ["Missing power", "No MCU"]
        error = DesignValidationError(
            "Design invalid",
            design_id="design1",
            issues=issues,
        )
        assert error.design_id == "design1"
        assert error.issues == issues

    def test_layout_validation_error(self) -> None:
        """Test layout validation error."""
        error = LayoutValidationError(
            "Layout invalid",
            layout_id="layout1",
            violations=["Overlap detected"],
        )
        assert error.layout_id == "layout1"
        assert "Overlap detected" in error.violations


class TestComponentErrors:
    """Tests for component error classes."""

    def test_component_not_found(self) -> None:
        """Test component not found error."""
        error = ComponentNotFoundError("comp123")
        assert error.component_id == "comp123"
        assert "comp123" in str(error)


class TestLayoutErrors:
    """Tests for layout error classes."""

    def test_placement_error(self) -> None:
        """Test placement error."""
        error = PlacementError("comp1", position=(10.0, 20.0), reason="Overlap")
        assert "comp1" in str(error)
        assert "Overlap" in str(error)

    def test_out_of_bounds_error(self) -> None:
        """Test out of bounds error."""
        error = OutOfBoundsError(x=150.0, y=50.0, bounds=(0, 0, 100, 100))
        assert "150.0" in str(error)
        assert "50.0" in str(error)


class TestMarketplaceErrors:
    """Tests for marketplace error classes."""

    def test_invalid_bid_error(self) -> None:
        """Test invalid bid error."""
        error = InvalidBidError(
            listing_id="list1",
            bid_amount=50.0,
            reason="Below minimum",
        )
        assert "50.0" in str(error)
        assert "Below minimum" in str(error)

    def test_listing_expired_error(self) -> None:
        """Test listing expired error."""
        error = ListingExpiredError("list1")
        assert "list1" in str(error)


class TestWorkflowErrors:
    """Tests for workflow error classes."""

    def test_workflow_step_error(self) -> None:
        """Test workflow step error."""
        cause = ValueError("Bad input")
        error = WorkflowStepError("validate", workflow_id="wf1", cause=cause)
        assert error.step_name == "validate"
        assert error.__cause__ is cause

    def test_pipeline_error(self) -> None:
        """Test pipeline error."""
        error = PipelineError("optimization", reason="No solution found")
        assert "optimization" in str(error)


class TestAIErrors:
    """Tests for AI error classes."""

    def test_design_generation_error(self) -> None:
        """Test design generation error."""
        error = DesignGenerationError(
            reason="Insufficient requirements",
            requirements={"name": "test"},
        )
        assert "Insufficient requirements" in str(error)

    def test_optimization_error(self) -> None:
        """Test optimization error."""
        error = OptimizationError(
            goal="minimize_trace_length",
            reason="Convergence failed",
            layout_id="layout1",
        )
        assert "minimize_trace_length" in str(error)


class TestConfigurationErrors:
    """Tests for configuration error classes."""

    def test_configuration_error(self) -> None:
        """Test configuration error."""
        error = ConfigurationError(
            "Invalid config",
            config_key="api_key",
            expected="non-empty string",
            actual="",
        )
        assert error.details["config_key"] == "api_key"


class TestIOErrors:
    """Tests for I/O error classes."""

    def test_serialization_error(self) -> None:
        """Test serialization error."""
        error = SerializationError("Cannot serialize", object_type="Design")
        assert "Cannot serialize" in str(error)
        assert error.details["object_type"] == "Design"
