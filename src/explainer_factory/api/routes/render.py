"""Render job management endpoints."""

import asyncio
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from explainer_factory.api.schemas import JobStatusResponse, RenderRequest, RenderResponse
from explainer_factory.config import get_settings
from explainer_factory.logging import get_logger
from explainer_factory.models.render_job import RenderJob, RenderStatus
from explainer_factory.orchestrator.graph import PipelineOrchestrator

logger = get_logger(__name__)
router = APIRouter(prefix="/render", tags=["Render"])

# In-memory job store for the prototype
# In a real app, this would be a database (PostgreSQL, Redis, etc.)
_JOBS: dict[str, RenderJob] = {}

# Global orchestrator instance
_orchestrator = PipelineOrchestrator()


def _process_job_background(job: RenderJob) -> None:
    """Run the rendering pipeline in a background task."""
    try:
        settings = get_settings()
        
        # Setup job output directory
        job_dir = settings.output_dir / job.job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        job.output_dir = job_dir
        
        # Execute pipeline
        completed_job = _orchestrator.run(job)
        _JOBS[job.job_id] = completed_job
        
    except Exception as e:
        logger.error("api.background_task.failed", job_id=job.job_id, error=str(e))
        job.mark_failed(message=f"Unhandled pipeline error: {e}")
        _JOBS[job.job_id] = job


@router.post("", response_model=RenderResponse)
async def submit_render_job(
    request: RenderRequest,
    background_tasks: BackgroundTasks,
) -> RenderResponse:
    """Submit a new video rendering job."""
    logger.info("api.submit_job", topic=request.topic)
    
    # Initialize job
    job = RenderJob(topic=request.topic)
    _JOBS[job.job_id] = job
    
    # Submit to background processing
    background_tasks.add_task(_process_job_background, job)
    
    return RenderResponse(
        job_id=job.job_id,
        status=job.status,
        topic=job.topic,
        message="Render job submitted successfully",
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Get the status of a specific render job."""
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Build progress details
    details: dict[str, Any] = {
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
        "duration_seconds": job.duration_seconds,
    }
    
    if job.script:
        details["script_segments"] = len(job.script.segments)
    if job.scenes:
        details["scenes_planned"] = len(job.scenes)
        
    # Build URLs for outputs (in a real app, these would be S3/CDN URLs)
    video_url = None
    subtitle_url = None
    
    if job.status == RenderStatus.COMPLETED:
        if job.output_video:
            # Assuming outputs directory is mounted statically at /outputs
            video_url = f"/outputs/{job.job_id}/{job.output_video.name}"
        if job.output_subtitle:
            subtitle_url = f"/outputs/{job.job_id}/{job.output_subtitle.name}"
            
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        topic=job.topic,
        progress_details=details,
        output_video_url=video_url,
        output_subtitle_url=subtitle_url,
        error_message=job.error_message,
    )
