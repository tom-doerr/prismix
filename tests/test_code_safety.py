"""
Test module for code safety checks.
"""

import pytest

from prismix.core.iterative_programmer import setup_agent


@pytest.fixture
def setup_agent_fixture():
    """Fixture to set up the agent."""
    return setup_agent()


@pytest.fixture
def agent():
    """Fixture to create an instance of the agent."""
    return setup_agent()
