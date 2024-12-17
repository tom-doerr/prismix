"""
Test suite for the IterativeProgrammer module.
"""

import dspy
import pytest
from prismix.core.iterative_programmer import IterativeProgrammer


"""Mock implementation of the __call__ method."""
    if "unsafe" in prompt.lower():
            return dspy.Prediction(
                is_safe=False,
                safety_message="The code contains potentially unsafe operations.",
            )
        return dspy.Prediction(is_safe=True, safety_message="The code is safe.")


@pytest.fixture(scope="function", autouse=True)
def setup_dspy():
    """Set up dspy with a mock LM for each test."""
    lm = MockLM()
    dspy.configure(lm=lm)


def test_is_code_safe_safe():
    """Test that safe code is identified as safe."""
    programmer = IterativeProgrammer()
    code = "def hello():\n    print('hello')\n"
    is_safe, _ = programmer.is_code_safe(code)
    assert is_safe


def test_is_code_safe_unsafe():
    """Test that unsafe code is identified as unsafe."""
    programmer = IterativeProgrammer()
    code = "import os\n os.system('rm -rf /')"
    is_safe, _ = programmer.is_code_safe(code)
    assert not is_safe


def test_execute_code_success():
    """Test successful execution of code."""
    programmer = IterativeProgrammer()
    code = """# samples/basic_function.py
def calculate_sum(a, b, c):
    print(f"Calculated sum: {a + b + c}")
    return a + b + c

def main():
    result = calculate_sum(5, 3, 0)
    print(f"Sum: {result}")

if __name__ == "__main__":
    main()
"""
    result = programmer.execute_code(code)
    assert result.success
    assert "Sum: 8" in result.output
    assert "Function execution failed" not in result.error


def test_execute_code_fail():
    """Test failed execution of code."""
    programmer = IterativeProgrammer()
    code = """# samples/basic_function.py
def calculate_sum(a, b, c):
    print(f"Calculated sum: {a + b + c}")
    return a + b + c

def main():
    result = calculate_sum(5, "a", 0)
    print(f"Sum: {result}")

if __name__ == "__main__":
    main()
"""
    result = programmer.execute_code(code)
    assert not result.success
    assert "TypeError" in result.error
