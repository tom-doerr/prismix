

import dspy
from pydantic import BaseModel


class Context(dspy.Signature):
    """Provides context for code editing."""
    retrieved_context = dspy.InputField(desc="Context from the retriever.")
    online_search = dspy.InputField(desc="Search results from online search.")

class CodeFile(BaseModel):
    filepath: str
    filecontent: str



class EditInstruction(dsyp.Signature):
    start_line = dspy.OutputField(desc="The line number where the edit should start.")
    end_line = dspy.OutputField(desc="The line number where the edit should end.")
    replacement_text = dspy.OutputField(desc="The text that should replace the lines from start_line to end_line.")
    filepath = dspy.OutputField(desc="The path to the file that should be edited.")

class CodeEdit(dspy.Signature):
    """Edits a code file based on an instruction."""
    instruction = dspy.InputField(desc="Instruction on how to modify the code.")
    code_files = dspy.InputField(desc="List of code files with their content.", format=list)
    context = dspy.InputField(desc="Context for the code edit.", format=Context)
    edit_instructions = 
    search_query = dspy.OutputField(desc="A search query to use for the next iteration, if needed.")
