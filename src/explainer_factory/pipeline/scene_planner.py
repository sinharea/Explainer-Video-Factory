"""Scene planner — breaks scripts into timed, visualized scenes.

Takes a Script and produces a list of Scene objects, each with:
- Narration text for that scene
- Visual element descriptions
- Timing information aligned to the global timeline
"""

from __future__ import annotations

from explainer_factory.exceptions import ScenePlanningError
from explainer_factory.logging import get_logger
from explainer_factory.models.scene import Scene, SceneType, VisualElement
from explainer_factory.models.script import Script

logger = get_logger(__name__)

# Visual element templates per scene type
SCENE_VISUAL_TEMPLATES: dict[SceneType, list[dict]] = {
    SceneType.TITLE: [
        {
            "element_type": "text_block",
            "content": "{title}",
            "position": (0.5, 0.4),
            "size": (0.8, 0.15),
        },
        {
            "element_type": "text_block",
            "content": "{subtitle}",
            "position": (0.5, 0.6),
            "size": (0.6, 0.08),
        },
    ],
    SceneType.EXPLANATION: [
        {
            "element_type": "text_block",
            "content": "{heading}",
            "position": (0.5, 0.15),
            "size": (0.8, 0.08),
        },
        {
            "element_type": "text_block",
            "content": "{body}",
            "position": (0.5, 0.5),
            "size": (0.75, 0.5),
        },
    ],
    SceneType.DIAGRAM: [
        {
            "element_type": "text_block",
            "content": "{heading}",
            "position": (0.5, 0.1),
            "size": (0.8, 0.06),
        },
        {
            "element_type": "box",
            "content": "{left_label}",
            "position": (0.25, 0.45),
            "size": (0.2, 0.15),
            "color": "primary",
        },
        {
            "element_type": "arrow",
            "content": "",
            "position": (0.5, 0.45),
            "size": (0.15, 0.02),
        },
        {
            "element_type": "box",
            "content": "{right_label}",
            "position": (0.75, 0.45),
            "size": (0.2, 0.15),
            "color": "secondary",
        },
        {
            "element_type": "text_block",
            "content": "{caption}",
            "position": (0.5, 0.75),
            "size": (0.7, 0.08),
        },
    ],
    SceneType.KEY_POINT: [
        {
            "element_type": "icon",
            "content": "★",
            "position": (0.5, 0.2),
            "size": (0.1, 0.1),
            "color": "accent",
        },
        {
            "element_type": "text_block",
            "content": "{key_point}",
            "position": (0.5, 0.5),
            "size": (0.7, 0.35),
        },
    ],
    SceneType.ANALOGY: [
        {
            "element_type": "text_block",
            "content": "💡 Analogy",
            "position": (0.5, 0.15),
            "size": (0.4, 0.06),
            "color": "accent",
        },
        {
            "element_type": "text_block",
            "content": "{analogy}",
            "position": (0.5, 0.5),
            "size": (0.7, 0.4),
        },
    ],
    SceneType.SUMMARY: [
        {
            "element_type": "text_block",
            "content": "Summary",
            "position": (0.5, 0.12),
            "size": (0.4, 0.06),
        },
        {
            "element_type": "text_block",
            "content": "{summary}",
            "position": (0.5, 0.5),
            "size": (0.75, 0.5),
        },
    ],
    SceneType.CREDITS: [
        {
            "element_type": "text_block",
            "content": "Thank You",
            "position": (0.5, 0.35),
            "size": (0.5, 0.1),
        },
        {
            "element_type": "text_block",
            "content": "{credits}",
            "position": (0.5, 0.55),
            "size": (0.6, 0.15),
        },
    ],
}


def _classify_segment(index: int, total: int, text: str, emphasis: bool) -> SceneType:
    """Classify a script segment into a scene type based on content and position."""
    text_lower = text.lower()

    if index == 0:
        return SceneType.TITLE
    if index == total - 1:
        return SceneType.CREDITS

    # Keyword-based classification
    if any(word in text_lower for word in ["imagine", "analogy", "think of", "like a"]):
        return SceneType.ANALOGY
    if any(word in text_lower for word in ["summarize", "summary", "in conclusion", "to recap"]):
        return SceneType.SUMMARY
    if any(word in text_lower for word in ["diagram", "experiment", "epr", "bell"]):
        return SceneType.DIAGRAM
    if emphasis:
        return SceneType.KEY_POINT

    return SceneType.EXPLANATION


def _estimate_segment_duration(text: str, pause_after: float = 0.3) -> float:
    """Estimate speaking duration for a text segment.

    Uses ~145 words per minute speaking rate, plus pauses.
    """
    word_count = len(text.split())
    speaking_time = (word_count / 145.0) * 60.0
    return speaking_time + pause_after


def _build_visual_elements(
    scene_type: SceneType,
    narration: str,
    title: str,
    keywords: list[str],
) -> list[VisualElement]:
    """Build visual elements for a scene based on its type and content."""
    templates = SCENE_VISUAL_TEMPLATES.get(scene_type, SCENE_VISUAL_TEMPLATES[SceneType.EXPLANATION])
    elements = []

    # Extract key sentences for visual labels
    sentences = [s.strip() for s in narration.split(".") if s.strip()]
    first_sentence = sentences[0] if sentences else narration[:80]
    body_text = narration if len(narration) <= 200 else narration[:197] + "..."

    # Build context for template substitution
    context = {
        "title": title,
        "subtitle": first_sentence if scene_type == SceneType.TITLE else "",
        "heading": title or first_sentence[:60],
        "body": body_text,
        "key_point": narration,
        "analogy": narration,
        "summary": narration,
        "credits": "Explainer Video Factory",
        "left_label": keywords[0] if keywords else "Concept A",
        "right_label": keywords[1] if len(keywords) > 1 else "Concept B",
        "caption": first_sentence[:80] if first_sentence else "",
    }

    for tmpl in templates:
        content = tmpl["content"]
        # Substitute placeholders
        for key, value in context.items():
            content = content.replace(f"{{{key}}}", value)

        elements.append(VisualElement(
            element_type=tmpl["element_type"],
            content=content,
            position=tmpl["position"],
            size=tmpl["size"],
            color=tmpl.get("color", ""),
        ))

    return elements


class ScenePlanner:
    """Plans scenes from a script, assigning timing and visual elements."""

    def plan(self, script: Script) -> list[Scene]:
        """Break a script into a list of timed scenes.

        Args:
            script: The educational script to segment.

        Returns:
            Ordered list of Scene objects with timing and visual elements.

        Raises:
            ScenePlanningError: If scene planning fails.
        """
        logger.info(
            "scene_planner.plan",
            topic=script.topic,
            num_segments=len(script.segments),
        )

        if not script.segments:
            raise ScenePlanningError(
                "Cannot plan scenes from empty script",
                details={"topic": script.topic},
            )

        try:
            scenes: list[Scene] = []
            current_time = 0.0

            for i, segment in enumerate(script.segments):
                scene_type = _classify_segment(
                    index=i,
                    total=len(script.segments),
                    text=segment.text,
                    emphasis=segment.emphasis,
                )

                duration = _estimate_segment_duration(segment.text, segment.pause_after)

                # Determine scene title
                scene_title = self._extract_scene_title(scene_type, segment.text, script.title)

                # Build visual elements
                visual_elements = _build_visual_elements(
                    scene_type=scene_type,
                    narration=segment.text,
                    title=scene_title,
                    keywords=script.keywords,
                )

                scene = Scene(
                    scene_id=f"scene_{i:03d}",
                    scene_type=scene_type,
                    title=scene_title,
                    narration=segment.text,
                    visual_elements=visual_elements,
                    duration=duration,
                    start_time=current_time,
                    keywords=script.keywords[:4],
                    transition_in="fade" if i == 0 else "crossfade",
                    transition_out="fade" if i == len(script.segments) - 1 else "crossfade",
                )

                scenes.append(scene)
                current_time += duration

            logger.info(
                "scene_planner.complete",
                num_scenes=len(scenes),
                total_duration=f"{current_time:.1f}s",
            )
            return scenes

        except ScenePlanningError:
            raise
        except Exception as e:
            raise ScenePlanningError(
                "Scene planning failed unexpectedly",
                details={"topic": script.topic, "error": str(e)},
            ) from e

    def _extract_scene_title(
        self, scene_type: SceneType, narration: str, script_title: str
    ) -> str:
        """Extract a short title for the scene from its content."""
        if scene_type == SceneType.TITLE:
            return script_title
        if scene_type == SceneType.CREDITS:
            return "Thank You"
        if scene_type == SceneType.SUMMARY:
            return "Summary"

        # Use first sentence or first 50 characters
        sentences = narration.split(".")
        if sentences:
            title = sentences[0].strip()
            if len(title) > 60:
                title = title[:57] + "..."
            return title
        return narration[:50]
