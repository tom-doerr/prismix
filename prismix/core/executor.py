from dataclasses import dataclass
from typing import Dict, Any, Callable

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
            "TypeError": TypeError
        }

    @staticmethod
    def execute(code: str) -> CodeResult:
        """Execute code in isolated environment and return results"""
        try:
            # Set up isolated execution environment
            local_vars = {}
            exec(code, {"__builtins__": CodeExecutor.get_safe_builtins()}, local_vars)
            
            # Get the main function from the generated code
            main_func = None
            for name, obj in local_vars.items():
                if callable(obj):
                    main_func = obj
                    break
            
            if main_func is None:
                return CodeResult(
                    code=code,
                    success=False,
                    output="",
                    error="No callable function found in generated code"
                )
            
            # Test the function with a sample input
            try:
                result = main_func(5)  # Test with simple input
                return CodeResult(
                    code=code,
                    success=True, 
                    output=f"Code executed successfully. Test {main_func.__name__}(5) = {result}"
                )
            except TypeError as e:
                return CodeResult(
                    code=code,
                    success=False,
                    output="",
                    error=f"Function execution failed: {str(e)}"
                )
        except Exception as e:
            return CodeResult(
                code=code,
                success=False,
                output="",
                error=str(e)
            )
