import dspy
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class CodeResult:
    code: str
    success: bool
    output: str
    error: str = ""

class ProgramSpec(dspy.Signature):
    """Analyze command and create program specification"""
    command = dspy.InputField()
    requirements = dspy.OutputField(desc="List of requirements and constraints")
    approach = dspy.OutputField(desc="High-level approach to implement the program")

class CodeImplementation(dspy.Signature):
    """Generate code implementation"""
    requirements = dspy.InputField() 
    approach = dspy.InputField()
    previous_attempt = dspy.InputField(desc="Previous code attempt and errors if any")
    code = dspy.OutputField(desc="Complete code implementation")

class CodeReview(dspy.Signature):
    """Review and improve code"""
    code = dspy.InputField()
    error = dspy.InputField()
    improvements = dspy.OutputField(desc="List of suggested improvements")
    fixed_code = dspy.OutputField(desc="Improved code implementation")

class IterativeProgrammer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.spec_generator = dspy.ChainOfThought(ProgramSpec)
        self.code_generator = dspy.ChainOfThought(CodeImplementation) 
        self.code_reviewer = dspy.ChainOfThought(CodeReview)
        self.max_iterations = 3

    def execute_code(self, code: str) -> CodeResult:
        """Execute the generated code and return results"""
        try:
            # Set up isolated execution environment
            local_vars = {}
            exec(code, {}, local_vars)
            # Test basic functionality
            test_input = 5
            result = local_vars['factorial'](test_input)
            return CodeResult(
                code=code,
                success=True, 
                output=f"Code executed successfully. Test factorial({test_input}) = {result}"
            )
        except Exception as e:
            return CodeResult(
                code=code,
                success=False,
                output="",
                error=str(e)
            )

    def forward(self, command: str) -> CodeResult:
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
            
            print("3. Testing implementation...")
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

def setup_agent():
    # Configure LM
    lm = dspy.LM(
        model="gpt-4o-mini",
        max_tokens=2000
    )
    dspy.configure(lm=lm)
    
    return IterativeProgrammer()
