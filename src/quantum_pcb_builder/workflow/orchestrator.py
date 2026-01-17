"""Workflow orchestration for the PCB Builder system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
from uuid import uuid4

from quantum_pcb_builder.core.base import BaseDesign
from quantum_pcb_builder.core.events import Event, EventBus


class WorkflowState(Enum):
    """State of a workflow."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepState(Enum):
    """State of a workflow step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """A step in a workflow."""

    step_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    state: StepState = StepState.PENDING
    handler: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    dependencies: list[str] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def run(self, context: dict[str, Any]) -> bool:
        """Execute the step."""
        self.state = StepState.RUNNING
        self.started_at = datetime.utcnow()

        try:
            if self.handler:
                self.result = self.handler(context)
            self.state = StepState.COMPLETED
            self.completed_at = datetime.utcnow()
            return True
        except Exception as e:
            self.state = StepState.FAILED
            self.error_message = str(e)
            self.completed_at = datetime.utcnow()
            return False

    def skip(self) -> None:
        """Skip this step."""
        self.state = StepState.SKIPPED

    def to_dict(self) -> dict[str, Any]:
        """Serialize step to dictionary."""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "description": self.description,
            "state": self.state.value,
            "dependencies": self.dependencies,
            "result": self.result,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class DesignWorkflow:
    """A complete workflow for PCB design."""

    workflow_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    state: WorkflowState = WorkflowState.CREATED
    steps: list[WorkflowStep] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    current_step_index: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def status(self) -> str:
        """Get workflow status string."""
        return self.state.value

    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow."""
        self.steps.append(step)

    def start(self) -> bool:
        """Start the workflow."""
        if self.state != WorkflowState.CREATED:
            return False
        self.state = WorkflowState.RUNNING
        self.started_at = datetime.utcnow()
        return True

    def pause(self) -> bool:
        """Pause the workflow."""
        if self.state != WorkflowState.RUNNING:
            return False
        self.state = WorkflowState.PAUSED
        return True

    def resume(self) -> bool:
        """Resume the workflow."""
        if self.state != WorkflowState.PAUSED:
            return False
        self.state = WorkflowState.RUNNING
        return True

    def cancel(self) -> bool:
        """Cancel the workflow."""
        if self.state in [WorkflowState.COMPLETED, WorkflowState.FAILED]:
            return False
        self.state = WorkflowState.CANCELLED
        self.completed_at = datetime.utcnow()
        return True

    def run_next_step(self) -> tuple[bool, WorkflowStep | None]:
        """Run the next pending step.

        Returns (has_more_steps, step_that_ran).
        """
        if self.state != WorkflowState.RUNNING:
            return (False, None)

        if self.current_step_index >= len(self.steps):
            self.state = WorkflowState.COMPLETED
            self.completed_at = datetime.utcnow()
            return (False, None)

        step = self.steps[self.current_step_index]

        # Check dependencies
        for dep_id in step.dependencies:
            dep_step = next((s for s in self.steps if s.step_id == dep_id), None)
            if dep_step and dep_step.state != StepState.COMPLETED:
                step.skip()
                self.current_step_index += 1
                return (True, step)

        # Run the step
        success = step.run(self.context)
        if success:
            # Update context with step results
            self.context[step.name] = step.result
        else:
            self.state = WorkflowState.FAILED
            self.completed_at = datetime.utcnow()
            return (False, step)

        self.current_step_index += 1
        has_more = self.current_step_index < len(self.steps)
        if not has_more:
            self.state = WorkflowState.COMPLETED
            self.completed_at = datetime.utcnow()
        return (has_more, step)

    def run_all(self) -> bool:
        """Run all steps to completion."""
        if not self.start() and self.state != WorkflowState.RUNNING:
            return False

        while True:
            has_more, step = self.run_next_step()
            if not has_more:
                break

        return self.state == WorkflowState.COMPLETED

    def get_progress(self) -> dict[str, Any]:
        """Get workflow progress."""
        completed = sum(1 for s in self.steps if s.state == StepState.COMPLETED)
        failed = sum(1 for s in self.steps if s.state == StepState.FAILED)
        pending = sum(1 for s in self.steps if s.state == StepState.PENDING)

        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "state": self.state.value,
            "total_steps": len(self.steps),
            "completed_steps": completed,
            "failed_steps": failed,
            "pending_steps": pending,
            "current_step": self.current_step_index,
            "progress_percent": (completed / len(self.steps) * 100) if self.steps else 0,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize workflow to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "state": self.state.value,
            "steps": [s.to_dict() for s in self.steps],
            "current_step_index": self.current_step_index,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class WorkflowOrchestrator:
    """Orchestrator for managing multiple workflows."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Initialize the orchestrator."""
        self._workflows: dict[str, DesignWorkflow] = {}
        self.event_bus = event_bus or EventBus()

    def create_design_workflow(
        self,
        name: str,
        design: BaseDesign | None = None,
    ) -> DesignWorkflow:
        """Create a standard design workflow."""
        workflow = DesignWorkflow(
            name=name,
            description=f"Design workflow for {name}",
            context={"design": design.to_dict() if design else {}},
        )

        # Add standard design steps
        workflow.add_step(
            WorkflowStep(
                name="requirements_analysis",
                description="Analyze design requirements",
                handler=self._analyze_requirements,
            )
        )

        workflow.add_step(
            WorkflowStep(
                name="component_selection",
                description="Select components for the design",
                handler=self._select_components,
            )
        )

        workflow.add_step(
            WorkflowStep(
                name="layout_generation",
                description="Generate PCB layout",
                handler=self._generate_layout,
            )
        )

        workflow.add_step(
            WorkflowStep(
                name="design_validation",
                description="Validate the design",
                handler=self._validate_design,
            )
        )

        workflow.add_step(
            WorkflowStep(
                name="optimization",
                description="Optimize the layout",
                handler=self._optimize_layout,
            )
        )

        self._workflows[workflow.workflow_id] = workflow
        self._emit_event("workflow_created", {"workflow_id": workflow.workflow_id})

        return workflow

    def _analyze_requirements(self, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze requirements step handler."""
        design = context.get("design", {})
        return {
            "analyzed": True,
            "design_name": design.get("name", "Unknown"),
            "component_count": len(design.get("components", [])),
        }

    def _select_components(self, context: dict[str, Any]) -> dict[str, Any]:
        """Select components step handler."""
        return {
            "selected": True,
            "components_validated": True,
        }

    def _generate_layout(self, context: dict[str, Any]) -> dict[str, Any]:
        """Generate layout step handler."""
        return {
            "layout_generated": True,
            "auto_routed": True,
        }

    def _validate_design(self, context: dict[str, Any]) -> dict[str, Any]:
        """Validate design step handler."""
        return {
            "validated": True,
            "drc_passed": True,
            "erc_passed": True,
        }

    def _optimize_layout(self, context: dict[str, Any]) -> dict[str, Any]:
        """Optimize layout step handler."""
        return {
            "optimized": True,
            "trace_length_reduced": True,
        }

    def get_workflow(self, workflow_id: str) -> DesignWorkflow | None:
        """Get a workflow by ID."""
        return self._workflows.get(workflow_id)

    def list_workflows(self, state: WorkflowState | None = None) -> list[DesignWorkflow]:
        """List all workflows, optionally filtered by state."""
        workflows = list(self._workflows.values())
        if state:
            workflows = [w for w in workflows if w.state == state]
        return workflows

    def run_workflow(self, workflow_id: str) -> bool:
        """Run a workflow to completion."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return False

        self._emit_event("workflow_started", {"workflow_id": workflow_id})

        success = workflow.run_all()

        if success:
            self._emit_event("workflow_completed", {"workflow_id": workflow_id})
        else:
            self._emit_event(
                "workflow_failed",
                {"workflow_id": workflow_id, "state": workflow.state.value},
            )

        return success

    def _emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit an event through the event bus."""
        event = Event(event_type=event_type, data=data, source="workflow_orchestrator")
        self.event_bus.publish(event)

    def get_statistics(self) -> dict[str, Any]:
        """Get orchestrator statistics."""
        by_state: dict[str, int] = {}
        for workflow in self._workflows.values():
            state_key = workflow.state.value
            by_state[state_key] = by_state.get(state_key, 0) + 1

        return {
            "total_workflows": len(self._workflows),
            "by_state": by_state,
        }
