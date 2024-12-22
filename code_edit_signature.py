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
        # self.predictor = dspy.Predict(signature)
        self.predictor = dspy.ChainOfThought(signature)

    def forward(self, instruction, context):
        """
        Performs the code edit inference.
        """
        prediction = self.predictor(instruction=instruction, context=context)
        if False:
            print("prediction:", prediction)
            try:
                import json

                edit_instructions = json.loads(prediction.edit_instructions)
                validated_edit_instructions = EditInstructions(
                    edit_instructions=edit_instructions
                )
                self.validate_edit_instructions(
                    validated_edit_instructions.edit_instructions,
                    prediction,
                    target_module=self,
                )
                prediction.edit_instructions = (
                    validated_edit_instructions.edit_instructions
                )
            except Exception as e:
                print(f"Error parsing edit_instructions: {e}")
                dspy.Suggest(
                    False, f"Error parsing edit_instructions: {e}", target_module=self
                )

        return prediction


def validate_edit_instructions(value, prediction, target_module):
    dspy.Suggest(
        isinstance(value, list),
        "edit_instructions must be a list",
        target_module=target_module,
    )
    for item in value:
        dspy.Suggest(
            isinstance(item, dict),
            "Each edit instruction must be a dictionary",
            target_module=target_module,
        )
        dspy.Suggest(
            "filepath" in item,
            "Each edit instruction must have a filepath",
            target_module=target_module,
        )
        if "start_line" in item:
            dspy.Suggest(
                "end_line" in item,
                "LineNumberEditInstruction must have an end_line",
                target_module=target_module,
            )
            dspy.Suggest(
                "replacement_text" in item,
                "LineNumberEditInstruction must have a replacement_text",
                target_module=target_module,
            )
        elif "search_text" in item:
            dspy.Suggest(
                "replacement_text" in item,
                "SearchReplaceEditInstruction must have a replacement_text",
                target_module=target_module,
            )


class CodeFile(BaseModel):
    filepath: str
    filecontent: str


class LineNumberEditInstruction(BaseModel):
    start_line: int = Field(..., desc="The line number where the edit should start.")
    end_line: int = Field(..., desc="The line number where the edit should end.")
    replacement_text: str = Field(
        ..., desc="The text that should replace the lines from start_line to end_line."
    )
    filepath: str = Field(..., desc="The path to the file that should be edited.")


class SearchReplaceEditInstruction(BaseModel):
    filepath: str = Field(..., desc="The path to the file that should be edited.")
    search_text: str = Field(..., desc="The text to search for.")
    replacement_text: str = Field(..., desc="The text to replace the found text with.")


class EditInstructions(BaseModel):
    edit_instructions: list[
        Union[LineNumberEditInstruction, SearchReplaceEditInstruction]
    ] = Field(..., desc="A list of edit instructions.")


class CodeEdit(dspy.Signature):
    """Edits a code file based on an instruction."""

    instruction = dspy.InputField(desc="Instruction on how to modify the code.")
    context = dspy.InputField(desc="Context for the code edit.", type=str)
    edit_instructions = dspy.OutputField(
        desc="A list of edit instructions.", base_signature=EditInstructions
    )
    search_query = dspy.OutputField(
        desc="A search query to use for the next iteration, if needed."
    )


# Assuming you have a dspy.Model set up, e.g., using OpenAI
# If not, you'll need to set it up like this:
from typing import Union

import dspy

# dspy.configure(lm=dspy.LM(model="openai/gpt-4o-mini"))
lm = dspy.LM(model="deepseek/deepseek-chat", max_tokens=200, cache=False)
dspy.configure(lm=lm)


context_sample = """
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
"""


instruction_context_pairs = [
    {
        "instruction": "Add a comment to the hello function that says 'This is a hello function.'",
        "context": context_sample,
    },
    {
        "instruction": "Change the print statement in the hello function to say 'hello world'",
        "context": context_sample,
    },
    {
        "instruction": "Add a new function called goodbye that prints 'goodbye'",
        "context": context_sample,
    },
    {"instruction": "Rename the hello function to greet", "context": context_sample},
    {
        "instruction": "Remove the print statement from the hello function",
        "context": context_sample,
    },
    {
        "instruction": "Add a parameter called name to the hello function",
        "context": context_sample,
    },
    {
        "instruction": "Make the hello function return 'hello'",
        "context": context_sample,
    },
    {"instruction": "Add a docstring to the hello function", "context": context_sample},
    {"instruction": "Add a type hint to the hello function", "context": context_sample},
    {
        "instruction": "Add a default value to the name parameter of the hello function",
        "context": context_sample,
    },
    {
        "instruction": "Change the print statement in the print_datetime_nyc function to print the time in UTC",
        "context": context_sample,
    },
    {
        "instruction": "Remove the print_datetime_nyc function",
        "context": context_sample,
    },
    {
        "instruction": "Add a new function called print_date that prints the current date",
        "context": context_sample,
    },
    {
        "instruction": "Add a type hint to the print_datetime_nyc function",
        "context": context_sample,
    },
    {
        "instruction": "Add a docstring to the print_datetime_nyc function",
        "context": context_sample,
    },
]


generate_answer = assert_transform_module(
    InferenceModule(CodeEdit),
    functools.partial(backtrack_handler, max_backtracks=30),
)


def run_code_edit_example():
    # Create a predictor using the CodeEdit signature

    # Example usage
    code_files = [
        {"filepath": "example.py", "filecontent": "def hello():\n    print('hello')\n"}
    ]
    context = {
        "retrieved_context": "This is an example python file.",
        "online_search": "No relevant search results.",
    }

    for item in instruction_context_pairs:
        # Call the predictor
        prediction = generate_answer(
            instruction=item["instruction"], context=item["context"]
        )
        print("prediction:", prediction)

        # Print the generated answer
        print(f"Generated Answer: {prediction.edit_instructions}")


class Scorer(BaseModel):
    score: float = Field(
        ..., ge=0, le=10, desc="The score of the edit, value between 0 and 10."
    )


# new signature for rating the output
class CodeEditRating(dspy.Signature):
    """Rates how close the edit_instruction conforms to the edit_format."""

    # edit_instructions = dspy.InputField(
        # desc="A list of edit instructions.", base_signature=EditInstructions
    # )
    # edit_instructions = dspy.InputField(
        # desc="A list of edit instructions.", type=str
    # )
    edit_instructions = dspy.InputField(
        desc="A list of edit instructions."
    )
    search_query = dspy.InputField(
        desc="A search query to use for the next iteration, if needed."
    )
    edit_format = dspy.InputField(desc="The format of the edit instructions.", type=str)
    # rating = dspy.OutputField(desc="A rating of the code edit on a scale from 1 to 10. Reply with just the int and nothing else.", type=int)
    rating = dspy.OutputField(
        base_signature=Scorer,
        type=float,
        desc="A rating of the code edit on a scale from 1 to 10.",
    )


# edit_rater = dspy.ChainOfThought(CodeEditRating)
edit_rater = dspy.TypedChainOfThought(CodeEditRating)


# def custom_metric(gold, pred, trace=None):
def custom_metric(reasoning, edit_instructions, search_query=""):
    print("custom_metric called")
    print("edit_instructions:", edit_instructions)
    # try to parse the edit instructions
    score = 0.0
    edit_instructions_format = EditInstructions.model_json_schema()
    print("edit_instructions_format:", edit_instructions_format)
    edit_rater_score = edit_rater(
        edit_instructions=str(edit_instructions),
        search_query=str(search_query),
        edit_format=edit_instructions_format,
    )
    print("edit_rater_score:", edit_rater_score)
    score += float(edit_rater_score.rating)
    try:
        import json

        pred_edit_instructions = json.loads(edit_instructions.edit_instructions)
        score += 20.0
        return score
    except Exception as e:
        print(f"Error parsing edit_instructions: {e}")
        return score


def run_mipro_optimization():
    from dspy.teleprompt import MIPROv2

    edit_dataset = [
        dspy.Example(
            instruction=item["instruction"], context=item["context"]
        ).with_inputs("instruction", "context")
        for item in instruction_context_pairs
    ]
    # trainset = Dataset(edit_dataset)
    trainset = edit_dataset

    teleprompter = MIPROv2(
        # metric=lambda predictions, labels: 1.0,  # Dummy metric for now
        metric=custom_metric,
        # auto="light",
        auto="heavy",
        num_candidates=7,
        init_temperature=0.5,
        max_bootstrapped_demos=3,
        max_labeled_demos=4,
        verbose=False,
        # num_threads=5,
        num_threads=10,
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
        # SimpleEditModule(CodeEdit),
        # InferenceModule(CodeEdit),
        generate_answer,
        trainset=trainset,
        num_trials=15,
        minibatch_size=25,
        minibatch_full_eval_steps=100,
        minibatch=True,
        requires_permission_to_run=False,
        # requires_permission_to_run=True,
    )

    # Save the optimized program
    optimized_program.save("mipro_optimized.json")

    print("MIPRO optimization complete.")


if __name__ == "__main__":
    run_code_edit_example()
    run_mipro_optimization()
