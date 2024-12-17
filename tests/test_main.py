"""
Test suite for the main functionality of the Prismix application.
"""

import sys
from unittest.mock import patch
from io import StringIO

sys.path.append(".")
import sys
from unittest.mock import patch
from io import StringIO

sys.path.append(".")
from prismix.main import execute_instruction


def test_execute_instruction_code_result():
    """Test the execution of an instruction that generates code."""
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        execute_instruction("create a function that adds two numbers")
        assert "Success:" in mock_stdout.getvalue()
        assert "Generated code saved to:" in mock_stdout.getvalue()


def test_execute_instruction_file_edit():
    """Test the execution of an instruction that edits a file."""
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        execute_instruction(
            "edit samples/basic_function.py Replace 'print(f\"Calculated sum: {a + b + c}\")' with 'print(f\"The sum is: {a + b + c}\")'"
        )
        assert "Changes made:" in mock_stdout.getvalue()
        assert (
            "- Replace 'print(f\"Calculated sum: {a + b + c}\")' with 'print(f\"The sum is: {a + b + c}\")'"
            in mock_stdout.getvalue()
        )
