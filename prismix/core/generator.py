"""Handles the iterative code generation process."""

from dataclasses import dataclass
from typing import Optional

import dspy

from prismix.core.signatures import CodeImplementation, CodeReview, ProgramSpec


@dataclass
class GenerationContext:
    """Tracks the state of code generation process"""

    requirements: str
    approach: str
    previous_code: Optional[str] = None
    previous_error: Optional[str] = None


class CodeGenerator:
    """Handles the iterative code generation process"""

    def __init__(self, max_iterations: int = 3):
        self.spec_generator = dspy.ChainOfThought(ProgramSpec)
        self.code_generator = dspy.ChainOfThought(CodeImplementation)
        self.code_reviewer = dspy.ChainOfThought(CodeReview)
        self.max_iterations = max_iterations

    def generate_spec(self, command: str) -> GenerationContext:
        """Generate program specification from command"""
        spec = self.spec_generator(command=command)
        return GenerationContext(requirements=spec.requirements, approach=spec.approach)

    def generate_implementation(self, context: GenerationContext) -> str:
        """Generate code implementation based on context"""
        implementation = self.code_generator(
            requirements=context.requirements,
            approach=context.approach,
            previous_attempt=context.previous_code or "",
        )

        # Wrap the generated code in a main function and call it
        code = implementation.code

        # Extract the file path from the code comment
        lines = code.splitlines()
        file_path = None
        for line in lines:
            if line.strip().startswith("#"):
                file_path = line.strip()[1:].strip()
                break
        if file_path:
            code = f"""
if __name__ == "__main__":
    {code}
    main()
"""
        return code

    def improve_implementation(self, code: str, error: str) -> str:
        """Review and improve failed implementation"""
        review = self.code_reviewer(code=code, error=error)
        return review.fixed_code
