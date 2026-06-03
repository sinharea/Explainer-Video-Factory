"""Data models for video scenes."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class SceneType(str, Enum):
    """Type of visual scene."""
    TITLE = "title"
    EXPLANATION = "explanation"
    DIAGRAM = "diagram"
    KEY_POINT = "key_point"
    ANALOGY = "analogy"
    SUMMARY = "summary"
    CREDITS = "credits"


class VisualElement(BaseModel):
    """A visual element within a scene (e.g., diagram, icon, label)."""
    element_type: str = Field(..., description="Type: text_block, circle, arrow, box, icon")
    content: str = Field(default="", description="Text content or label")
    position: tuple[float, float] = Field(
        default=(0.5, 0.5),
        description="Relative position (0-1) on the canvas",
    )
    size: tuple[float, float] = Field(
        default=(0.3, 0.1),
        description="Relative size (0-1) on the canvas",
    )
    color: str = Field(default="", description="Color override (hex or name)")
    metadata: dict = Field(default_factory=dict, description="Additional rendering hints")


class Scene(BaseModel):
    """A single scene in the video timeline."""
    scene_id: str = Field(..., description="Unique scene identifier")
    scene_type: SceneType = Field(..., description="Type of this scene")
    title: str = Field(default="", description="Scene title or heading")
    narration: str = Field(..., description="Narration text for this scene")
    visual_elements: list[VisualElement] = Field(
        default_factory=list,
        description="Visual elements to render",
    )
    duration: float = Field(
        default=0.0,
        description="Scene duration in seconds (0 = auto from narration)",
    )
    start_time: float = Field(
        default=0.0,
        description="Start time in seconds on the global timeline",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Key terms highlighted in this scene",
    )
    transition_in: str = Field(default="fade", description="Transition effect entering this scene")
    transition_out: str = Field(default="fade", description="Transition effect leaving this scene")

    # Rendered asset paths (populated during rendering)
    audio_path: Path | None = Field(default=None, description="Path to rendered audio file")
    visual_path: Path | None = Field(default=None, description="Path to rendered visual image")

    @property
    def end_time(self) -> float:
        """Calculate end time from start + duration."""
        return self.start_time + self.duration
