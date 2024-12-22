

from typing import Union

import dspy
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
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
    context = dspy.InputField(desc="Context for the code edit.")
    edit_instructions = dspy.OutputField(desc="A list of edit instructions.", base_signature=EditInstructions)
    search_query = dspy.OutputField(desc="A search query to use for the next iteration, if needed.")

    def __call__(self, **kwargs):
        output = self.forward(**kwargs)
        self.validate_edit_instructions(output.edit_instructions)
        return output

    def validate_edit_instructions(self, value):
        dspy.Assert(isinstance(value, list), "edit_instructions must be a list")
        for item in value:
            dspy.Assert(isinstance(item, dict), "Each edit instruction must be a dictionary")
            dspy.Assert("filepath" in item, "Each edit instruction must have a filepath")
            if "start_line" in item:
                dspy.Assert("end_line" in item, "LineNumberEditInstruction must have an end_line")
                dspy.Assert("replacement_text" in item, "LineNumberEditInstruction must have a replacement_text")
            elif "search_text" in item:
                dspy.Assert("replacement_text" in item, "SearchReplaceEditInstruction must have a replacement_text")
            else:
                raise AssertionError("Each edit instruction must be either a LineNumberEditInstruction or a SearchReplaceEditInstruction")

# Assuming you have a dspy.Model set up, e.g., using OpenAI
# If not, you'll need to set it up like this:
from typing import Union

import dspy

dspy.configure(lm=dspy.LM(model="openai/gpt-4o-mini"))


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
    instruction = "Add a comment to the hello function that says 'This is a hello function.'"

    # Call the predictor
    prediction = generate_answer(instruction=instruction, context=context)
    print("prediction:", prediction)

    # Activate assertions
    generate_answer_with_assertions = assert_transform_module(generate_answer, backtrack_handler)

    # Call the predictor with assertions
    prediction = generate_answer_with_assertions(instruction=instruction, context=context)

    # Print the generated answer
    print(f"Generated Answer: {prediction.edit_instructions}")


if __name__ == "__main__":
    run_code_edit_example()
