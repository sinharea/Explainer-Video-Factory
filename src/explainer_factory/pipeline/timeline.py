"""Timeline management for synchronizing audio and visual elements.

Handles temporal alignment between narration audio, visual scenes,
and subtitle overlays to ensure a coherent viewing experience.
"""

from __future__ import annotations

from dataclasses import dataclass

from explainer_factory.exceptions import TimelineError
from explainer_factory.logging import get_logger
from explainer_factory.models.scene import Scene

logger = get_logger(__name__)


@dataclass
class TimelineEntry:
    """A single entry in the rendering timeline."""
    scene_id: str
    start_time: float
    end_time: float
    narration: str
    has_audio: bool = False
    has_visual: bool = False

    @property
    def duration(self) -> float:
        """Duration in seconds."""
        return self.end_time - self.start_time


class Timeline:
    """Manages temporal alignment of all scene assets.

    Ensures audio, visuals, and subtitles are properly synchronized
    across the complete video timeline.
    """

    def __init__(self) -> None:
        self.entries: list[TimelineEntry] = []
        self._total_duration: float = 0.0

    @property
    def total_duration(self) -> float:
        """Total timeline duration in seconds."""
        return self._total_duration

    @property
    def scene_count(self) -> int:
        """Number of scenes in the timeline."""
        return len(self.entries)

    def build_from_scenes(self, scenes: list[Scene]) -> None:
        """Build timeline from a list of scenes.

        Args:
            scenes: Ordered list of scenes with timing information.

        Raises:
            TimelineError: If timeline construction fails.
        """
        if not scenes:
            raise TimelineError("Cannot build timeline from empty scene list")

        self.entries.clear()
        current_time = 0.0

        for scene in scenes:
            entry = TimelineEntry(
                scene_id=scene.scene_id,
                start_time=current_time,
                end_time=current_time + scene.duration,
                narration=scene.narration,
            )
            self.entries.append(entry)
            current_time += scene.duration

        self._total_duration = current_time
        logger.info(
            "timeline.built",
            num_entries=len(self.entries),
            total_duration=f"{self._total_duration:.1f}s",
        )

    def update_with_actual_durations(self, actual_durations: dict[str, float]) -> None:
        """Re-align timeline using actual audio durations after TTS.

        After TTS rendering, actual audio durations may differ from
        estimates. This method re-aligns the entire timeline.

        Args:
            actual_durations: Mapping of scene_id -> actual audio duration in seconds.
        """
        current_time = 0.0
        updated_count = 0

        for entry in self.entries:
            entry.start_time = current_time
            if entry.scene_id in actual_durations:
                actual = actual_durations[entry.scene_id]
                entry.end_time = current_time + actual
                current_time += actual
                entry.has_audio = True
                updated_count += 1
            else:
                entry.end_time = current_time + entry.duration
                current_time += entry.duration

        self._total_duration = current_time
        logger.info(
            "timeline.realigned",
            updated_scenes=updated_count,
            new_duration=f"{self._total_duration:.1f}s",
        )

    def mark_visual_ready(self, scene_id: str) -> None:
        """Mark a scene's visual as rendered and ready."""
        for entry in self.entries:
            if entry.scene_id == scene_id:
                entry.has_visual = True
                return
        logger.warning("timeline.unknown_scene", scene_id=scene_id)

    def is_complete(self) -> bool:
        """Check if all timeline entries have both audio and visual assets."""
        return all(e.has_audio and e.has_visual for e in self.entries)

    def get_subtitle_entries(self) -> list[dict]:
        """Generate subtitle entries from timeline.

        Returns:
            List of subtitle entries with index, start/end times, and text.
        """
        subtitles = []
        for i, entry in enumerate(self.entries):
            subtitles.append({
                "index": i + 1,
                "start_time": entry.start_time,
                "end_time": entry.end_time,
                "text": entry.narration,
            })
        return subtitles

    def __repr__(self) -> str:
        return f"Timeline(scenes={self.scene_count}, duration={self.total_duration:.1f}s)"
