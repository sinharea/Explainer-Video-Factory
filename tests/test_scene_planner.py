"""Tests for the scene planner."""

import pytest

from explainer_factory.models.scene import Scene
from explainer_factory.pipeline.scene_planner import ScenePlanner
from explainer_factory.pipeline.script_generator import ScriptGenerator


def test_scene_planner():
    """Test scene planning from a generated script."""
    generator = ScriptGenerator(use_llm=False)
    script = generator.generate("Quantum Entanglement")
    
    planner = ScenePlanner()
    scenes = planner.plan(script)
    
    assert len(scenes) == len(script.segments)
    for scene in scenes:
        assert isinstance(scene, Scene)
        assert scene.duration > 0.0
        assert scene.narration != ""
        assert len(scene.visual_elements) > 0
