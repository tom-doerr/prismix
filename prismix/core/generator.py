import dspy
from .signatures import ProgramSpec, CodeImplementation, CodeReview

from dataclasses import dataclass
from typing import Optional


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
        return GenerationContext(
            requirements=spec.requirements,
            approach=spec.approach
        )

    def generate_implementation(self, context: GenerationContext) -> str:
        """Generate code implementation based on context"""
        implementation = self.code_generator(
            requirements=context.requirements,
            approach=context.approach,
            previous_attempt=context.previous_code or ""
        )
        return implementation.code

    
    def improve_implementation(self, code: str, error: str) -> str:
        """Review and improve failed implementation"""
        review = self.code_reviewer(code=code, error=error)
        return review.fixed_code
