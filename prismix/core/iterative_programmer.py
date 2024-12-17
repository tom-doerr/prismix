"""
Module for iterative programming and code generation.
"""

import subprocess
import sys
import tempfile
from io import StringIO
from subprocess import CalledProcessError
from typing import Tuple, Union

import dspy

from prismix.core.executor import CodeResult
from prismix.core.file_operations import FileContext, FileEditor
from prismix.core.generator import CodeGenerator
from prismix.core.signatures import CodeSafetyCheck


def is_code_safe(code: str, safety_checker: dspy.TypedPredictor) -> Tuple[bool, str]:
    """Check if the generated code is safe to execute."""
    if "import os" in code or "os.system" in code:
        return (
            False,
            "The code contains potentially unsafe operations (e.g., import os, os.system).",
        )
    safety_check = safety_checker(code=code)
    return safety_check.is_safe, safety_check.safety_message


class IterativeProgrammer(dspy.Module):
    """Class for iterative programming and code generation."""

    def __init__(self, max_iterations: int = 3) -> None:
        """Initialize the IterativeProgrammer with a maximum number of iterations."""
        super().__init__()
        self.generator = CodeGenerator(max_iterations)
        self.safety_checker = dspy.TypedPredictor(CodeSafetyCheck)
        self.file_editor = FileEditor()
        self.max_iterations = max_iterations

    def is_code_safe(self, code: str) -> Tuple[bool, str]:
        """Check if the generated code is safe to execute."""
        return is_code_safe(code, self.safety_checker)

    def execute_code(self, code: str) -> CodeResult:
        """Execute the generated code in a safe environment and return results."""
        is_safe, safety_msg = self.is_code_safe(code)
        print("is_safe:", is_safe)
        if not is_safe:
            return CodeResult(
                code=code,
                success=False,
                output="",
                error=f"Safety check failed: {safety_msg}",
            )
        try:
            # Extract the file path from the code comment
            lines = code.splitlines()
            file_path = None
            for line in lines:
                if line.strip().startswith("#"):
                    file_path = line.strip()[1:].strip()
                    break
            if not file_path:
                # If no file path is provided, use a temporary file
                with tempfile.NamedTemporaryFile(
                    mode="w", delete=False, suffix=".py", encoding="utf-8"
                ) as temp_file:
                    temp_file_path = temp_file.name
                    temp_file.write(code)
                file_path = temp_file_path

            # Read the original file content
            with open(file_path, "r", encoding="utf-8") as f:
                original_content = f.read()

            # Apply the changes to the original content
            file_editor = FileEditor()
            modified_content, _ = file_editor.apply_line_edits(original_content, code)

            # Write the modified content back to the original file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(modified_content)

            # Capture stdout and stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            old_stdout, old_stderr = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = StringIO(), StringIO()

            # Execute the modified file
            result = subprocess.run(
                [sys.executable, file_path], check=True, text=True, capture_output=True
            )

            # Restore stdout and stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            output = result.stdout
            error = result.stderr

            return CodeResult(code=code, success=True, output=output, error=error)
        except (CalledProcessError, FileNotFoundError, PermissionError) as e:
            return CodeResult(
                code=code,
                success=False,
                output="",
                error=f"Function execution failed in {file_path}: {str(e)}",
            )

    def forward(self, command: str) -> Union[CodeResult, FileContext]:
        """Generate and execute code or edit files based on the command."""
        if command.startswith("edit"):
            return self._handle_edit_command(command)

        return self._handle_code_generation(command)


def setup_agent() -> IterativeProgrammer:
    """Configure and return an instance of IterativeProgrammer."""
    # Configure LM
    lm = dspy.LM(model="gpt-4o-mini", max_tokens=2000)
    dspy.configure(lm=lm)

    return IterativeProgrammer()
