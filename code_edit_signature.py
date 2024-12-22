

import functools
from typing import Union

import dspy
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
from pydantic import BaseModel, Field


class InferenceModule(dspy.Module):
    """
    A base class for inference modules.
    """
    def __init__(self, signature):
        super().__init__()
        self.predictor = dspy.Predict(signature)

    def forward(self, instruction, context):
        """
        Performs the code edit inference.
        """
        prediction = self.predictor(instruction=instruction, context=context)
        print("prediction:", prediction)
        self.validate_edit_instructions(prediction.edit_instructions)
        return prediction

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
    context = dspy.InputField(desc="Context for the code edit.", type=str)
    edit_instructions = dspy.OutputField(desc="A list of edit instructions.", base_signature=EditInstructions)
    search_query = dspy.OutputField(desc="A search query to use for the next iteration, if needed.")

# Assuming you have a dspy.Model set up, e.g., using OpenAI
# If not, you'll need to set it up like this:
from typing import Union

import dspy

# dspy.configure(lm=dspy.LM(model="openai/gpt-4o-mini"))
dspy.configure(lm=dspy.LM(model="deepseek/deepseek-chat"))


context_sample = \
'''
from datetime import datetime

def hello():
    print('hello')

def print_datetime_nyc():
    print(datetime.now())

# This is a sample python file
# It contains a hello function
# that prints hello

if __name__ == "__main__":
    hello()
'''


instruction_context_pairs = [
    {
        "instruction": "Add a comment to the hello function that says 'This is a hello function.'",
        "context": context_sample
    },
    {
        "instruction": "Change the print statement in the hello function to say 'hello world'",
        "context": context_sample
    },
    {
        "instruction": "Add a new function called goodbye that prints 'goodbye'",
        "context": context_sample
    },
    {
        "instruction": "Rename the hello function to greet",
        "context": context_sample
    },
    {
        "instruction": "Remove the print statement from the hello function",
        "context": context_sample
    },
    {
        "instruction": "Add a parameter called name to the hello function",
         "context": context_sample
    },
    {
        "instruction": "Make the hello function return 'hello'",
        "context": context_sample
    },
    {
        "instruction": "Add a docstring to the hello function",
        "context": context_sample
    },
    {
        "instruction": "Add a type hint to the hello function",
        "context": context_sample
    },
    {
        "instruction": "Add a default value to the name parameter of the hello function",
        "context": context_sample
    },
    {
        "instruction": "Change the print statement in the print_datetime_nyc function to print the time in UTC",
        "context": context_sample
    },
    {
        "instruction": "Remove the print_datetime_nyc function",
        "context": context_sample
    },
    {
        "instruction": "Add a new function called print_date that prints the current date",
        "context": context_sample
    },
    {
        "instruction": "Add a type hint to the print_datetime_nyc function",
        "context": context_sample
    },
    {
        "instruction": "Add a docstring to the print_datetime_nyc function",
        "context": context_sample
    }
]





def run_code_edit_example():
    # Create a predictor using the CodeEdit signature
    generate_answer = assert_transform_module(
        InferenceModule(CodeEdit),
        functools.partial(backtrack_handler, max_backtracks=10),
    )

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

    for item in instruction_context_pairs:
        # Call the predictor
        prediction = generate_answer(instruction=item["instruction"], context=item["context"])
        print("prediction:", prediction)

        # Print the generated answer
        print(f"Generated Answer: {prediction.edit_instructions}")


def run_mipro_optimization():
    from dspy.datasets import Dataset
    from dspy.teleprompt import MIPROv2

    class EditDataset(Dataset):
        def __init__(self, data):
            super().__init__()
            self._train = list(data)

        def __len__(self):
            return len(self._train)

        def __getitem__(self, idx):
            return self._train[idx]

    trainset = EditDataset(instruction_context_pairs)

    teleprompter = MIPROv2(
        metric=lambda predictions, labels: 1.0,  # Dummy metric for now
        auto="light",
        num_candidates=7,
        init_temperature=0.5,
        max_bootstrapped_demos=3,
        max_labeled_demos=4,
        verbose=False,
    )

    # Create a simple module for optimization
    class SimpleEditModule(dspy.Module):
        def __init__(self, signature):
            super().__init__()
            self.predictor = dspy.Predict(signature)

        def forward(self, instruction, context):
            return self.predictor(instruction=instruction, context=context)

    # Optimize the module
    optimized_program = teleprompter.compile(
        SimpleEditModule(CodeEdit),
        trainset=trainset,
        num_trials=15,
        # num_trials=5,
        minibatch_size=25,
        minibatch_full_eval_steps=10,
        minibatch=True,
        # requires_permission_to_run=False,
        requires_permission_to_run=True,
    )

    # Save the optimized program
    optimized_program.save("mipro_optimized.json")

    print("MIPRO optimization complete.")


if __name__ == "__main__":
    run_mipro_optimization()
    run_code_edit_example()
