"""
Test module for code safety checks.
"""

import pytest
from prismix.core.iterative_programmer import setup_agent


@pytest.fixture
def setup_agent_fixture():
    return setup_agent()




@pytest.fixture
def agent():
    return setup_agent()
