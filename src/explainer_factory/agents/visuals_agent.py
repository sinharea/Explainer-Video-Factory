"""Visuals Agent — handles scene planning and visual generation.

Responsible for taking an educational script, breaking it into planned
scenes with visual elements, and rendering the final image for each scene.
"""

from __future__ import annotations

from pathlib import Path

from explainer_factory.exceptions import AgentError
from explainer_factory.logging import get_logger
from explainer_factory.models.render_job import RenderJob
from explainer_factory.pipeline.scene_planner import ScenePlanner
from explainer_factory.renderers.visual_renderer import VisualRenderer

logger = get_logger(__name__)


class VisualsAgent:
    """Agent responsible for all visual generation tasks."""

    def __init__(self):
        """Initialize the Visuals Agent."""
        self.scene_planner = ScenePlanner()
        self.visual_renderer = VisualRenderer()
        logger.info("visuals_agent.init")

    def plan_scenes(self, job: RenderJob) -> RenderJob:
        """Plan scenes from the job's script.

        Args:
            job: The render job containing a generated script.

        Returns:
            Updated render job with planned scenes.
            
        Raises:
            AgentError: If scene planning fails.
        """
        logger.info("visuals_agent.plan_scenes.start", job_id=job.job_id)
        
        if not job.script:
            raise AgentError("VisualsAgent", "Cannot plan scenes: no script generated yet")

        try:
            scenes = self.scene_planner.plan(job.script)
            job.scenes = scenes
            logger.info("visuals_agent.plan_scenes.complete", job_id=job.job_id, num_scenes=len(scenes))
            return job
        except Exception as e:
            logger.error("visuals_agent.plan_scenes.error", error=str(e))
            raise AgentError("VisualsAgent", f"Failed to plan scenes: {e}") from e

    def render_visuals(self, job: RenderJob) -> RenderJob:
        """Render visuals for all planned scenes.

        Args:
            job: The render job with planned scenes.

        Returns:
            Updated render job with visual paths populated on scenes.
            
        Raises:
            AgentError: If visual rendering fails.
        """
        logger.info("visuals_agent.render_visuals.start", job_id=job.job_id)

        if not job.scenes:
            raise AgentError("VisualsAgent", "No scenes planned for visual rendering")
            
        if not job.output_dir:
            raise AgentError("VisualsAgent", "Job output directory not set")

        visuals_dir = job.output_dir / "visuals"
        visuals_dir.mkdir(parents=True, exist_ok=True)

        try:
            # The visual renderer updates scene.visual_path in-place
            self.visual_renderer.render_all_scenes(job.scenes, visuals_dir)
            logger.info("visuals_agent.render_visuals.complete", job_id=job.job_id)
            return job
            
        except Exception as e:
            logger.error("visuals_agent.render_visuals.error", error=str(e))
            raise AgentError("VisualsAgent", f"Failed to render visuals: {e}") from e
