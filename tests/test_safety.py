import unittest
import dspy
from prismix.core.signatures import CodeSafetyCheck
from prismix.core.iterative_programmer import IterativeProgrammer

class TestSafetyCheck(unittest.TestCase):
    def setUp(self):
        lm = dspy.LM(model="gpt-4o-mini", max_tokens=2000)
        dspy.configure(lm=lm)
        self.programmer = IterativeProgrammer()

    def test_safe_code(self):
        safe_code = """
def add(a, b):
    return a + b
"""
        is_safe, message = self.programmer.is_code_safe(safe_code)
        self.assertTrue(is_safe)
        self.assertEqual(message, "The code is safe.")

    def test_code_with_print(self):
        code_with_print = """
def add(a, b):
    print(f"The sum is {a + b}")
    return a + b
"""
        is_safe, message = self.programmer.is_code_safe(code_with_print)
        self.assertTrue(is_safe)
        self.assertEqual(message, "The code is safe.")

    def test_unsafe_code(self):
        unsafe_code = """
import os
os.system("rm -rf /")
"""
        is_safe, message = self.programmer.is_code_safe(unsafe_code)
        self.assertFalse(is_safe)
        self.assertIn("potential security risk", message)

if __name__ == '__main__':
    unittest.main()