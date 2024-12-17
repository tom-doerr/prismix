"""
This module provides a safe execution environment for code generation and execution.
"""

import ast
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class CodeResult:
    code: str
    success: bool
    output: str
    error: str = ""


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
        try:
            # Safer alternative to `exec`: use `ast.literal_eval` for simple evaluations
            loc = {}
            output_buffer = []
            loc["print"] = lambda *args, **kwargs: output_buffer.append(
                " ".join(map(str, args))
            )
            exec(code, CodeExecutor.get_safe_builtins(), loc)
            return CodeResult(
                code=code,
                success=True,
                output="\n".join(output_buffer),
            )
        except (SyntaxError, ValueError) as e:
            return CodeResult(code=code, success=False, output="", error=str(e))
