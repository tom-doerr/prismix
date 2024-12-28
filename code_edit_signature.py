import functools
import json
from typing import Union, List

import dspy
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
from dspy.teleprompt import BootstrapFewShot
from prismix.core.models import (
    Context,
    CodeFile,
    SearchReplaceEditInstruction,
    EditInstructions,
    Scorer
)
from pydantic import BaseModel, Field, ValidationError


class InferenceModule(dspy.Module):
    """Handles code edit inference using search/replace instructions."""
    
    def __init__(self, signature):
        super().__init__()
        self.predictor = dspy.ChainOfThought(signature)
        self.signature = signature

    def _validate_edit_instructions(self, instructions: str) -> EditInstructions:
        """Validate and parse edit instructions.
        
        Args:
            instructions: JSON string of edit instructions
            
        Returns:
            EditInstructions: Validated edit instructions
            
        Raises:
            ValueError: If instructions are invalid
        """
        try:
            parsed = json.loads(instructions)
            return EditInstructions(edit_instructions=[
                SearchReplaceEditInstruction(**instr) 
                for instr in parsed
            ])
        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(
                f"Invalid edit instructions: {e}. Must match format: {EditInstructions.model_json_schema()}"
            )

    def forward(self, instruction: str, context: str) -> dspy.Prediction:
        """Generate and validate code edit instructions.
        
        Args:
            instruction: The edit instruction to process
            context: Context for the code edit
            
        Returns:
            dspy.Prediction: Contains reasoning and validated edit instructions
            
        Raises:
            dspy.DSPyAssertionError: If instructions fail validation
        """
        prediction = self.predictor(instruction=instruction, context=context)
        
        try:
            validated_instructions = self._validate_edit_instructions(prediction.edit_instructions)
            return dspy.Prediction(
                reasoning=prediction.reasoning,
                edit_instructions=validated_instructions.json()
            )
        except ValueError as e:
            dspy.Assert(
                False,
                f"Error parsing edit_instructions: {e}"
            )

class SearchReplaceEditInstruction2(BaseModel):
    filepath: str = Field(..., desc="The path to the file that should be edited.")
    search_text: str = Field(..., desc="The text to search for.")
    replacement_text: str = Field(..., desc="The text to replace the found text with.")


class CodeEdit(dspy.Signature):
    """Edits a code file based on an instruction using search/replace.
    Returns a JSON array of edit instructions with filepath, search_text, and replacement_text."""

    instruction = dspy.InputField(
        desc="Specific instruction on how to modify the code. Be precise about what to change."
    )
    context = dspy.InputField(
        desc="Context for the code edit including relevant code snippets.", 
        type=str
    )
    edit_instructions = dspy.OutputField(
        desc="JSON array of edit instructions. Each instruction must have: "
             "filepath (string), search_text (string), replacement_text (string). "
             "Example: [{'filepath': 'test.py', 'search_text': 'print()', 'replacement_text': 'print(time_in_china)'}]",
        type=str
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


def run_code_edit_example():
    # Create a predictor using the CodeEdit signature
    module = InferenceModule(CodeEdit)
    generate_answer = assert_transform_module(
        module,
        functools.partial(backtrack_handler, max_backtracks=100),  # Increased from 30 to 100
    )

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


edit_rater = dspy.ChainOfThought(CodeEditRating)
# edit_rater = dspy.TypedChainOfThought(CodeEditRating)


# def custom_metric(gold, pred, trace=None):
def custom_metric(reasoning: str, edit_instructions: str, search_query: str = "") -> float:
    """Evaluate the quality of generated edit instructions.
    
    Args:
        reasoning: The reasoning behind the edits
        edit_instructions: The generated edit instructions
        search_query: Optional search query for context
        
    Returns:
        float: Score between 0 and 10
        
    Raises:
        ValueError: If instructions cannot be parsed
    """
    try:
        # Validate instructions first
        instructions = json.loads(edit_instructions)
        EditInstructions(edit_instructions=instructions)
        
        # Get rating from LLM
        rating = edit_rater(
            edit_instructions=edit_instructions,
            search_query=search_query,
            edit_format=str(EditInstructions.model_json_schema())
        ).rating
        
        # Add bonus for valid JSON
        return float(rating) + 2.0
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"Invalid edit instructions: {e}")


def generate_answer_with_assertions(instruction, context):

    module = InferenceModule(CodeEdit)
    prediction = module.forward(instruction=instruction, context=context)
    edit_instructions_format = str(EditInstructions.model_json_schema())
    try:

        import json

        edit_instructions = json.loads(prediction.edit_instructions)
        validated_edit_instructions = EditInstructions(edit_instructions=edit_instructions)
        prediction.edit_instructions = validated_edit_instructions.edit_instructions
    except Exception as e:
        dspy.Assert(False,
        f"Error parsing edit_instructions: {e}. edit_instructions must be of the following format: {edit_instructions_format}")


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
    module = InferenceModule(CodeEdit)
    optimized_program = teleprompter.compile(
        assert_transform_module(
            module,
            functools.partial(backtrack_handler, max_backtracks=10),  # Increased from 3 to 10
        ),
        trainset=trainset,
        num_trials=15,
        minibatch_size=25,
        minibatch_full_eval_steps=100,
        minibatch=True,
        requires_permission_to_run=False,
        # requires_permission_to_run=True,
    )

    # Save the optimized program to a single JSON file
    # with open("mipro_optimized.json", "w") as f:
        # json.dump(optimized_program.to_json(), f)
    optimized_program.save("mipro_optimized.json")

    print("MIPRO optimization complete.")



def run_bootstrap_fewshot_optimization() -> dspy.Module:
    """Optimize the code edit module using BootstrapFewShot.
    
    Returns:
        dspy.Module: Optimized program
    """
    # Create training dataset
    trainset = [
        dspy.Example(
            instruction=item["instruction"], 
            context=item["context"]
        ).with_inputs("instruction", "context")
        for item in instruction_context_pairs
    ]

    # Configure optimizer
    teleprompter = BootstrapFewShot(
        metric=custom_metric,
        max_bootstrapped_demos=8,
        max_labeled_demos=4,
        max_rounds=10,
        num_threads=10
    )

    # Create and optimize module
    module = InferenceModule(CodeEdit)
    optimized_program = teleprompter.compile(
        assert_transform_module(
            module,
            functools.partial(backtrack_handler, max_backtracks=10)
        ),
        trainset=trainset,
    )

    # Save optimized program
    optimized_program.save("bootstrap_optimized.json")
    print("BootstrapFewShot optimization complete.")
    return optimized_program


def load_optimized_program(filename: str):
    """Loads an optimized program from a JSON file."""
    # with open(filename, "r") as f:
        # program_json = json.load(f)

    # Create an instance of InferenceModule with the loaded signature
    # signature = CodeEdit(**program_json["signature"])
    # module = InferenceModule(signature)

    # Load the module
    # module = dspy.Module.from_json(program_json)
    module = InferenceModule(CodeEdit)

    # Load the state of the module
    # module.load_state(program_json)
    module.load(filename)

    return module

    # Load the state of the module
    # module.load_state(program_json)

    # return module


def run_inference(program, instruction: str, context: str):
    """Runs inference using the loaded program."""
    prediction = program(instruction=instruction, context=context)
    return prediction


def run_code_edit_example():
    # Load the optimized program
    optimized_program = load_optimized_program("bootstrap_optimized.json")
    # optimized_program = load_optimized_program("mipro_optimized.json")

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
        prediction = run_inference(
            optimized_program, instruction=item["instruction"], context=item["context"]
        )
        print("prediction:", prediction)

        # Print the generated answer
        print(f"Generated Answer: {prediction.edit_instructions}")


if __name__ == "__main__":
    # run_bootstrap_fewshot_optimization()
    # run_code_edit_example()
    run_mipro_optimization()
