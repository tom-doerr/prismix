"""
Test module for factorial calculations.
"""

import pytest
from prismix.core.executor import CodeExecutor
from prismix.core.iterative_programmer import CodeResult, setup_agent


def test_factorial_basic():
    """Test basic factorial calculation."""
    programmer = setup_agent()
    result = programmer.forward(
        "Create a function that calculates factorial of a number"
    )

    # Safer execution using CodeExecutor
    code_result = CodeExecutor.execute(
        result.code.replace("```python", "").replace("```", "")
    )
    assert code_result.success, f"Code execution failed: {code_result.error}"
    factorial = locals().get("factorial")

    # Test basic cases
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(5) == 120


def test_factorial_negative():
    """Test factorial calculation with negative input."""
    programmer = setup_agent()
    result = programmer.forward(
        "Create a function that calculates factorial of a number"
    )

    # Execute the generated code
    local_vars = {}
    exec(result.code, {}, local_vars)
    factorial = local_vars["factorial"]

    # Test negative input
    with pytest.raises(ValueError):
        factorial(-1)


def test_code_result_structure():
    """Test the structure of the CodeResult object."""
    programmer = setup_agent()
    result = programmer.forward(
        "Create a function that calculates factorial of a number"
    )

    assert isinstance(result, CodeResult)
    assert isinstance(result.code, str)
    assert isinstance(result.success, bool)
    assert isinstance(result.output, str)
    assert result.success is True
    assert "factorial" in result.code
