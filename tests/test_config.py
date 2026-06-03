"""Tests for configuration management."""

import pytest

from explainer_factory.config import Settings, get_settings


def test_default_settings():
    """Test that default settings are loaded correctly."""
    settings = get_settings()
    assert settings.app_env == "development"
    assert settings.video.width == 1920
    assert settings.video.height == 1080
    assert settings.tts.voice == "en-US-AriaNeural"


def test_theme_loading():
    """Test that default theme matches expectations."""
    settings = get_settings()
    theme = settings.theme
    assert theme.name == "default"
    assert theme.primary_color == "#4F46E5"
