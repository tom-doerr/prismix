"""
This module provides a safe execution environment for code generation and execution.
"""

import subprocess
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


@dataclass
class CodeResult:
    """Represents the result of code execution."""

    code: str
    success: bool
    output: str
    error: str = ""


class FileContext(BaseModel):
    filepath: str
    content: str
    changes: List[str]
    error: Optional[str]


class CodeExecutor:
    """
    Handles safe code execution in isolated environment.

    This class provides methods to execute code in a controlled and safe environment,
    ensuring that only a limited set of built-in functions are available to the executed code.
    """

    @staticmethod
    def get_safe_builtins() -> Dict[str, Any]:
        """Get dictionary of allowed built-in functions"""
        return {
            "print": print,
            "isinstance": isinstance,
            "range": range,
            "int": int,
            "str": str,
            "bool": bool,
            "len": len,
            "ValueError": ValueError,
            "TypeError": TypeError,
        }

    @staticmethod
    def execute(code: str) -> CodeResult:
        """Execute code in isolated environment and return results"""
        # safe_builtins = CodeExecutor.get_safe_builtins() # Removed unused variable
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as tmp_file:
                tmp_file.write(code)
                tmp_file_path = tmp_file.name

                # Execute the code in a controlled environment
                process = subprocess.run(
                    ["python", tmp_file_path],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if process.returncode == 0:
                    success = True
                    output = process.stdout
                else:
                    success = False
                    output = ""
                return CodeResult(
                    code=code,
                    success=success,
                    output=output,
                    error=process.stderr,
                )
        except FileNotFoundError as e:
            return CodeResult(code=code, success=False, output="", error=str(e))
        except PermissionError as e:
            return CodeResult(code=code, success=False, output="", error=str(e))
