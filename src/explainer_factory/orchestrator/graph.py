"""LangGraph orchestration graph.

Defines the multi-agent workflow graph for the entire video generation pipeline.
Supports parallel execution of audio and visual rendering.
"""

from __future__ import annotations

import time

from langgraph.graph import END, START, StateGraph

from explainer_factory.logging import get_logger
from explainer_factory.models.render_job import RenderJob, RenderStatus
from explainer_factory.orchestrator.nodes import (
    generate_script_node,
    plan_scenes_node,
    render_audio_node,
    render_visuals_node,
    synthesize_video_node,
)
from explainer_factory.orchestrator.state import PipelineState

logger = get_logger(__name__)


def route_after_planning(state: PipelineState) -> list[str]:
    """Determine routing after scene planning.
    
    If there are errors, halt. Otherwise, split to parallel renderers.
    """
    if state.get("errors"):
        return ["error_handler"]
    return ["render_audio", "render_visuals"]


def route_after_parallel(state: PipelineState) -> str:
    """Determine routing after parallel rendering.
    
    Join point for audio and visuals before synthesis.
    """
    if state.get("errors"):
        return "error_handler"
    return "synthesize_video"


def error_handler_node(state: PipelineState) -> PipelineState:
    """Handle fatal pipeline errors."""
    job = state["job"]
    errors = state.get("errors", ["Unknown pipeline error"])
    
    error_msg = "; ".join(errors)
    logger.error("orchestrator.pipeline_failed", job_id=job.job_id, error=error_msg)
    
    job.mark_failed(message=error_msg)
    return {"job": job, "errors": []}


def create_pipeline_graph() -> StateGraph:
    """Create and configure the LangGraph workflow.

    Returns:
        Compiled StateGraph ready for execution.
    """
    workflow = StateGraph(PipelineState)

    # Add all nodes
    workflow.add_node("generate_script", generate_script_node)
    workflow.add_node("plan_scenes", plan_scenes_node)
    workflow.add_node("render_audio", render_audio_node)
    workflow.add_node("render_visuals", render_visuals_node)
    workflow.add_node("synthesize_video", synthesize_video_node)
    workflow.add_node("error_handler", error_handler_node)

    # Define execution edges
    workflow.add_edge(START, "generate_script")
    
    # Simple sequential check
    workflow.add_conditional_edges(
        "generate_script",
        lambda state: "error_handler" if state.get("errors") else "plan_scenes"
    )
    
    # Simple sequential execution
    workflow.add_conditional_edges(
        "plan_scenes",
        lambda state: "error_handler" if state.get("errors") else "render_audio"
    )
    workflow.add_edge("render_audio", "render_visuals")
    workflow.add_edge("render_visuals", "synthesize_video")
    
    # Finalize
    workflow.add_conditional_edges(
        "synthesize_video",
        lambda state: "error_handler" if state.get("errors") else END
    )
    workflow.add_edge("error_handler", END)

    return workflow.compile()


class PipelineOrchestrator:
    """Manages execution of the video generation pipeline."""

    def __init__(self):
        """Initialize the orchestrator."""
        self.graph = create_pipeline_graph()
        logger.info("orchestrator.init")

    def run(self, job: RenderJob) -> RenderJob:
        """Run the complete pipeline for a render job.

        Args:
            job: The render job to process.

        Returns:
            Completed or failed render job.
        """
        logger.info("orchestrator.run.start", job_id=job.job_id, topic=job.topic)
        
        job.pipeline_start_time = time.time()
        initial_state: PipelineState = {"job": job, "errors": []}
        
        try:
            # Execute the graph
            final_state = self.graph.invoke(initial_state)
            
            job = final_state["job"]
            job.pipeline_end_time = time.time()
            
            if job.status == RenderStatus.COMPLETED:
                logger.info(
                    "orchestrator.run.success", 
                    job_id=job.job_id, 
                    duration=f"{job.duration_seconds:.1f}s"
                )
            else:
                logger.error(
                    "orchestrator.run.failed", 
                    job_id=job.job_id,
                    status=job.status.value
                )
                
            return job
            
        except Exception as e:
            logger.error("orchestrator.run.fatal", job_id=job.job_id, error=str(e))
            job.mark_failed(message=f"Fatal orchestrator error: {e}")
            job.pipeline_end_time = time.time()
            return job
