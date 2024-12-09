import json
import random
from pathlib import Path
from dataclasses import dataclass
import dspy
from typing import List, Dict, Any, Tuple
from prismix.core.file_operations import FileEditor
from prismix.core.metrics import calculate_levenshtein_similarity

class GenerateScript(dspy.Signature):
    """Generate a Python script based on a theme"""
    theme = dspy.InputField(desc="Theme or topic for the script (e.g., 'file processing', 'data structures')")
    script = dspy.OutputField(desc="Complete Python script following best practices")

class GenerateEditInstruction(dspy.Signature):
    """Generate an edit instruction for a script"""
    script = dspy.InputField(desc="Original Python script")
    instruction = dspy.OutputField(desc="Natural language instruction for editing the script (e.g., 'add error handling', 'improve documentation')")

class GenerateHindsightEdit(dspy.Signature):
    """Generate precise edit command that describes transformation between two scripts"""
    original = dspy.InputField(desc="Original script content")
    edited = dspy.InputField(desc="Edited script content")
    edit_command = dspy.OutputField(desc="Precise edit command in format: 'edit <description of changes>' that would transform original into edited version")

@dataclass
class EditDataPoint:
    """Represents a single edit transformation example"""
    original_script: str
    edited_script: str
    edit_instruction: str
    hindsight_command: str
    
class EditDatasetGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
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
            "configuration management"
        ]
        
    def generate_datapoint(self) -> EditDataPoint:
        """Generate a single edit transformation example"""
        print("\nGenerating new datapoint...")
        
        # 1. Generate original script
        theme = random.choice(self.themes)
        print(f"Selected theme: {theme}")
        
        result = self.script_generator(theme=theme)
        print("Generated original script length:", len(result.script))
        
        # Remove markdown wrapper if present
        original_script = result.script.strip()
        if original_script.startswith("```python"):
            original_script = original_script[8:].strip()
        if original_script.endswith("```"):
            original_script = original_script[:-3].strip()
        
        print("Cleaned script length:", len(original_script))
        print("Script preview:", original_script[:100] + "..." if len(original_script) > 100 else original_script)
    
        # 2. Generate edit instruction
        print("\nGenerating edit instruction...")
        edit_result = self.edit_generator(script=original_script)
        edit_instruction = edit_result.instruction
        print("Edit instruction:", edit_instruction)
        
        # 3. Apply edit instruction using FileEditor
        print("\nApplying edits...")
        editor = FileEditor()
        temp_file = "temp.py"
        with open(temp_file, "w") as f:
            f.write(original_script)
            
        file_context = editor.edit_file(temp_file, edit_instruction)
        if file_context.error:
            print("Editor error:", file_context.error)
        else:
            print("Editor changes:", len(file_context.changes), "modifications")
            for change in file_context.changes:
                print(f"- {change}")
        
        # Generate modified version with both approaches
        print("\nGenerating alternative version...")
        modified_result = self.script_generator(
            theme=theme,
            instruction=edit_instruction
        )
        generated_script = modified_result.script.strip()
        if generated_script.startswith("```python"):
            generated_script = generated_script[8:].strip()
        if generated_script.endswith("```"):
            generated_script = generated_script[:-3].strip()
            
        print("Generated alternative length:", len(generated_script))
        
        # Compare both versions and use the one with significant changes
        editor_script = file_context.content if not file_context.error else None
        
        # Log similarity scores
        if editor_script:
            editor_similarity = calculate_levenshtein_similarity(original_script, editor_script)
            print(f"\nEditor version similarity: {editor_similarity:.3f}")
            print("Editor changes preview:", editor_script[:100] + "..." if len(editor_script) > 100 else editor_script)
        else:
            editor_similarity = 1.0
            print("\nNo valid editor version")
            
        generated_similarity = calculate_levenshtein_similarity(original_script, generated_script)
        print(f"Generated version similarity: {generated_similarity:.3f}")
        print("Generated changes preview:", generated_script[:100] + "..." if len(generated_script) > 100 else generated_script)

        # Calculate similarity scores and retry until we get meaningful changes
        editor_similarity = calculate_levenshtein_similarity(original_script, editor_script) if editor_script else 1.0
        generated_similarity = calculate_levenshtein_similarity(original_script, generated_script)
        
        # Use DSPy assertions with suggestions for guidance
        dspy.Assert(
            0.3 < editor_similarity < 0.9 or 0.3 < generated_similarity < 0.9,
            f"Similarity scores (editor: {editor_similarity:.2f}, generated: {generated_similarity:.2f}) " 
            "should be between 0.3 and 0.9 for meaningful changes. "
            "Try making more substantial modifications to the code structure, "
            "such as adding new functions, changing logic flow, or restructuring classes."
        )
        
        # Provide specific suggestions for the LLM to improve the changes
        if editor_similarity >= 0.9:
            dspy.Suggest(
                "Make more significant changes in the editor version by:\n"
                "1. Adding new helper functions\n"
                "2. Implementing error handling\n"
                "3. Restructuring the code organization\n"
                "4. Adding new features or functionality"
            )
        
        if generated_similarity >= 0.9:
            dspy.Suggest(
                "Generate a more substantially different version by:\n"
                "1. Using different algorithms or approaches\n"
                "2. Adding new class structures\n"
                "3. Implementing additional features\n"
                "4. Changing the code architecture"
            )
        
        # Choose the version with better similarity score
        if editor_script and 0.3 < editor_similarity < 0.9:
            edited_script = editor_script
        else:
            edited_script = generated_script

        # 4. Generate hindsight edit command
        hindsight = self.hindsight_generator(
            original=original_script,
            edited=edited_script
        )

        return EditDataPoint(
            original_script=original_script,
            edited_script=edited_script,
            edit_instruction=edit_instruction,
            hindsight_command=hindsight.edit_command
        )
    
    def forward(self, num_examples: int = 10, output_file: str = "data/edit_dataset.json") -> None:
        """Forward method for compatibility with DSPy transforms"""
        return self.generate_dataset(num_examples, output_file)
        
    def generate_dataset(self, num_examples: int, output_file: str) -> None:
        """Generate multiple examples and save to JSON file"""
        dataset = []
        
        for i in range(num_examples):
            print(f"Generating example {i+1}/{num_examples}...")
            try:
                datapoint = self.generate_datapoint()
                dataset.append({
                    "original": datapoint.original_script,
                    "edited": datapoint.edited_script,
                    "instruction": datapoint.edit_instruction,
                    "hindsight_command": datapoint.hindsight_command
                })
            except Exception as e:
                print(f"Error generating example {i+1}: {str(e)}")
                continue
        
        # Save dataset
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(dataset, f, indent=2)
        
        print(f"\nDataset generated with {len(dataset)} examples")
        print(f"Saved to: {output_path}")

def main():
    # Configure DSPy
    lm = dspy.LM(model="gpt-4o-mini", max_tokens=2000)
    dspy.configure(lm=lm)
    
    # Set up generator with retry transform and custom backtrack handler
    generator = EditDatasetGenerator()
    from functools import partial
    custom_backtrack = partial(dspy.backtrack_handler, max_backtracks=30)
    generator = dspy.assert_transform_module(
        generator.map_named_predictors(dspy.Retry), 
        custom_backtrack
    )
    generator(
        num_examples=10,
        output_file="data/edit_dataset.json"
    )

if __name__ == "__main__":
    main()
