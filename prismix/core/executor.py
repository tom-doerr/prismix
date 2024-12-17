"""
This module provides a safe execution environment for code generation and execution.
"""

import ast
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class CodeResult:
    """Result of code generation and execution"""

    code: str
    success: bool
    output: str
    error: str = ""


class CodeExecutor:
    """Handles safe code execution in isolated environment"""

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
            local_vars = {}
            # Use a safer alternative, such as `ast.literal_eval` for simple evaluations
            result = ast.literal_eval(code)
            main_func = local_vars.get("main")
            if main_func:
                result = main_func(5)
                return CodeResult(
                    code=code,
                    success=True,
                    output=f"Code executed successfully. Test main(5) = {result}",
                )
            else:
                return CodeResult(
                    code=code,
                    success=False,
                    output="",
                    error="No callable 'main' function found in generated code",
                )
        except Exception as e:
            return CodeResult(code=code, success=False, output="", error=str(e))
