

from typing import Union

import dspy
from pydantic import BaseModel, Field


class Context(dspy.Signature):
    """Provides context for code editing."""
    retrieved_context = dspy.InputField(desc="Context from the retriever.")
    online_search = dspy.InputField(desc="Search results from online search.")

class CodeFile(BaseModel):
    filepath: str
    filecontent: str

class LineNumberEditInstruction(BaseModel):
    start_line: int = Field(..., desc="The line number where the edit should start.")
    end_line: int = Field(..., desc="The line number where the edit should end.")
    replacement_text: str = Field(..., desc="The text that should replace the lines from start_line to end_line.")
    filepath: str = Field(..., desc="The path to the file that should be edited.")



class SearchReplaceEditInstruction(BaseModel):
    filepath: str = Field(..., desc="The path to the file that should be edited.")
    search_text: str = Field(..., desc="The text to search for.")
    replacement_text: str = Field(..., desc="The text to replace the found text with.")

class EditInstructions(BaseModel):
    edit_instructions: list[Union[LineNumberEditInstruction, SearchReplaceEditInstruction]] = Field(..., desc="A list of edit instructions.")

class CodeEdit(dspy.Signature):
    """Edits a code file based on an instruction."""
    instruction = dspy.InputField(desc="Instruction on how to modify the code.")
    code_files = dspy.InputField(desc="List of code files with their content.", format=list)
    context = dspy.InputField(desc="Context for the code edit.", format=Context)
    # edit_instructions: list[Union[LineNumberEditInstruction, SearchReplaceEditInstruction]] = Field(..., desc="A list of edit instructions.")
    edit_instructions = dspy.OutputField(desc="A list of edit instructions.", format=EditInstructions)
    search_query = dspy.OutputField(desc="A search query to use for the next iteration, if needed.")

# class CodeEditPydantic(BaseModel):
    # instruction: Union[LineNumberEditInstruction, SearchReplaceEditInstruction]
    # code_files: list[CodeFile]
    # context: Context
    # search_query: str = Field(None, desc="A search query to use for the next iteration, if needed.")
    # edit_instructions: list[Union[LineNumberEditInstruction, SearchReplaceEditInstruction]] = Field(None, desc="A list of edit instructions.")


# CodeEdit = create_signature_class_from_model(CodeEditPydantic)

from typing import Union

import dspy

# Assuming you have a dspy.Model set up, e.g., using OpenAI
# If not, you'll need to set it up like this:
import os
os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"
dspy.configure(lm=dspy.OpenAI(model="gpt-4o-mini"))


def run_code_edit_example():
    # Create a predictor using the CodeEdit signature
    generate_answer = dspy.Predict(CodeEdit)

    # Example usage
    code_files = [
        {
            "filepath": "example.py",
            "filecontent": "def hello():\n    print('hello')\n"
        }
    ]
    context = {
        "retrieved_context": "This is an example python file.",
        "online_search": "No relevant search results."
    }
    instruction = "Add a comment to the hello function that says 'This is a hello function'."

    # Call the predictor
    prediction = generate_answer(instruction=instruction, code_files=code_files, context=context)

    # Print the generated answer
    print(f"Generated Answer: {prediction.edit_instructions}")


if __name__ == "__main__":
    run_code_edit_example()
