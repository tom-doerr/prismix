"""
Test module for factorial calculations.
"""

import ast

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
    cleaned_code = result.code.replace("```python", "").replace("```", "").strip()

    # Extract the factorial function definition
    tree = ast.parse(cleaned_code)
    function_def = next(
        (node for node in tree.body if isinstance(node, ast.FunctionDef)), None
    )
    if function_def:
        function_code = ast.unparse(function_def)
    else:
        raise ValueError("No function definition found in the generated code.")

    code_result = CodeExecutor.execute(function_code)
    assert code_result.success, f"Code execution failed: {code_result.error}"

    # Execute the factorial function directly
    local_vars = {}
    # Safer alternative: Use CodeExecutor to execute the function code
    code_result = CodeExecutor.execute(function_code)
    assert code_result.success, f"Code execution failed: {code_result.error}"
    local_vars = {"factorial": lambda x: code_result.output}
    factorial = local_vars.get("factorial")

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

    cleaned_code = result.code.replace("```python", "").replace("```", "").strip()
    tree = ast.parse(cleaned_code)
    function_def = next(
        (node for node in tree.body if isinstance(node, ast.FunctionDef)), None
    )
    function_code = ast.unparse(function_def)
    local_vars = {}
    local_vars = {}
    exec(function_code, globals(), local_vars)
    factorial = local_vars.get("factorial")
    assert factorial(5) == 120
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
