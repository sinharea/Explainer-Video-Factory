"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from explainer_factory import __version__
from explainer_factory.api.routes import health, render
from explainer_factory.config import get_settings
from explainer_factory.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager (startup/shutdown events)."""
    settings = get_settings()
    
    # Initialize logging
    setup_logging(
        level=settings.log_level,
        log_format=settings.log_format,
    )
    
    # Ensure required directories exist
    settings.ensure_directories()
    
    logger.info("api.startup", version=__version__, env=settings.app_env)
    
    yield
    
    logger.info("api.shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="Explainer Video Factory API",
        description="Multi-modal synchronous rendering pipeline",
        version=__version__,
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(render.router, prefix="/api/v1")

    # Static files mounting for served videos
    app.mount("/outputs", StaticFiles(directory=settings.output_dir), name="outputs")

    return app


app = create_app()
