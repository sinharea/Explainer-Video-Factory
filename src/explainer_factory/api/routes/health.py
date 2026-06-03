"""Health check endpoints."""

from fastapi import APIRouter

from explainer_factory import __version__
from explainer_factory.api.schemas import HealthResponse
from explainer_factory.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check API health status."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=__version__,
        environment=settings.app_env,
    )
