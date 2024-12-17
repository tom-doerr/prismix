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
        import ast
        try:
            result = ast.literal_eval(code)
            return CodeResult(code=code, success=True, output=str(result))
        except Exception as e:
            return CodeResult(code=code, success=False, error=str(e))
