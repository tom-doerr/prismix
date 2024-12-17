"""
Test module for code safety checks.
"""

import pytest
from prismix.core.iterative_programmer import setup_agent


@pytest.fixture
def agent():
    return setup_agent()


def test_safe_code(agent):
    """Test safe code execution."""
    code = "def safe_function(): return 42"
    result = agent.execute_code(code)
    assert result.success is True, f"Code execution failed: {result.error}"


def test_unsafe_code(agent):
    """Test unsafe code execution."""
    code = "import os; os.system('rm -rf /')"
    result = agent.execute_code(code)
    assert result.success is False


def test_safe_code_with_input(agent):
    """Test safe code execution with input."""
    code = "def safe_function(x): return x * 2"
    result = agent.execute_code(code)
    assert result.success is True


def test_unsafe_code_with_input(agent):
    """Test unsafe code execution with input."""
    code = "import os; os.system('rm -rf /')"
    result = agent.execute_code(code)
    assert result.success is False


def test_safe_code_with_output(agent):
    """Test safe code execution with output."""
    code = "def safe_function(x): return x * 2"
    result = agent.execute_code(code)
    assert result.success is True
