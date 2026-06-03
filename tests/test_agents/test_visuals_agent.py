"""Tests for the visuals agent."""

import pytest

from explainer_factory.agents.avatar_agent import AvatarAgent
from explainer_factory.agents.visuals_agent import VisualsAgent
from explainer_factory.models.render_job import RenderJob


def test_visuals_agent_plan_scenes():
    """Test scene planning via the visuals agent."""
    avatar = AvatarAgent(use_llm=False)
    visuals = VisualsAgent()
    
    job = RenderJob(topic="Quantum Entanglement")
    job = avatar.generate_script(job)
    
    updated_job = visuals.plan_scenes(job)
    
    assert updated_job.scenes is not None
    assert len(updated_job.scenes) == len(job.script.segments)
