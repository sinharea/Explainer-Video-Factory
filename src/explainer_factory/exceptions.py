"""Custom exception hierarchy for the Explainer Video Factory."""


class ExplainerFactoryError(Exception):
    """Base exception for all Explainer Video Factory errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.details = details or {}


class ScriptGenerationError(ExplainerFactoryError):
    """Raised when script generation fails."""
    pass


class ScenePlanningError(ExplainerFactoryError):
    """Raised when scene planning/segmentation fails."""
    pass


class TTSRenderError(ExplainerFactoryError):
    """Raised when text-to-speech rendering fails."""
    pass


class VisualRenderError(ExplainerFactoryError):
    """Raised when visual/image rendering fails."""
    pass


class VideoCompositionError(ExplainerFactoryError):
    """Raised when video composition/encoding fails."""
    pass


class PipelineError(ExplainerFactoryError):
    """Raised when the overall pipeline encounters a fatal error."""
    pass


class ConfigurationError(ExplainerFactoryError):
    """Raised when configuration is invalid or missing."""
    pass


class AgentError(ExplainerFactoryError):
    """Raised when an agent encounters an unrecoverable error."""

    def __init__(self, agent_name: str, message: str, details: dict | None = None):
        super().__init__(f"[{agent_name}] {message}", details)
        self.agent_name = agent_name


class TimelineError(ExplainerFactoryError):
    """Raised when timeline synchronization fails."""
    pass


class AssetError(ExplainerFactoryError):
    """Raised when a required asset is missing or invalid."""
    pass
