import pytest
from prismix.main import execute_instruction
from unittest.mock import patch
import io

def test_execute_instruction_code_result():
    with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
        execute_instruction("create a function that adds two numbers")
        assert "Success:" in mock_stdout.getvalue()
        assert "Generated code saved to:" in mock_stdout.getvalue()

def test_execute_instruction_file_edit():
    with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
        execute_instruction("edit samples/basic_function.py Replace 'print(f\"Calculated sum: {a + b + c}\")' with 'print(f\"The sum is: {a + b + c}\")'")
        assert "Changes made:" in mock_stdout.getvalue()
        assert "- Replace 'print(f\"Calculated sum: {a + b + c}\")' with 'print(f\"The sum is: {a + b + c}\")'" in mock_stdout.getvalue()
        assert "Updated file contents:" in mock_stdout.getvalue()
        with open("samples/basic_function.py", "r") as f:
            assert "print(f\"The sum is: {a + b + c}\")" in f.read()
        execute_instruction("edit samples/basic_function.py Replace 'print(f\"The sum is: {a + b + c}\")' with 'print(f\"Calculated sum: {a + b + c}\")'")
        with open("samples/basic_function.py", "r") as f:
            assert "print(f\"Calculated sum: {a + b + c}\")" in f.read()