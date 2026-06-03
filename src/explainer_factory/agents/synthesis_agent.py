"""Synthesis Agent — merges audio, visuals, and subtitles into final video.

Takes the completed assets from Avatar and Visuals agents, aligns them
on a global timeline using ACTUAL audio file durations, and encodes
the final educational video with perfect synchronization.
"""

from __future__ import annotations

from pathlib import Path

from moviepy import AudioFileClip

from explainer_factory.exceptions import AgentError
from explainer_factory.logging import get_logger
from explainer_factory.models.render_job import RenderJob
from explainer_factory.pipeline.timeline import Timeline
from explainer_factory.renderers.subtitle_renderer import SubtitleRenderer
from explainer_factory.renderers.video_composer import VideoComposer

logger = get_logger(__name__)


def _probe_audio_duration(audio_path: Path) -> float:
    """Get the true playback duration from an audio file.

    This is the authoritative source of truth for timing.  We read
    the actual decoded audio stream rather than relying on metadata
    or word-boundary estimates from the TTS engine.

    Args:
        audio_path: Path to the audio file.

    Returns:
        Duration in seconds.
    """
    try:
        clip = AudioFileClip(str(audio_path))
        duration = clip.duration
        clip.close()
        return duration
    except Exception as e:
        logger.warning(
            "synthesis_agent.probe_fallback",
            path=str(audio_path),
            error=str(e),
        )
        # Fallback: estimate from file size (~16 kBps MP3)
        if audio_path.exists():
            return audio_path.stat().st_size / 16000.0
        return 0.0


class SynthesisAgent:
    """Agent responsible for final video assembly and encoding."""

    def __init__(self):
        """Initialize the Synthesis Agent."""
        self.video_composer = VideoComposer()
        self.subtitle_renderer = SubtitleRenderer()
        logger.info("synthesis_agent.init")

    def synthesize(self, job: RenderJob) -> RenderJob:
        """Merge all assets into the final video.

        The synthesis pipeline:
        1. Probe every audio file to get ground-truth durations.
        2. Rebuild the timeline using those durations (cumulative timestamps).
        3. Generate subtitles aligned to the rebuilt timeline.
        4. Compose the video — each visual displays for exactly its audio length.

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
            # ── 1. Probe actual audio durations from rendered files ──
            actual_durations: dict[str, float] = {}
            for scene in job.scenes:
                if scene.audio_path and scene.audio_path.exists():
                    probed = _probe_audio_duration(scene.audio_path)
                    actual_durations[scene.scene_id] = probed
                    # Also update the scene model so everything is consistent
                    scene.duration = probed
                    logger.debug(
                        "synthesis_agent.probed_duration",
                        scene_id=scene.scene_id,
                        duration=f"{probed:.2f}s",
                    )

            # ── 2. Build timeline from actual durations ──
            timeline = Timeline()
            timeline.build_from_scenes(job.scenes)
            timeline.update_with_actual_durations(actual_durations)

            for scene in job.scenes:
                if scene.visual_path:
                    timeline.mark_visual_ready(scene.scene_id)

            if not timeline.is_complete():
                logger.warning("synthesis_agent.incomplete_timeline")

            logger.info(
                "synthesis_agent.timeline_ready",
                total_duration=f"{timeline.total_duration:.2f}s",
                num_scenes=timeline.scene_count,
            )

            # ── 3. Generate subtitles aligned to real timeline ──
            subtitle_path = job.output_dir / "subtitles.srt"
            job.output_subtitle = self.subtitle_renderer.generate_srt(
                timeline=timeline,
                output_path=subtitle_path,
            )

            # ── 4. Compose final video ──
            video_path = job.output_dir / "final_video.mp4"
            job.output_video = self.video_composer.compose_timeline(
                timeline=timeline,
                scenes=job.scenes,
                output_path=video_path,
            )

            logger.info(
                "synthesis_agent.synthesize.complete",
                job_id=job.job_id,
                video=str(job.output_video),
            )
            return job

        except Exception as e:
            logger.error("synthesis_agent.synthesize.error", error=str(e))
            raise AgentError("SynthesisAgent", f"Failed to synthesize video: {e}") from e
