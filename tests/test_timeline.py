"""Tests for the timeline module."""

import pytest

from explainer_factory.models.scene import Scene, SceneType
from explainer_factory.pipeline.timeline import Timeline


def test_timeline_build():
    """Test building a timeline from scenes."""
    scenes = [
        Scene(scene_id="s1", scene_type=SceneType.TITLE, narration="A", duration=5.0),
        Scene(scene_id="s2", scene_type=SceneType.EXPLANATION, narration="B", duration=10.0),
    ]
    
    timeline = Timeline()
    timeline.build_from_scenes(scenes)
    
    assert timeline.scene_count == 2
    assert timeline.total_duration == 15.0
    assert timeline.entries[0].start_time == 0.0
    assert timeline.entries[0].end_time == 5.0
    assert timeline.entries[1].start_time == 5.0
    assert timeline.entries[1].end_time == 15.0


def test_timeline_update_actual_durations():
    """Test updating timeline with actual audio durations."""
    scenes = [
        Scene(scene_id="s1", scene_type=SceneType.TITLE, narration="A", duration=5.0),
        Scene(scene_id="s2", scene_type=SceneType.EXPLANATION, narration="B", duration=10.0),
    ]
    
    timeline = Timeline()
    timeline.build_from_scenes(scenes)
    
    actual_durations = {"s1": 6.0, "s2": 9.5}
    timeline.update_with_actual_durations(actual_durations)
    
    assert timeline.total_duration == 15.5
    assert timeline.entries[0].duration == 6.0
    assert timeline.entries[1].duration == 9.5
