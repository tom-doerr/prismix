"""
Test suite for the safety checks in the IterativeProgrammer module.
"""

import unittest
import dspy
from prismix.core.iterative_programmer import IterativeProgrammer


import pytest
from prismix.core.iterative_programmer import IterativeProgrammer


@pytest.fixture
def setup_agent_fixture():
    return setup_agent()


class TestSafetyCheck(unittest.TestCase):
    """Test class for safety checks in the IterativeProgrammer module."""

    def setUp(self):
        """Set up the test environment with a mock language model."""
        dspy.configure(lm=dspy.LM(model="gpt-4o-mini", max_tokens=2000))
        self.programmer = IterativeProgrammer()

    def test_safe_code(self):
        """Test that safe code is identified as safe."""
        safe_code = """
def safe_function(): return 42
"""
        is_safe, message = self.programmer.is_code_safe(safe_code)
        self.assertTrue(is_safe)
        self.assertIn(
            (
                "The code defines a simple function that returns a constant value (42) "
                "and does not involve any user input or external data, making it safe."
            ),
            message,
        )

    def test_code_with_print(self):
        """Test that code with print is identified as safe."""
        code_with_print = """
def add(a, b):
    print(f"The sum is {a + b}")
    return a + b
"""
        is_safe, message = self.programmer.is_code_safe(code_with_print)
        self.assertTrue(is_safe)
        self.assertEqual(
            message,
            (
                "The code simply prints the sum of two numbers, which is generally safe "
                "as it does not expose sensitive information or perform any harmful operations."
            ),
        )

    def test_unsafe_code(self):
        """Test that unsafe code is identified as unsafe."""
        unsafe_code = """
import os
os.system("rm -rf /")
"""
        is_safe, message = self.programmer.is_code_safe(unsafe_code)
        self.assertFalse(is_safe)
        self.assertIn("potentially unsafe operations", message)


if __name__ == "__main__":
    unittest.main()
