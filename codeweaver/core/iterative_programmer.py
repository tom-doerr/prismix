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
        self.safety_checker = dspy.ChainOfThought(CodeSafetyCheck)
        self.max_iterations = 3

    def is_code_safe(self, code: str) -> tuple[bool, str]:
        """Check if code is safe to execute using LLM"""
        safety_check = self.safety_checker(code=code)
        return safety_check.is_safe, safety_check.safety_message

class CodeSafetyCheck(dspy.Signature):
    """Analyze code for potential security risks"""
    code = dspy.InputField()
    is_safe = dspy.OutputField(desc="Boolean indicating if code is safe")
    safety_message = dspy.OutputField(desc="Explanation of safety concerns if any")

    def execute_code(self, code: str) -> CodeResult:
        """Execute the generated code and return results"""
        # First check if code is safe
        is_safe, safety_msg = self.is_code_safe(code)
        if not is_safe:
            return CodeResult(
                code=code,
                success=False,
                output="",
                error=f"Safety check failed: {safety_msg}"
            )
            
        try:
            # Set up isolated execution environment with necessary builtins
            safe_builtins = {
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
            local_vars = {}
            exec(code, {"__builtins__": safe_builtins}, local_vars)
            
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
                # Try with a simple test case (5)
                result = main_func(5)
                return CodeResult(
                    code=code,
                    success=True, 
                    output=f"Code executed successfully. Test {main_func.__name__}(5) = {result}"
                )
            except TypeError as e:
                # If the function requires different arguments, return error
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
