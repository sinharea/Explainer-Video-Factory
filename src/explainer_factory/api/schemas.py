"""API request and response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from explainer_factory.models.render_job import RenderStatus
from explainer_factory.models.script import DifficultyLevel


class RenderRequest(BaseModel):
    """Request to render a new video."""
    topic: str = Field(..., description="Educational topic to explain")
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.INTERMEDIATE,
        description="Target difficulty level"
    )
    target_duration: float = Field(
        default=120.0,
        description="Target video duration in seconds",
        ge=30.0,
        le=600.0
    )
    use_llm: bool = Field(
        default=False,
        description="Use LLM for script generation (requires API key configuration)"
    )


class RenderResponse(BaseModel):
    """Response containing a submitted render job."""
    job_id: str
    status: RenderStatus
    topic: str
    message: str


class JobStatusResponse(BaseModel):
    """Response containing the status of a render job."""
    job_id: str
    status: RenderStatus
    topic: str
    progress_details: dict[str, Any]
    output_video_url: str | None = None
    output_subtitle_url: str | None = None
    error_message: str | None = None


class HealthResponse(BaseModel):
    """API health status response."""
    status: str
    version: str
    environment: str
