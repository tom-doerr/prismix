"""
Test module for code safety checks.
"""
"""
Test module for code safety checks.
"""

import pytest
from prismix.core.iterative_programmer import IterativeProgrammer, setup_agent


@pytest.fixture
def agent():
    return setup_agent()


def test_safe_code(agent):
    code = "def safe_function(): return 42"
    result = agent.execute_code(code)
    assert result.success is True

def test_unsafe_code(agent):
    code = "import os; os.system('rm -rf /')"
    result = agent.execute_code(code)
    assert result.success is False

def test_safe_code_with_input(agent):
    code = "def safe_function(x): return x * 2"
    result = agent.execute_code(code)
    assert result.success is True

def test_unsafe_code_with_input(agent):
    code = "import os; os.system('rm -rf /')"
    result = agent.execute_code(code)
    assert result.success is False

def test_safe_code_with_output(agent):
    code = "def safe_function(x): return x * 2"
    result = agent.execute_code(code)
    assert result.success is True
