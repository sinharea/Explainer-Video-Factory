"""Tests for the script generator."""

import pytest

from explainer_factory.models.script import Script
from explainer_factory.pipeline.script_generator import ScriptGenerator


def test_script_generator_template_match():
    """Test script generation using predefined templates."""
    generator = ScriptGenerator(use_llm=False)
    script = generator.generate("Quantum Entanglement")
    
    assert isinstance(script, Script)
    assert script.topic == "Quantum Entanglement"
    assert "Spooky" in script.title
    assert len(script.segments) > 10
    assert "superposition" in script.keywords


def test_script_generator_fallback():
    """Test script generation for unknown topics."""
    generator = ScriptGenerator(use_llm=False)
    script = generator.generate("Unknown Topic XYZ")
    
    assert isinstance(script, Script)
    assert "Unknown Topic XYZ" in script.title
    assert len(script.segments) == 7
    assert script.keywords == ["unknown topic xyz"]
