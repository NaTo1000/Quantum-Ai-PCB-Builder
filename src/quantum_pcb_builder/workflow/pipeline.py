"""Design pipeline for end-to-end PCB design and production."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from quantum_pcb_builder.ai.designer import AIDesigner, DesignRequirements
from quantum_pcb_builder.ai.optimizer import LayoutOptimizer, OptimizationGoal
from quantum_pcb_builder.core.base import BaseDesign
from quantum_pcb_builder.core.events import Event, EventBus
from quantum_pcb_builder.marketplace.listings import ListingManager
from quantum_pcb_builder.marketplace.sales import SalesManager
from quantum_pcb_builder.pcb.validators import DesignValidator


class PipelineStage(Enum):
    """Stages in the design pipeline."""

    IDEATION = "ideation"
    DESIGN = "design"
    VALIDATION = "validation"
    OPTIMIZATION = "optimization"
    LISTING = "listing"
    SALE = "sale"
    PRODUCTION = "production"
    DELIVERY = "delivery"


@dataclass
class PipelineContext:
    """Context data passed through the pipeline."""

    pipeline_id: str = field(default_factory=lambda: str(uuid4()))
    requirements: DesignRequirements | None = None
    design: BaseDesign | None = None
    listing_id: str | None = None
    sale_id: str | None = None
    order_id: str | None = None
    current_stage: PipelineStage = PipelineStage.IDEATION
    stage_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize context to dictionary."""
        return {
            "pipeline_id": self.pipeline_id,
            "current_stage": self.current_stage.value,
            "listing_id": self.listing_id,
            "sale_id": self.sale_id,
            "order_id": self.order_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "stage_results": self.stage_results,
        }


class DesignPipeline:
    """End-to-end pipeline for PCB design, listing, and production."""

    def __init__(
        self,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the design pipeline."""
        self.event_bus = event_bus or EventBus()
        self.ai_designer = AIDesigner()
        self.optimizer = LayoutOptimizer()
        self.validator = DesignValidator()
        self.listing_manager = ListingManager()
        self.sales_manager = SalesManager()
        self._pipelines: dict[str, PipelineContext] = {}

    def create_pipeline(self, requirements: DesignRequirements) -> PipelineContext:
        """Create a new design pipeline."""
        context = PipelineContext(requirements=requirements)
        self._pipelines[context.pipeline_id] = context
        self._emit_event("pipeline_created", {"pipeline_id": context.pipeline_id})
        return context

    def run_ideation(self, context: PipelineContext) -> dict[str, Any]:
        """Run the ideation stage - brainstorm ideas."""
        context.current_stage = PipelineStage.IDEATION

        if not context.requirements:
            return {"success": False, "error": "No requirements provided"}

        # Get AI suggestions based on requirements
        suggestions = self.ai_designer.brainstorm(context.requirements.description)

        result = {
            "success": True,
            "suggestions": [s.to_dict() for s in suggestions],
            "suggestion_count": len(suggestions),
        }

        context.stage_results["ideation"] = result
        self._emit_event(
            "stage_completed",
            {
                "pipeline_id": context.pipeline_id,
                "stage": "ideation",
            },
        )

        return result

    def run_design(self, context: PipelineContext) -> dict[str, Any]:
        """Run the design stage - generate PCB layout."""
        context.current_stage = PipelineStage.DESIGN

        if not context.requirements:
            return {"success": False, "error": "No requirements provided"}

        # Generate design using AI
        layout = self.ai_designer.generate_design(context.requirements)
        context.design = layout

        result = {
            "success": True,
            "design_id": layout.design_id,
            "component_count": len(layout.components),
            "connection_count": len(layout.get_connections()),
        }

        context.stage_results["design"] = result
        self._emit_event(
            "stage_completed",
            {
                "pipeline_id": context.pipeline_id,
                "stage": "design",
            },
        )

        return result

    def run_validation(self, context: PipelineContext) -> dict[str, Any]:
        """Run the validation stage - validate the design."""
        context.current_stage = PipelineStage.VALIDATION

        if not context.design:
            return {"success": False, "error": "No design to validate"}

        validation_result = self.validator.validate(context.design)

        result = {
            "success": validation_result.is_valid,
            "is_valid": validation_result.is_valid,
            "errors": validation_result.errors,
            "warnings": validation_result.warnings,
        }

        context.stage_results["validation"] = result
        self._emit_event(
            "stage_completed",
            {
                "pipeline_id": context.pipeline_id,
                "stage": "validation",
            },
        )

        return result

    def run_optimization(self, context: PipelineContext) -> dict[str, Any]:
        """Run the optimization stage - optimize the layout."""
        context.current_stage = PipelineStage.OPTIMIZATION

        if not context.design:
            return {"success": False, "error": "No design to optimize"}

        # Import the layout type for type checking
        from quantum_pcb_builder.pcb.layout import PCBLayout

        if not isinstance(context.design, PCBLayout):
            return {"success": False, "error": "Design is not a PCBLayout"}

        # Run optimization
        opt_result = self.optimizer.optimize(
            context.design,
            [OptimizationGoal.MINIMIZE_TRACE_LENGTH, OptimizationGoal.MAXIMIZE_SPACING],
        )

        result = {
            "success": opt_result.success,
            "iterations": opt_result.iterations,
            "improvement_percent": opt_result.improvement_percent,
            "message": opt_result.message,
        }

        context.stage_results["optimization"] = result
        self._emit_event(
            "stage_completed",
            {
                "pipeline_id": context.pipeline_id,
                "stage": "optimization",
            },
        )

        return result

    def run_listing(
        self,
        context: PipelineContext,
        seller_id: str,
        min_price: float,
        title: str | None = None,
    ) -> dict[str, Any]:
        """Run the listing stage - list design on marketplace."""
        context.current_stage = PipelineStage.LISTING

        if not context.design:
            return {"success": False, "error": "No design to list"}

        listing_title = title or (
            context.requirements.name if context.requirements else "PCB Design"
        )

        listing = self.listing_manager.create_listing(
            design=context.design,
            seller_id=seller_id,
            title=listing_title,
            min_price=min_price,
            description=context.requirements.description if context.requirements else "",
        )

        # Activate the listing
        listing.activate()

        context.listing_id = listing.listing_id

        result = {
            "success": True,
            "listing_id": listing.listing_id,
            "status": listing.status.value,
        }

        context.stage_results["listing"] = result
        self._emit_event(
            "stage_completed",
            {
                "pipeline_id": context.pipeline_id,
                "stage": "listing",
            },
        )

        return result

    def run_full_design_pipeline(self, requirements: DesignRequirements) -> PipelineContext:
        """Run the full design pipeline from ideation through optimization."""
        context = self.create_pipeline(requirements)

        # Run each stage sequentially
        self.run_ideation(context)
        self.run_design(context)
        self.run_validation(context)
        self.run_optimization(context)

        return context

    def get_pipeline(self, pipeline_id: str) -> PipelineContext | None:
        """Get a pipeline by ID."""
        return self._pipelines.get(pipeline_id)

    def list_pipelines(self) -> list[PipelineContext]:
        """List all pipelines."""
        return list(self._pipelines.values())

    def get_pipeline_status(self, pipeline_id: str) -> dict[str, Any]:
        """Get detailed status of a pipeline."""
        context = self._pipelines.get(pipeline_id)
        if not context:
            return {"error": "Pipeline not found"}

        stages_completed = list(context.stage_results.keys())
        all_stages = [s.value for s in PipelineStage]
        progress = len(stages_completed) / len(all_stages) * 100

        return {
            "pipeline_id": pipeline_id,
            "current_stage": context.current_stage.value,
            "stages_completed": stages_completed,
            "progress_percent": progress,
            "has_design": context.design is not None,
            "has_listing": context.listing_id is not None,
            "has_sale": context.sale_id is not None,
        }

    def _emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit an event through the event bus."""
        event = Event(event_type=event_type, data=data, source="design_pipeline")
        self.event_bus.publish(event)
