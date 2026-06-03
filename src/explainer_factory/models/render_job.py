"""Data models for render jobs and pipeline state."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from .scene import Scene
from .script import Script


class RenderStatus(str, Enum):
    """Status of a render job."""
    PENDING = "pending"
    GENERATING_SCRIPT = "generating_script"
    PLANNING_SCENES = "planning_scenes"
    RENDERING_AUDIO = "rendering_audio"
    RENDERING_VISUALS = "rendering_visuals"
    COMPOSING_VIDEO = "composing_video"
    COMPLETED = "completed"
    FAILED = "failed"


class RenderJob(BaseModel):
    """A complete render job tracking the pipeline from input to output."""
    job_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique job identifier",
    )
    topic: str = Field(..., description="The educational topic to render")
    status: RenderStatus = Field(
        default=RenderStatus.PENDING,
        description="Current pipeline status",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Job creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )

    # Pipeline artifacts
    script: Script | None = Field(default=None, description="Generated script")
    scenes: list[Scene] = Field(default_factory=list, description="Planned scenes")

    # Output paths
    output_dir: Path | None = Field(default=None, description="Output directory for this job")
    output_video: Path | None = Field(default=None, description="Final rendered video path")
    output_subtitle: Path | None = Field(default=None, description="Generated subtitle file path")

    # Error tracking
    error_message: str | None = Field(default=None, description="Error message if failed")
    error_details: dict | None = Field(default=None, description="Detailed error info")

    # Timing metrics
    pipeline_start_time: float | None = Field(default=None, description="Pipeline start (epoch)")
    pipeline_end_time: float | None = Field(default=None, description="Pipeline end (epoch)")

    @property
    def duration_seconds(self) -> float | None:
        """Total pipeline execution time in seconds."""
        if self.pipeline_start_time and self.pipeline_end_time:
            return self.pipeline_end_time - self.pipeline_start_time
        return None

    def update_status(self, status: RenderStatus) -> None:
        """Update job status and timestamp."""
        self.status = status
        self.updated_at = datetime.now(timezone.utc)

    def mark_failed(self, message: str, details: dict | None = None) -> None:
        """Mark job as failed with error details."""
        self.status = RenderStatus.FAILED
        self.error_message = message
        self.error_details = details
        self.updated_at = datetime.now(timezone.utc)
