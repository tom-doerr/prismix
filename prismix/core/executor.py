"""
This module provides a safe execution environment for code generation and execution.
"""

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
            # Set up isolated execution environment
            local_vars = {}
            # Safely parse and execute the code
            import ast
            parsed_code = ast.parse(code)
            exec(compile(parsed_code, filename="<string>", mode="exec"), {"__builtins__": CodeExecutor.get_safe_builtins()}, local_vars)

            # Get the main function from the generated code
            main_func = None
            for _, obj in local_vars.items():
                if callable(obj) and obj.__name__ == "main":
                    main_func = obj
                    break

            if main_func is None:
                return CodeResult(
                    code=code,
                    success=False,
                    output="",
                    error="No callable 'main' function found in generated code",
                )

            # Test the function with a sample input
            try:
                result = main_func(5)  # Test with simple input
                return CodeResult(
                    code=code,
                    success=True,
                    output=f"Code executed successfully. Test main(5) = {result}",
                )
            except TypeError as e:
                return CodeResult(
                    code=code,
                    success=False,
                    output="",
                    error=f"Function execution failed: {str(e)}",
                )
        except (SyntaxError, NameError) as e:
            return CodeResult(code=code, success=False, output="", error=str(e))
