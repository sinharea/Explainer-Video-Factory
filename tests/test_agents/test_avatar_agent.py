"""Tests for the avatar agent."""

import pytest

from explainer_factory.agents.avatar_agent import AvatarAgent
from explainer_factory.models.render_job import RenderJob


def test_avatar_agent_generate_script():
    """Test script generation via the avatar agent."""
    agent = AvatarAgent(use_llm=False)
    job = RenderJob(topic="Quantum Entanglement")
    
    updated_job = agent.generate_script(job)
    
    assert updated_job.script is not None
    assert updated_job.script.topic == "Quantum Entanglement"
    assert len(updated_job.script.segments) > 0
