import dspy

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

class CodeSafetyCheck(dspy.Signature):
    """Analyze code for potential security risks"""
    code: str = dspy.InputField(desc="Code to analyze")
    is_safe: bool = dspy.OutputField(desc="Boolean indicating if code is safe")
    safety_message: str = dspy.OutputField(desc="Explanation of safety concerns if any")

class FileEdit(dspy.Signature):
    """
    Signature for editing code in a file.
    """
    context = dspy.InputField(desc="The context for the edit operation.")
    instruction = dspy.InputField(desc="The instruction for the edit operation.")
    inputs = dspy.InputField(desc="Additional inputs for the edit operation.")
    filename = dspy.OutputField(desc="The filename where the edit will be applied.")
    search = dspy.OutputField(desc="The search pattern to be replaced.")
    replace = dspy.OutputField(desc="The replacement code.")
