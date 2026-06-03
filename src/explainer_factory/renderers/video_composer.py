"""Video composition engine using MoviePy.

Assembles rendered audio clips, visual scenes, and subtitle overlays
into a final synchronized MP4 video.
"""

from __future__ import annotations

import os
from pathlib import Path

from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
)

from explainer_factory.config import VideoSettings
from explainer_factory.exceptions import VideoCompositionError
from explainer_factory.logging import get_logger
from explainer_factory.models.scene import Scene
from explainer_factory.pipeline.timeline import Timeline

logger = get_logger(__name__)


class VideoComposer:
    """Assembles audio and visual assets into a final video."""

    def __init__(self, settings: VideoSettings | None = None):
        """Initialize the video composer.

        Args:
            settings: Video configuration. Uses defaults if not provided.
        """
        self.settings = settings or VideoSettings()
        logger.info(
            "video_composer.init",
            resolution=f"{self.settings.width}x{self.settings.height}",
            fps=self.settings.fps,
        )

    def compose_timeline(
        self,
        timeline: Timeline,
        scenes: list[Scene],
        output_path: Path,
    ) -> Path:
        """Compose all scenes into a final video.

        Args:
            timeline: The synchronized timeline.
            scenes: List of Scene objects with rendered asset paths.
            output_path: Path to write the final video.

        Returns:
            Path to the rendered final video.

        Raises:
            VideoCompositionError: If composition fails.
        """
        logger.info("video_composer.compose.start", output_path=str(output_path))
        
        if not timeline.is_complete():
            logger.warning("video_composer.timeline_incomplete")

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create a lookup for scenes
            scene_lookup = {scene.scene_id: scene for scene in scenes}
            
            clips = []
            
            # Process each timeline entry
            for i, entry in enumerate(timeline.entries):
                scene = scene_lookup.get(entry.scene_id)
                if not scene:
                    raise VideoCompositionError(f"Scene {entry.scene_id} missing from scenes list")
                    
                if not scene.visual_path or not scene.visual_path.exists():
                    raise VideoCompositionError(f"Visual asset missing for scene {entry.scene_id}")
                    
                if not scene.audio_path or not scene.audio_path.exists():
                    raise VideoCompositionError(f"Audio asset missing for scene {entry.scene_id}")
                
                logger.debug(
                    "video_composer.process_scene", 
                    scene_id=scene.scene_id, 
                    duration=f"{entry.duration:.2f}s"
                )
                
                # Load image and set duration
                img_clip = ImageClip(str(scene.visual_path))
                img_clip = img_clip.set_duration(entry.duration)
                
                # Load audio and attach to image
                audio_clip = AudioFileClip(str(scene.audio_path))
                
                # Ensure audio duration matches clip duration exactly (handle rounding)
                if abs(audio_clip.duration - entry.duration) > 0.1:
                    logger.warning(
                        "video_composer.duration_mismatch",
                        scene=scene.scene_id,
                        audio=audio_clip.duration,
                        timeline=entry.duration
                    )
                
                img_clip = img_clip.set_audio(audio_clip)
                
                # Apply crossfade transition if specified
                # Moviepy concatenate_videoclips handles transitions if we use specific methods,
                # but standard concatenate is safest for exact timing
                clips.append(img_clip)
                
            if not clips:
                raise VideoCompositionError("No clips generated for composition")
                
            # Concatenate all clips sequentially
            logger.info("video_composer.concatenate", num_clips=len(clips))
            final_clip = concatenate_videoclips(clips, method="compose")
            
            # Write final video file
            logger.info("video_composer.encode.start")
            
            # Hide moviepy's internal prints
            import builtins
            original_print = builtins.print
            try:
                builtins.print = lambda *args, **kwargs: None
                final_clip.write_videofile(
                    str(output_path),
                    fps=self.settings.fps,
                    codec=self.settings.codec,
                    audio_codec=self.settings.audio_codec,
                    bitrate=self.settings.bitrate,
                    audio_bitrate=self.settings.audio_bitrate,
                    preset="fast",
                    threads=4,
                    logger=None  # Disable progress bar
                )
            finally:
                builtins.print = original_print
                
            # Cleanup clips to free memory
            for clip in clips:
                clip.close()
            final_clip.close()
            
            logger.info("video_composer.compose.complete", output_path=str(output_path))
            return output_path
            
        except Exception as e:
            logger.error("video_composer.compose.error", error=str(e))
            raise VideoCompositionError(
                f"Video composition failed: {str(e)}",
                details={"output": str(output_path)}
            ) from e
