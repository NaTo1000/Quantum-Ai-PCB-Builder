"""Tests for workflow module."""

from quantum_pcb_builder.ai.designer import (
    ApplicationDomain,
    CommunicationType,
    DesignRequirements,
)
from quantum_pcb_builder.core.base import BaseComponent, BaseDesign
from quantum_pcb_builder.workflow.orchestrator import (
    DesignWorkflow,
    StepState,
    WorkflowOrchestrator,
    WorkflowState,
    WorkflowStep,
)
from quantum_pcb_builder.workflow.pipeline import (
    DesignPipeline,
)


class TestWorkflowStep:
    """Tests for WorkflowStep class."""

    def test_create_step(self) -> None:
        """Test creating a workflow step."""
        step = WorkflowStep(
            name="test_step",
            description="A test step",
        )
        assert step.name == "test_step"
        assert step.state == StepState.PENDING

    def test_run_step(self) -> None:
        """Test running a step."""

        def handler(context: dict) -> dict:
            return {"result": "success"}

        step = WorkflowStep(
            name="test_step",
            handler=handler,
        )
        success = step.run({})
        assert success
        assert step.state == StepState.COMPLETED
        assert step.result["result"] == "success"

    def test_step_failure(self) -> None:
        """Test step failure handling."""

        def failing_handler(context: dict) -> dict:
            raise ValueError("Test error")

        step = WorkflowStep(
            name="failing_step",
            handler=failing_handler,
        )
        success = step.run({})
        assert not success
        assert step.state == StepState.FAILED
        assert "Test error" in step.error_message

    def test_skip_step(self) -> None:
        """Test skipping a step."""
        step = WorkflowStep(name="skipped_step")
        step.skip()
        assert step.state == StepState.SKIPPED


class TestDesignWorkflow:
    """Tests for DesignWorkflow class."""

    def test_create_workflow(self) -> None:
        """Test creating a workflow."""
        workflow = DesignWorkflow(
            name="Test Workflow",
            description="A test workflow",
        )
        assert workflow.name == "Test Workflow"
        assert workflow.state == WorkflowState.CREATED

    def test_add_steps(self) -> None:
        """Test adding steps to workflow."""
        workflow = DesignWorkflow(name="Test")
        workflow.add_step(WorkflowStep(name="step1"))
        workflow.add_step(WorkflowStep(name="step2"))
        assert len(workflow.steps) == 2

    def test_start_workflow(self) -> None:
        """Test starting a workflow."""
        workflow = DesignWorkflow(name="Test")
        assert workflow.start()
        assert workflow.state == WorkflowState.RUNNING

    def test_pause_resume(self) -> None:
        """Test pausing and resuming."""
        workflow = DesignWorkflow(name="Test")
        workflow.start()

        assert workflow.pause()
        assert workflow.state == WorkflowState.PAUSED

        assert workflow.resume()
        assert workflow.state == WorkflowState.RUNNING

    def test_cancel_workflow(self) -> None:
        """Test canceling a workflow."""
        workflow = DesignWorkflow(name="Test")
        workflow.start()

        assert workflow.cancel()
        assert workflow.state == WorkflowState.CANCELLED

    def test_run_all_steps(self) -> None:
        """Test running all steps."""

        def step_handler(context: dict) -> dict:
            return {"done": True}

        workflow = DesignWorkflow(name="Test")
        workflow.add_step(WorkflowStep(name="step1", handler=step_handler))
        workflow.add_step(WorkflowStep(name="step2", handler=step_handler))

        success = workflow.run_all()
        assert success
        assert workflow.state == WorkflowState.COMPLETED
        assert all(s.state == StepState.COMPLETED for s in workflow.steps)

    def test_get_progress(self) -> None:
        """Test getting workflow progress."""
        workflow = DesignWorkflow(name="Test")
        workflow.add_step(WorkflowStep(name="step1"))
        workflow.add_step(WorkflowStep(name="step2"))

        progress = workflow.get_progress()
        assert progress["total_steps"] == 2
        assert progress["pending_steps"] == 2
        assert progress["progress_percent"] == 0


class TestWorkflowOrchestrator:
    """Tests for WorkflowOrchestrator."""

    def test_create_design_workflow(self) -> None:
        """Test creating a design workflow."""
        orchestrator = WorkflowOrchestrator()
        design = BaseDesign(name="Test Design")
        design.add_component(BaseComponent(name="MCU", component_type="microcontroller"))

        workflow = orchestrator.create_design_workflow("Test", design)

        assert workflow.name == "Test"
        assert len(workflow.steps) > 0

    def test_run_workflow(self) -> None:
        """Test running a workflow through orchestrator."""
        orchestrator = WorkflowOrchestrator()
        design = BaseDesign(name="Test")

        workflow = orchestrator.create_design_workflow("Test", design)
        success = orchestrator.run_workflow(workflow.workflow_id)

        assert success
        assert workflow.state == WorkflowState.COMPLETED

    def test_list_workflows(self) -> None:
        """Test listing workflows."""
        orchestrator = WorkflowOrchestrator()

        orchestrator.create_design_workflow("Workflow 1", None)
        orchestrator.create_design_workflow("Workflow 2", None)

        workflows = orchestrator.list_workflows()
        assert len(workflows) == 2

    def test_get_statistics(self) -> None:
        """Test getting orchestrator statistics."""
        orchestrator = WorkflowOrchestrator()

        workflow = orchestrator.create_design_workflow("Test", None)
        orchestrator.run_workflow(workflow.workflow_id)

        stats = orchestrator.get_statistics()
        assert stats["total_workflows"] == 1
        assert "completed" in stats["by_state"]


class TestDesignPipeline:
    """Tests for DesignPipeline."""

    def test_create_pipeline(self) -> None:
        """Test creating a pipeline."""
        pipeline = DesignPipeline()
        req = DesignRequirements(
            name="IoT Device",
            description="Smart sensor device",
        )

        context = pipeline.create_pipeline(req)
        assert context.pipeline_id
        assert context.requirements == req

    def test_run_ideation(self) -> None:
        """Test running ideation stage."""
        pipeline = DesignPipeline()
        req = DesignRequirements(
            name="Weather Station",
            description="Remote weather monitoring with battery power",
        )
        context = pipeline.create_pipeline(req)

        result = pipeline.run_ideation(context)
        assert result["success"]
        assert "suggestions" in result

    def test_run_design(self) -> None:
        """Test running design stage."""
        pipeline = DesignPipeline()
        req = DesignRequirements(
            name="IoT Device",
            communication_types=[CommunicationType.WIFI],
        )
        context = pipeline.create_pipeline(req)

        result = pipeline.run_design(context)
        assert result["success"]
        assert context.design is not None

    def test_run_validation(self) -> None:
        """Test running validation stage."""
        pipeline = DesignPipeline()
        req = DesignRequirements(
            name="IoT Device",
            communication_types=[CommunicationType.WIFI],
        )
        context = pipeline.create_pipeline(req)

        pipeline.run_design(context)
        result = pipeline.run_validation(context)
        assert "is_valid" in result

    def test_run_optimization(self) -> None:
        """Test running optimization stage."""
        pipeline = DesignPipeline()
        req = DesignRequirements(
            name="IoT Device",
            communication_types=[CommunicationType.WIFI],
        )
        context = pipeline.create_pipeline(req)

        pipeline.run_design(context)
        result = pipeline.run_optimization(context)
        assert "success" in result

    def test_run_listing(self) -> None:
        """Test running listing stage."""
        pipeline = DesignPipeline()
        req = DesignRequirements(
            name="IoT Device",
            communication_types=[CommunicationType.WIFI],
        )
        context = pipeline.create_pipeline(req)

        pipeline.run_design(context)
        result = pipeline.run_listing(context, "seller1", 100.0)
        assert result["success"]
        assert context.listing_id is not None

    def test_run_full_pipeline(self) -> None:
        """Test running the full design pipeline."""
        pipeline = DesignPipeline()
        req = DesignRequirements(
            name="Complete IoT Device",
            description="Full-featured IoT sensor",
            domain=ApplicationDomain.IOT,
            communication_types=[CommunicationType.LORA, CommunicationType.WIFI],
            sensor_types=["temperature", "humidity"],
        )

        context = pipeline.run_full_design_pipeline(req)

        assert context.design is not None
        assert "ideation" in context.stage_results
        assert "design" in context.stage_results
        assert "validation" in context.stage_results
        assert "optimization" in context.stage_results

    def test_get_pipeline_status(self) -> None:
        """Test getting pipeline status."""
        pipeline = DesignPipeline()
        req = DesignRequirements(name="Test")
        context = pipeline.create_pipeline(req)

        pipeline.run_ideation(context)
        pipeline.run_design(context)

        status = pipeline.get_pipeline_status(context.pipeline_id)
        assert "design" in status["stages_completed"]
        assert status["has_design"]
