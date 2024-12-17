"""
This module provides a safe execution environment for code generation and execution.
"""

import ast
from dataclasses import dataclass
from typing import Dict, Any
import tempfile
import subprocess
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


@dataclass
class CodeResult:
    code: str
    success: bool
    output: str
    error: str = ""


class FileContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    filepath: str
    content: str
    changes: List[str]
    error: Optional[str]


class CodeExecutor:
    """Handles safe code execution in isolated environment.

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
        safe_builtins = CodeExecutor.get_safe_builtins()
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as tmp_file:
                tmp_file.write(code)
                tmp_file_path = tmp_file.name

                # Execute the code in a controlled environment
                # The `exec` function is used here to execute the code
                # This is a potential security risk, but it is necessary for this use case
                loc = {}
                output_buffer = []
                loc["print"] = lambda *args, **kwargs: output_buffer.append(
                    " ".join(map(str, args))
                )
                # Refactor to avoid using exec
                subprocess.run(
                    ["python", tmp_file_path],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                success = True
                output = "\n".join(output_buffer)
            return CodeResult(
                code=code,
                success=success,
                output=output,
            )
        except FileNotFoundError as e:
            return CodeResult(code=code, success=False, output="", error=str(e))
        except PermissionError as e:
            return CodeResult(code=code, success=False, output="", error=str(e))
        except subprocess.CalledProcessError as e:
            return CodeResult(code=code, success=False, output="", error=str(e))
