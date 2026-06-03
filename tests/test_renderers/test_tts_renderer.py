"""Tests for the TTS renderer."""

import os
import tempfile
from pathlib import Path

import pytest

from explainer_factory.renderers.tts_renderer import TTSRenderer


@pytest.mark.asyncio
async def test_tts_render_segment():
    """Test rendering a single TTS segment."""
    renderer = TTSRenderer()
    
    with tempfile.TemporaryDirectory() as td:
        output_path = Path(td) / "test.mp3"
        result = await renderer.render_segment_async("Test", output_path)
        
        assert result["duration"] > 0
        assert result["path"] == output_path
        assert output_path.exists()
