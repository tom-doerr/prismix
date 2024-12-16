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
        # Basic check for potentially unsafe operations
        if "import os" in code or "os.system" in code:
            return False, "The code contains potentially unsafe operations (e.g., import os, os.system)."
        
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
        import sys
        from io import StringIO
        import os
        import subprocess
        
        try:
            # Extract the file path from the code comment
            lines = code.splitlines()
            file_path = None
            for line in lines:
                if line.strip().startswith("#"):
                    file_path = line.strip()[1:].strip()
                    break
            if not file_path:
                return CodeResult(
                    code=code,
                    success=False,
                    output="",
                    error="Could not determine file path from code comment."
                )
            
            # Read the original file content
            with open(file_path, 'r') as f:
                original_content = f.read()
            
            # Apply the changes to the original content
            file_editor = FileEditor()
            modified_content, _ = file_editor._apply_line_edits(original_content, code)
            
            # Write the modified content back to the original file
            with open(file_path, 'w') as f:
                f.write(modified_content)
            
            # Capture stdout and stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            redirected_output = sys.stdout = StringIO()
            redirected_error = sys.stderr = StringIO()

            # Execute the modified file
            subprocess.run([sys.executable, file_path], check=True)

            # Restore stdout and stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            output = redirected_output.getvalue()
            error = redirected_error.getvalue()

            return CodeResult(
                code=code,
                success=True,
                output=output,
                error=error
            )
        except subprocess.CalledProcessError as e:
            return CodeResult(
                code=code,
                success=False,
                output="",
                error=f"Function execution failed in {file_path}: {str(e.stderr)}"
            )
        except Exception as e:
            return CodeResult(
                code=code,
                success=False,
                output="",
                error=f"Function execution failed in {file_path}: {str(e)}"
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
            print("Code to be executed:")
            print("----------")
            print(code)
            print("----------")
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

        if not result.success:
            return result
        
        return result


def setup_agent() -> IterativeProgrammer:
    """Configure and return an instance of IterativeProgrammer"""
    # Configure LM
    lm = dspy.LM(model="gpt-4o-mini", max_tokens=2000)
    dspy.configure(lm=lm)

    return IterativeProgrammer()
