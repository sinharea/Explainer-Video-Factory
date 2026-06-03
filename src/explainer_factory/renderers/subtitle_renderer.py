"""Subtitle generation engine.

Generates SRT format subtitles from scene narration and timeline timing.
"""

from __future__ import annotations

import math
from pathlib import Path

from explainer_factory.exceptions import VideoCompositionError
from explainer_factory.logging import get_logger
from explainer_factory.pipeline.timeline import Timeline

logger = get_logger(__name__)


def _format_srt_time(seconds: float) -> str:
    """Format seconds into SRT time format (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(math.modf(seconds)[0] * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class SubtitleRenderer:
    """Renders subtitle files from the video timeline."""

    def __init__(self):
        """Initialize the subtitle renderer."""
        logger.info("subtitle_renderer.init")

    def generate_srt(self, timeline: Timeline, output_path: Path) -> Path:
        """Generate an SRT file from the timeline.

        Args:
            timeline: The synchronized timeline containing narration text.
            output_path: Path to write the .srt file.

        Returns:
            Path to the generated SRT file.
            
        Raises:
            VideoCompositionError: If subtitle generation fails.
        """
        logger.info("subtitle_renderer.generate.start", output_path=str(output_path))
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            entries = timeline.get_subtitle_entries()
            
            with open(output_path, "w", encoding="utf-8") as f:
                for entry in entries:
                    start_str = _format_srt_time(entry["start_time"])
                    end_str = _format_srt_time(entry["end_time"])
                    
                    # Write SRT block
                    f.write(f"{entry['index']}\n")
                    f.write(f"{start_str} --> {end_str}\n")
                    f.write(f"{entry['text']}\n\n")
                    
            logger.info("subtitle_renderer.generate.complete", num_entries=len(entries))
            return output_path
            
        except Exception as e:
            logger.error("subtitle_renderer.generate.error", error=str(e))
            raise VideoCompositionError(f"Failed to generate subtitles: {e}") from e
