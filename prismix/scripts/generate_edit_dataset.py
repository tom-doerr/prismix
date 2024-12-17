"""
Script to generate an edit dataset for training purposes.
"""

import json
import random
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import dspy

from prismix.core.file_operations import FileEditor
from prismix.core.metrics import calculate_levenshtein_similarity


class GenerateScript(dspy.Signature):
    """Generate a Python script based on a theme"""

    theme = dspy.InputField(
        desc="Theme or topic for the script (e.g., 'file processing', 'data structures')"
    )
    script = dspy.OutputField(desc="Complete Python script following best practices")


class GenerateEditInstruction(dspy.Signature):
    """Generate an edit instruction for a script"""

    script = dspy.InputField(desc="Original Python script")
    instruction = dspy.OutputField(
        desc="Natural language instruction for editing the script (e.g., 'add error handling', 'improve documentation')"
    )


class GenerateHindsightEdit(dspy.Signature):
    """Generate precise edit command that describes transformation between two scripts"""

    original = dspy.InputField(desc="Original script content")
    edited = dspy.InputField(desc="Edited script content")
    edit_command = dspy.OutputField(
        desc="Precise edit command in format: 'edit <description of changes>' that would transform original into edited version"
    )


@dataclass
class EditDataPoint:
    """Represents a single edit transformation example."""

    original_script: str
    edited_script: str
    edit_instruction: str
    hindsight_command: str


class EditDatasetGenerator(dspy.Module):
    """
    Module to generate edit dataset examples.
    This class generates datasets for training purposes by creating original and edited scripts,
    along with corresponding edit instructions and hindsight commands.
    """

    """
    Module to generate edit dataset examples.
    This class generates datasets for training purposes by creating original and edited scripts,
    along with corresponding edit instructions and hindsight commands.
    """

    def __init__(self):
        super().__init__()

        class GenerateDatasetSignature(dspy.Signature):
            num_examples = dspy.InputField(desc="Number of examples to generate")
            output_file = dspy.InputField(desc="Path to the output JSON file")
            dataset = dspy.OutputField(desc="Generated dataset containing examples")

        self.signature = GenerateDatasetSignature()
        self.script_generator = dspy.ChainOfThought(GenerateScript)
        self.edit_generator = dspy.ChainOfThought(GenerateEditInstruction)
        self.hindsight_generator = dspy.ChainOfThought(GenerateHindsightEdit)

        # Themes for script generation
        self.themes = [
            "file processing",
            "data structures implementation",
            "API client",
            "command line tool",
            "database operations",
            "text processing",
            "mathematical calculations",
            "system monitoring",
            "data validation",
            "configuration management",
        ]

    def generate_datapoint(self) -> EditDataPoint:
        """Generate a single edit transformation example"""
        print("\nGenerating new datapoint...")

        # 1. Generate original script
        theme = random.choice(self.themes)
        print(f"Selected theme: {theme}")

        result = self.script_generator(theme=theme)
        print("Generated original script length:", len(result.script))

        # Clean and validate the generated script
        original_script = self._clean_script(result.script)

        # 2. Generate edit instruction
        print("\nGenerating edit instruction...")
        edit_instruction = self._generate_edit_instruction(original_script)

        # 3. Apply edit instruction using FileEditor
        print("\nApplying edits...")
        editor_script = self._apply_edits(original_script, edit_instruction)

        # 4. Generate alternative version
        print("\nGenerating alternative version...")
        generated_script = self._generate_alternative_version(theme, edit_instruction)

        # 5. Compare versions and choose the best one
        edited_script = self._choose_best_version(
            original_script, editor_script, generated_script
        )

        # 6. Generate hindsight edit command
        hindsight_command = self._generate_hindsight_command(
            original_script, edited_script
        )

        return EditDataPoint(
            original_script=original_script,
            edited_script=edited_script,
            edit_instruction=edit_instruction,
            hindsight_command=hindsight_command,
        )

    def _clean_script(self, script: str) -> str:
        """Clean and validate the generated script."""
        script = script.strip()
        if "```" in script:
            # Extract code from markdown block
            code_match = re.search(r"```python\n(.*?)\n```", script, re.DOTALL)
            if code_match:
                script = code_match.group(1).strip()
            else:
                # Try without language specification
                code_match = re.search(r"```\n(.*?)\n```", script, re.DOTALL)
                if code_match:
                    script = code_match.group(1).strip()
        print("Cleaned script length:", len(script))
        print("Script preview:", script[:100] + "..." if len(script) > 100 else script)
        return script

    def _generate_edit_instruction(self, script: str) -> str:
        """Generate an edit instruction for the script."""
        edit_result = self.edit_generator(script=script)
        edit_instruction = edit_result.instruction
        print("Edit instruction:", edit_instruction)
        return edit_instruction

    def _apply_edits(
        self, original_script: str, edit_instruction: str
    ) -> Optional[str]:
        """Apply the edit instruction using FileEditor."""
        editor = FileEditor()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            temp_file = f.name
            f.write(original_script)

        file_context = editor.edit_file(temp_file, edit_instruction)
        if file_context.error:
            print("Editor error:", file_context.error)
            return None
        print("Editor changes:", len(file_context.changes), "modifications")
        for change in file_context.changes:
            print(f"- {change}")
        return file_context.content

    def _generate_alternative_version(self, theme: str, edit_instruction: str) -> str:
        """Generate an alternative version of the script."""
        modified_result = self.script_generator(
            theme=theme, instruction=edit_instruction
        )
        generated_script = modified_result.script.strip()
        if generated_script.startswith("```python"):
            generated_script = generated_script[8:].strip()
        if generated_script.endswith("```"):
            generated_script = generated_script[:-3].strip()
        print("Generated alternative length:", len(generated_script))
        return generated_script

    def _choose_best_version(
        self, original_script: str, editor_script: Optional[str], generated_script: str
    ) -> str:
        """Choose the best version based on similarity scores."""
        editor_similarity = (
            calculate_levenshtein_similarity(original_script, editor_script)
            if editor_script
            else 1.0
        )
        generated_similarity = calculate_levenshtein_similarity(
            original_script, generated_script
        )

        print("\nSimilarity scores:")
        print(f"Editor version: {editor_similarity:.3f}")
        print(f"Generated version: {generated_similarity:.3f}")

        if editor_script and 0.3 < editor_similarity < 0.9:
            return editor_script
        return generated_script

    def _generate_hindsight_command(
        self, original_script: str, edited_script: str
    ) -> str:
        """Generate a hindsight edit command."""
        hindsight = self.hindsight_generator(
            original=original_script, edited=edited_script
        )
        return hindsight.edit_command

    def forward(
        self, num_examples: int = 10, output_file: str = "data/edit_dataset.json"
    ) -> None:
        """Forward method for compatibility with DSPy transforms"""
        return self.generate_dataset(num_examples, output_file)

    def generate_dataset(self, num_examples: int, output_file: str) -> None:
        """Generate multiple examples and save to JSON file"""
        dataset = []

        for i in range(num_examples):
            print(f"Generating example {i+1}/{num_examples}...")
            try:
                datapoint = self.generate_datapoint()
                dataset.append(
                    {
                        "original": datapoint.original_script,
                        "edited": datapoint.edited_script,
                        "instruction": datapoint.edit_instruction,
                        "hindsight_command": datapoint.hindsight_command,
                    }
                )
            except (FileNotFoundError, PermissionError) as e:
                print(f"Error generating example {i+1}: {str(e)}")
                continue

        # Save dataset
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, indent=2)

        print(f"\nDataset generated with {len(dataset)} examples")
        print(f"Saved to: {output_path}")


def main():
    """Main function to generate the edit dataset"""
    # Configure DSPy
    lm = dspy.LM(model="gpt-4o-mini", max_tokens=2000)
    dspy.configure(lm=lm)

    # Set up generator with retry transform
    generator = EditDatasetGenerator()
    generator = dspy.Retry(generator)

    # Add backtracking for failed assertions
    def backtrack_handler(suggestion):
        """Handle backtracking with a suggestion"""
        print(f"Backtracking with suggestion: {suggestion}")
        return True

    generator = dspy.assert_transform_module(
        generator, backtrack_handler=backtrack_handler
    )
    generator(num_examples=10, output_file="data/edit_dataset.json")


if __name__ == "__main__":
    main()
