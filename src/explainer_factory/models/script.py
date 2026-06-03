"""Data models for educational scripts."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class DifficultyLevel(str, Enum):
    """Difficulty level for the educational content."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ScriptSegment(BaseModel):
    """A single segment of narration within a scene."""
    text: str = Field(..., description="The narration text for this segment")
    duration_hint: float = Field(
        default=0.0,
        description="Estimated duration in seconds (0 = auto-calculate from text length)",
    )
    emphasis: bool = Field(
        default=False,
        description="Whether this segment should be spoken with emphasis",
    )
    pause_after: float = Field(
        default=0.3,
        description="Pause duration in seconds after this segment",
    )


class Script(BaseModel):
    """Complete educational script for a topic."""
    topic: str = Field(..., description="The educational topic")
    title: str = Field(..., description="Video title")
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.INTERMEDIATE,
        description="Target difficulty level",
    )
    summary: str = Field(default="", description="Brief summary of the content")
    segments: list[ScriptSegment] = Field(
        default_factory=list,
        description="Ordered list of narration segments",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Key terms for the topic",
    )
    target_duration: float = Field(
        default=120.0,
        description="Target total video duration in seconds",
    )

    @property
    def total_text(self) -> str:
        """Get concatenated text from all segments."""
        return " ".join(seg.text for seg in self.segments)

    @property
    def estimated_duration(self) -> float:
        """Estimate total duration based on segment text lengths."""
        # Average speaking rate: ~150 words per minute
        words = sum(len(seg.text.split()) for seg in self.segments)
        pauses = sum(seg.pause_after for seg in self.segments)
        return (words / 150.0) * 60.0 + pauses
