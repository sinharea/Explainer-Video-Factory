"""Avatar Agent — handles narration, script generation, and text-to-speech.

Responsible for generating the educational script (if needed) and
rendering the audio narration with accurate timing for lip-sync/subtitles.
"""

from __future__ import annotations

from pathlib import Path

from explainer_factory.exceptions import AgentError
from explainer_factory.logging import get_logger
from explainer_factory.models.render_job import RenderJob
from explainer_factory.pipeline.script_generator import ScriptGenerator
from explainer_factory.renderers.tts_renderer import TTSRenderer

logger = get_logger(__name__)


class AvatarAgent:
    """Agent responsible for all audio/narration generation tasks."""

    def __init__(self, use_llm: bool = False):
        """Initialize the Avatar Agent.

        Args:
            use_llm: Whether to use LLM for script generation.
        """
        self.script_generator = ScriptGenerator(use_llm=use_llm)
        self.tts_renderer = TTSRenderer()
        logger.info("avatar_agent.init")

    def generate_script(self, job: RenderJob) -> RenderJob:
        """Generate the educational script for the job.

        Args:
            job: The render job containing the topic.

        Returns:
            Updated render job with the generated script.
            
        Raises:
            AgentError: If script generation fails.
        """
        logger.info("avatar_agent.generate_script.start", job_id=job.job_id, topic=job.topic)
        
        try:
            script = self.script_generator.generate(topic=job.topic)
            job.script = script
            logger.info("avatar_agent.generate_script.complete", job_id=job.job_id)
            return job
        except Exception as e:
            logger.error("avatar_agent.generate_script.error", error=str(e))
            raise AgentError("AvatarAgent", f"Failed to generate script: {e}") from e

    def render_audio(self, job: RenderJob) -> RenderJob:
        """Render TTS audio for all planned scenes.

        Args:
            job: The render job with planned scenes.

        Returns:
            Updated render job with audio paths populated on scenes.
            
        Raises:
            AgentError: If audio rendering fails.
        """
        logger.info("avatar_agent.render_audio.start", job_id=job.job_id)

        if not job.scenes:
            raise AgentError("AvatarAgent", "No scenes planned for audio rendering")
        
        if not job.output_dir:
            raise AgentError("AvatarAgent", "Job output directory not set")

        audio_dir = job.output_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        try:
            results = self.tts_renderer.render_all_scenes(job.scenes, audio_dir)
            
            # Update actual durations on scenes based on rendered audio
            for scene in job.scenes:
                if scene.scene_id in results:
                    scene.duration = results[scene.scene_id]["duration"]
            
            logger.info("avatar_agent.render_audio.complete", job_id=job.job_id)
            return job
            
        except Exception as e:
            logger.error("avatar_agent.render_audio.error", error=str(e))
            raise AgentError("AvatarAgent", f"Failed to render audio: {e}") from e
