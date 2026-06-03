"""Graph nodes for the rendering pipeline orchestrator.

Defines the individual steps in the LangGraph state machine, mapping
state transitions to agent actions.
"""

from __future__ import annotations

from explainer_factory.agents.avatar_agent import AvatarAgent
from explainer_factory.agents.synthesis_agent import SynthesisAgent
from explainer_factory.agents.visuals_agent import VisualsAgent
from explainer_factory.logging import get_logger
from explainer_factory.models.render_job import RenderStatus
from explainer_factory.orchestrator.state import PipelineState

logger = get_logger(__name__)

# Initialize agents
avatar_agent = AvatarAgent()
visuals_agent = VisualsAgent()
synthesis_agent = SynthesisAgent()


def generate_script_node(state: PipelineState) -> PipelineState:
    """Generate the educational script."""
    job = state["job"]
    logger.info("node.generate_script", job_id=job.job_id)
    
    try:
        job.update_status(RenderStatus.GENERATING_SCRIPT)
        updated_job = avatar_agent.generate_script(job)
        return {"job": updated_job, "errors": []}
    except Exception as e:
        logger.error("node.generate_script.error", error=str(e))
        return {"job": job, "errors": [f"Script generation failed: {e}"]}


def plan_scenes_node(state: PipelineState) -> PipelineState:
    """Plan scenes from the generated script."""
    job = state["job"]
    logger.info("node.plan_scenes", job_id=job.job_id)
    
    try:
        job.update_status(RenderStatus.PLANNING_SCENES)
        updated_job = visuals_agent.plan_scenes(job)
        return {"job": updated_job, "errors": []}
    except Exception as e:
        logger.error("node.plan_scenes.error", error=str(e))
        return {"job": job, "errors": [f"Scene planning failed: {e}"]}


def render_audio_node(state: PipelineState) -> PipelineState:
    """Render TTS audio for scenes."""
    job = state["job"]
    logger.info("node.render_audio", job_id=job.job_id)
    
    try:
        job.update_status(RenderStatus.RENDERING_AUDIO)
        updated_job = avatar_agent.render_audio(job)
        return {"job": updated_job, "errors": []}
    except Exception as e:
        logger.error("node.render_audio.error", error=str(e))
        return {"job": job, "errors": [f"Audio rendering failed: {e}"]}


def render_visuals_node(state: PipelineState) -> PipelineState:
    """Render visuals for scenes."""
    job = state["job"]
    logger.info("node.render_visuals", job_id=job.job_id)
    
    try:
        # Prevent overwriting status if parallel node already updated it
        if job.status != RenderStatus.RENDERING_AUDIO:
            job.update_status(RenderStatus.RENDERING_VISUALS)
            
        updated_job = visuals_agent.render_visuals(job)
        return {"job": updated_job, "errors": []}
    except Exception as e:
        logger.error("node.render_visuals.error", error=str(e))
        return {"job": job, "errors": [f"Visual rendering failed: {e}"]}


def synthesize_video_node(state: PipelineState) -> PipelineState:
    """Synthesize the final video."""
    job = state["job"]
    logger.info("node.synthesize_video", job_id=job.job_id)
    
    try:
        job.update_status(RenderStatus.COMPOSING_VIDEO)
        updated_job = synthesis_agent.synthesize(job)
        updated_job.update_status(RenderStatus.COMPLETED)
        return {"job": updated_job, "errors": []}
    except Exception as e:
        logger.error("node.synthesize_video.error", error=str(e))
        return {"job": job, "errors": [f"Video synthesis failed: {e}"]}
