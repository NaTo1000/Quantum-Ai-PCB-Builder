"""RabbitMQ job processor for background design jobs.

This module handles asynchronous job processing for long-running
design synthesis, validation, and simulation tasks.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Callable
from uuid import uuid4


class JobStatus(Enum):
    """Status of a background job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(Enum):
    """Types of background jobs."""

    SYNTHESIS = "synthesis"
    VALIDATION = "validation"
    SIMULATION = "simulation"
    VENDOR_MATCH = "vendor_match"
    EXPORT = "export"


@dataclass
class Job:
    """A background job."""

    job_id: str
    job_type: JobType
    status: JobStatus
    payload: dict
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: float = 0.0

    def __post_init__(self):
        """Set creation timestamp if not provided."""
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


class JobQueue:
    """In-memory job queue for development.

    Note: Production should use RabbitMQ or similar.
    """

    def __init__(self):
        """Initialize the job queue."""
        self._jobs: dict[str, Job] = {}
        self._pending: list[str] = []

    def enqueue(self, job: Job) -> str:
        """Add a job to the queue.

        Args:
            job: The job to enqueue.

        Returns:
            The job ID.
        """
        self._jobs[job.job_id] = job
        self._pending.append(job.job_id)
        return job.job_id

    def dequeue(self) -> Optional[Job]:
        """Get the next pending job.

        Returns:
            The next job, or None if queue is empty.
        """
        if not self._pending:
            return None

        job_id = self._pending.pop(0)
        return self._jobs.get(job_id)

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID.

        Args:
            job_id: The job ID.

        Returns:
            The job, or None if not found.
        """
        return self._jobs.get(job_id)

    def update_job(self, job: Job):
        """Update a job in the queue.

        Args:
            job: The updated job.
        """
        self._jobs[job.job_id] = job


class JobWorker:
    """Background worker for processing jobs.

    This worker polls the job queue and executes jobs
    using registered handlers.
    """

    def __init__(self, queue: Optional[JobQueue] = None):
        """Initialize the worker.

        Args:
            queue: Job queue to use. Creates new one if None.
        """
        self.queue = queue or JobQueue()
        self._handlers: dict[JobType, Callable] = {}
        self._running = False

    def register_handler(self, job_type: JobType, handler: Callable):
        """Register a handler for a job type.

        Args:
            job_type: Type of job to handle.
            handler: Callable that processes the job payload.
        """
        self._handlers[job_type] = handler

    def submit_job(
        self, job_type: JobType, payload: dict
    ) -> str:
        """Submit a new job.

        Args:
            job_type: Type of job.
            payload: Job payload data.

        Returns:
            The job ID.
        """
        job = Job(
            job_id=str(uuid4()),
            job_type=job_type,
            status=JobStatus.PENDING,
            payload=payload,
        )
        return self.queue.enqueue(job)

    def get_job_status(self, job_id: str) -> Optional[dict]:
        """Get the status of a job.

        Args:
            job_id: The job ID.

        Returns:
            Dictionary with job status, or None if not found.
        """
        job = self.queue.get_job(job_id)
        if not job:
            return None

        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "progress": job.progress,
            "result": job.result,
            "error": job.error,
        }

    def process_one(self) -> bool:
        """Process a single job from the queue.

        Returns:
            True if a job was processed, False if queue was empty.
        """
        job = self.queue.dequeue()
        if not job:
            return False

        # Update status to running
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow().isoformat()
        self.queue.update_job(job)

        # Get handler
        handler = self._handlers.get(job.job_type)
        if not handler:
            job.status = JobStatus.FAILED
            job.error = f"No handler for job type: {job.job_type.value}"
            job.completed_at = datetime.utcnow().isoformat()
            self.queue.update_job(job)
            return True

        # Execute handler
        try:
            result = handler(job.payload)
            job.status = JobStatus.COMPLETED
            job.result = result
            job.progress = 100.0
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)

        job.completed_at = datetime.utcnow().isoformat()
        self.queue.update_job(job)
        return True

    def run(self, max_jobs: Optional[int] = None):
        """Run the worker loop.

        Args:
            max_jobs: Maximum jobs to process. None for unlimited.

        Note: This is a simple synchronous implementation.
        Production should use async or threading.
        """
        self._running = True
        jobs_processed = 0

        while self._running:
            if max_jobs and jobs_processed >= max_jobs:
                break

            if self.process_one():
                jobs_processed += 1

    def stop(self):
        """Stop the worker loop."""
        self._running = False
