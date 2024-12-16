from typing import Tuple, Union
import dspy
from .signatures import CodeSafetyCheck
from .executor import CodeResult, CodeExecutor
from .generator import CodeGenerator, GenerationContext
from .file_operations import FileEditor, FileContext


class IterativeProgrammer(dspy.Module):
    """Main module that coordinates code generation, safety checks and execution"""

    def __init__(self, max_iterations: int = 3) -> None:
        super().__init__()
        self.generator = CodeGenerator(max_iterations)
        self.safety_checker = dspy.TypedPredictor(CodeSafetyCheck)
        self.file_editor = FileEditor()
        self.max_iterations = max_iterations

    def is_code_safe(self, code: str) -> Tuple[bool, str]:
        """Check if code is safe to execute using LLM"""
        safety_check = self.safety_checker(code=code)
        # TypedPredictor ensures is_safe is already a boolean
        return safety_check.is_safe, safety_check.safety_message

    def execute_code(self, code: str) -> CodeResult:
        """Execute the generated code in a safe environment and return results"""
        is_safe, safety_msg = self.is_code_safe(code)
        print("is_safe:", is_safe)
        if not is_safe:
            return CodeResult(
                code=code,
                success=False,
                output="",
                error=f"Safety check failed: {safety_msg}",
            )
        # Ensure the function is called without arguments
        try:
            # Execute the code in the global scope
            exec(code, globals())
            return CodeResult(
                code=code,
                success=True,
                output="",
                error=""
            )
        except Exception as e:
            return CodeResult(
                code=code,
                success=False,
                output="",
                error=f"Function execution failed: {str(e)}"
            )

    def forward(self, command: str) -> Union[CodeResult, FileContext]:
        """Generate and execute code or edit files based on the command"""
        # Check if this is a file editing command
        if command.startswith("edit"):
            command = command.strip()
            if command == "edit":
                return FileContext(
                    filepath="",
                    content="",
                    changes=[],
                    error="Invalid edit command. Use: edit <filepath> <instruction>",
                )

            # Extract filepath and instruction
            parts = command[4:].strip().split(" ", 1)
            if not parts or len(parts) != 2:
                return FileContext(
                    filepath="",
                    content="",
                    changes=[],
                    error="Invalid edit command. Use: edit <filepath> <instruction>",
                )
            filepath, instruction = parts
            print(f"Editing file: {filepath}")
            print(f"Instruction: {instruction}\n")
            file_context = self.file_editor.edit_file(filepath, instruction)
            return file_context

        # Regular code generation flow
        print("1. Generating program specification...")
        context = self.generator.generate_spec(command)
        print(f"Requirements: {context.requirements}")
        print(f"Approach: {context.approach}\n")

        # Iterative improvement loop
        for i in range(self.max_iterations):
            print(f"Iteration {i+1}/{self.max_iterations}")
            print("------------------------")

            # Generate implementation
            print("2. Generating implementation...")
            code = self.generator.generate_implementation(context)

            # Safety check
            print("3. Running safety check...")
            is_safe, safety_msg = self.is_code_safe(code)
            print(f"Safety check result: {'PASSED' if is_safe else 'FAILED'}")
            print(f"Safety analysis: {safety_msg}\n")

            if not is_safe:
                print("Code generation failed due to safety concerns.")
                return CodeResult(
                    code=code,
                    success=False,
                    output="",
                    error=f"Safety check failed: {safety_msg}",
                )

            # Test implementation
            print("4. Testing implementation...")
            result = self.execute_code(code)

            if result.success:
                print("Success! Implementation passed testing.\n")
                return result

            # Try to improve failed implementation
            print(f"Test failed: {result.error}")
            print("5. Reviewing and improving code...")

            improved_code = self.generator.improve_implementation(code, result.error)
            context.previous_code = code
            context.previous_error = result.error

            improved_result = self.execute_code(improved_code)
            if improved_result.success:
                return improved_result

        return result


def setup_agent() -> IterativeProgrammer:
    """Configure and return an instance of IterativeProgrammer"""
    # Configure LM
    lm = dspy.LM(model="gpt-4o-mini", max_tokens=2000)
    dspy.configure(lm=lm)

    return IterativeProgrammer()
