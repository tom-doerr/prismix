from typing import Tuple
import dspy
from .signatures import ProgramSpec, CodeImplementation, CodeReview, CodeSafetyCheck
from .executor import CodeResult, CodeExecutor

class IterativeProgrammer(dspy.Module):
    spec_generator: dspy.ChainOfThought
    code_generator: dspy.ChainOfThought
    code_reviewer: dspy.ChainOfThought
    safety_checker: dspy.ChainOfThought
    max_iterations: int

    def __init__(self) -> None:
        super().__init__()
        self.spec_generator = dspy.ChainOfThought(ProgramSpec)
        self.code_generator = dspy.ChainOfThought(CodeImplementation) 
        self.code_reviewer = dspy.ChainOfThought(CodeReview)
        self.safety_checker = dspy.TypedPredictor(CodeSafetyCheck)
        self.max_iterations = 3

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
                error=f"Safety check failed: {safety_msg}"
            )
        return CodeExecutor.execute(code)

    def forward(self, command: str) -> CodeResult:
        """Generate and execute code based on the given command"""
        print("1. Generating program specification...")
        spec = self.spec_generator(command=command)
        print(f"Requirements: {spec.requirements}")
        print(f"Approach: {spec.approach}\n")
        
        # Track previous attempts
        previous_attempt = ""  # Changed from dict to string
        
        # Iterative improvement loop
        for i in range(self.max_iterations):
            print(f"Iteration {i+1}/{self.max_iterations}")
            print("------------------------")
            print("2. Generating implementation...")
            implementation = self.code_generator(
                requirements=spec.requirements,
                approach=spec.approach,
                previous_attempt=previous_attempt
            )
            
            print("3. Running safety check...")
            is_safe, safety_msg = self.is_code_safe(implementation.code)
            print(f"Safety check result: {'PASSED' if is_safe else 'FAILED'}")
            print(f"Safety analysis: {safety_msg}\n")

            if not is_safe:
                print("Code generation failed due to safety concerns.")
                return CodeResult(
                    code=implementation.code,
                    success=False,
                    output="",
                    error=f"Safety check failed: {safety_msg}"
                )

            print("4. Testing implementation...")
            result = self.execute_code(implementation.code)
            
            if result.success:
                print("Success! Implementation passed testing.\n")
                return result
                
            print(f"Test failed: {result.error}")
            print("4. Reviewing and improving code...")
            review = self.code_reviewer(
                code=implementation.code,
                error=result.error
            )
            
            previous_attempt = {
                "code": implementation.code,
                "error": result.error
            }
            
            # Try improved version
            improved_result = self.execute_code(review.fixed_code)
            if improved_result.success:
                return improved_result
                
        # Return last attempt if max iterations reached
        return result


def setup_agent() -> IterativeProgrammer:
    """Configure and return an instance of IterativeProgrammer"""
    # Configure LM
    lm = dspy.LM(
        model="gpt-4o-mini",
        max_tokens=2000
    )
    dspy.configure(lm=lm)
    
    return IterativeProgrammer()
