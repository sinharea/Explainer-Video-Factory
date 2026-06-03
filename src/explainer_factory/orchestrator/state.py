"""State schema for the LangGraph orchestrator."""

from __future__ import annotations

from typing import Annotated, TypedDict

from explainer_factory.models.render_job import RenderJob


class PipelineState(TypedDict):
    """Shared state for the rendering pipeline graph."""
    
    # The core render job being processed
    job: RenderJob
    
    # List of errors encountered during processing
    # Annotated with a reducer to append rather than overwrite
    errors: Annotated[list[str], lambda x, y: x + y]
