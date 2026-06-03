"""Application configuration management using Pydantic Settings.

Loads configuration from environment variables and .env files, with
sensible defaults for all settings. Supports typed access to all
pipeline configuration parameters.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TTSSettings(BaseSettings):
    """Text-to-speech engine configuration."""
    model_config = SettingsConfigDict(env_prefix="TTS_")

    voice: str = "en-US-AriaNeural"
    rate: str = "+0%"
    volume: str = "+0%"


class VideoSettings(BaseSettings):
    """Video output configuration."""
    model_config = SettingsConfigDict(env_prefix="VIDEO_")

    width: int = 1920
    height: int = 1080
    fps: int = 24
    codec: str = "libx264"
    bitrate: str = "4000k"
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"

    @property
    def resolution(self) -> tuple[int, int]:
        """Return (width, height) tuple."""
        return (self.width, self.height)


class ThemeSettings(BaseSettings):
    """Visual theme configuration."""
    model_config = SettingsConfigDict(env_prefix="THEME_")

    name: str = "default"
    primary_color: str = "#4F46E5"
    secondary_color: str = "#7C3AED"
    bg_color: str = "#0F172A"
    text_color: str = "#F8FAFC"
    accent_color: str = "#06B6D4"

    def load_theme_file(self, themes_dir: Path) -> dict:
        """Load full theme configuration from JSON file.

        Args:
            themes_dir: Directory containing theme JSON files.

        Returns:
            Complete theme dictionary merged with environment overrides.
        """
        theme_path = themes_dir / f"{self.name}.json"
        if theme_path.exists():
            with open(theme_path) as f:
                theme_data = json.load(f)
            # Override colors from env if set
            theme_data["colors"].update({
                "primary": self.primary_color,
                "secondary": self.secondary_color,
                "background": self.bg_color,
                "text": self.text_color,
                "accent": self.accent_color,
            })
            return theme_data
        # Fallback: return env-only theme
        return {
            "name": self.name,
            "colors": {
                "primary": self.primary_color,
                "secondary": self.secondary_color,
                "background": self.bg_color,
                "text": self.text_color,
                "accent": self.accent_color,
            },
            "typography": {
                "title_font_size": 72,
                "heading_font_size": 48,
                "body_font_size": 32,
                "caption_font_size": 24,
                "subtitle_font_size": 28,
            },
            "layout": {"margin": 80, "padding": 40, "corner_radius": 20},
            "transitions": {"default_duration": 0.5, "fade_duration": 0.3},
        }


class LLMSettings(BaseSettings):
    """LLM configuration (optional)."""
    model_config = SettingsConfigDict(env_prefix="LLM_")

    provider: str | None = None
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096

    @property
    def is_enabled(self) -> bool:
        """Check if LLM integration is configured."""
        return self.provider is not None


class Settings(BaseSettings):
    """Root application settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # General
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    log_format: str = "console"

    # Paths
    output_dir: Path = Field(default=Path("./outputs"))
    temp_dir: Path = Field(default=Path("./tmp"))
    assets_dir: Path = Field(default=Path("./assets"))
    max_video_duration_seconds: int = 600

    # Sub-settings
    tts: TTSSettings = Field(default_factory=TTSSettings)
    video: VideoSettings = Field(default_factory=VideoSettings)
    theme: ThemeSettings = Field(default_factory=ThemeSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    @property
    def themes_dir(self) -> Path:
        """Path to themes directory."""
        return self.assets_dir / "themes"

    @property
    def fonts_dir(self) -> Path:
        """Path to fonts directory."""
        return self.assets_dir / "fonts"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings singleton.

    Returns:
        Application settings loaded from environment.
    """
    return Settings()
