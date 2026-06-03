"""Synthesis Agent — merges audio, visuals, and subtitles into final video.

Takes the completed assets from Avatar and Visuals agents, aligns them
on a global timeline, and encodes the final educational video.
"""

from __future__ import annotations

from pathlib import Path

from explainer_factory.exceptions import AgentError
from explainer_factory.logging import get_logger
from explainer_factory.models.render_job import RenderJob
from explainer_factory.pipeline.timeline import Timeline
from explainer_factory.renderers.subtitle_renderer import SubtitleRenderer
from explainer_factory.renderers.video_composer import VideoComposer

logger = get_logger(__name__)


class SynthesisAgent:
    """Agent responsible for final video assembly and encoding."""

    def __init__(self):
        """Initialize the Synthesis Agent."""
        self.video_composer = VideoComposer()
        self.subtitle_renderer = SubtitleRenderer()
        logger.info("synthesis_agent.init")

    def synthesize(self, job: RenderJob) -> RenderJob:
        """Merge all assets into the final video.

        Args:
            job: The render job with completed scenes and assets.

        Returns:
            Updated render job with output video and subtitle paths.
            
        Raises:
            AgentError: If synthesis fails.
        """
        logger.info("synthesis_agent.synthesize.start", job_id=job.job_id)
        
        if not job.scenes:
            raise AgentError("SynthesisAgent", "No scenes available for synthesis")
            
        if not job.output_dir:
            raise AgentError("SynthesisAgent", "Job output directory not set")

        try:
            # 1. Build and align timeline based on actual audio durations
            timeline = Timeline()
            timeline.build_from_scenes(job.scenes)
            
            # Update timeline entries based on actual asset states
            actual_durations = {s.scene_id: s.duration for s in job.scenes if s.audio_path}
            timeline.update_with_actual_durations(actual_durations)
            
            for scene in job.scenes:
                if scene.visual_path:
                    timeline.mark_visual_ready(scene.scene_id)
            
            if not timeline.is_complete():
                logger.warning("synthesis_agent.incomplete_timeline")

            # 2. Generate subtitles
            subtitle_path = job.output_dir / "subtitles.srt"
            job.output_subtitle = self.subtitle_renderer.generate_srt(
                timeline=timeline,
                output_path=subtitle_path
            )

            # 3. Compose final video
            video_path = job.output_dir / "final_video.mp4"
            job.output_video = self.video_composer.compose_timeline(
                timeline=timeline,
                scenes=job.scenes,
                output_path=video_path
            )

            logger.info(
                "synthesis_agent.synthesize.complete", 
                job_id=job.job_id,
                video=str(job.output_video)
            )
            return job
            
        except Exception as e:
            logger.error("synthesis_agent.synthesize.error", error=str(e))
            raise AgentError("SynthesisAgent", f"Failed to synthesize video: {e}") from e
