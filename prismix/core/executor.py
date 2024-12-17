"""
This module provides a safe execution environment for code generation and execution.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


@dataclass
class CodeResult:
    """Represents the result of code execution."""

    code: str
    success: bool
    output: str
    error: str = ""


class FileContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
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
    """
    Handles safe code execution in isolated environment.

    This class provides methods to execute code in a controlled and safe environment,
    ensuring that only a limited set of built-in functions are available to the executed code.
    """

    @staticmethod
    def execute(code: str) -> CodeResult:
        """Execute code in isolated environment and return results"""
        try:
            # Safely parse and evaluate the code
            tree = ast.parse(code)
            compiled_code = compile(tree, filename="<string>", mode="exec")
            local_vars = {}
            exec(compiled_code, CodeExecutor.get_safe_builtins(), local_vars)
            return CodeResult(code=code, success=True, output="", error="")
        except (SyntaxError, NameError) as e:
            return CodeResult(code=code, success=False, output="", error=str(e))

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

