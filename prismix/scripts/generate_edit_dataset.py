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
        
    def generate_datapoint(self, max_retries: int = 3) -> EditDataPoint:
        """Generate a single edit transformation example with retries"""
        for attempt in range(max_retries):
            try:
                # 1. Generate original script
                theme = random.choice(self.themes)
                result = self.script_generator(theme=theme)
                # Remove markdown wrapper if present
                original_script = result.script.strip()
                if original_script.startswith("```python"):
                    original_script = original_script[8:].strip()
                if original_script.endswith("```"):
                    original_script = original_script[:-3].strip()
        
                # 2. Generate edit instruction
                edit_result = self.edit_generator(script=original_script)
                edit_instruction = edit_result.instruction
                
                # 3. Apply edit instruction using FileEditor
                editor = FileEditor()
                temp_file = "temp.py"
                with open(temp_file, "w") as f:
                    f.write(original_script)
                    
                file_context = editor.edit_file(temp_file, edit_instruction)
                
                # Generate modified version with both approaches
                modified_result = self.script_generator(
                    theme=theme,
                    instruction=edit_instruction
                )
                generated_script = modified_result.script.strip()
                if generated_script.startswith("```python"):
                    generated_script = generated_script[8:].strip()
                if generated_script.endswith("```"):
                    generated_script = generated_script[:-3].strip()
                    
                # Compare both versions and use the one with significant changes
                editor_script = file_context.content if not file_context.error else None
        
                # Calculate and validate similarity scores using DSPy assertions
                editor_similarity = calculate_levenshtein_similarity(original_script, editor_script) if editor_script else 1.0
                generated_similarity = calculate_levenshtein_similarity(original_script, generated_script)
                
                # Assert that at least one version has meaningful changes
                dspy.Assert(
                    0.3 < editor_similarity < 0.9 or 0.3 < generated_similarity < 0.9,
                    f"Similarity scores (editor: {editor_similarity:.2f}, generated: {generated_similarity:.2f}) " 
                    "should be between 0.3 and 0.9 for meaningful changes",
                    on_failure=dspy.Suggest("Try generating a more substantially different version")
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
                
            except Exception as e:
                print(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise ValueError(f"Failed to generate valid edit after {max_retries} attempts: {str(e)}")
    
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
    
    # Set up generator with retry transform
    generator = EditDatasetGenerator()
    generator = dspy.assert_transform_module(
        generator.map_named_predictors(dspy.Retry(max_retries=3)), 
        dspy.backtrack_handler
    )
    generator.generate_dataset(
        num_examples=10,
        output_file="data/edit_dataset.json"
    )

if __name__ == "__main__":
    main()
