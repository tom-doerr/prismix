import dspy
from typing import List
from pydantic import BaseModel

class CodeFile(BaseModel):
    filepath: str
    filecontent: str

class CodeEdit(dspy.Signature):
    """Edits a code file based on an instruction."""
    instruction = dspy.InputField(desc="Instruction on how to modify the code.")
    code_files = dspy.InputField(desc="List of code files with their content.", format=List[CodeFile])
    start_line = dspy.OutputField(desc="The line number where the edit should start.")
    end_line = dspy.OutputField(desc="The line number where the edit should end.")
    replacement_text = dspy.OutputField(desc="The text that should replace the lines from start_line to end_line.")
