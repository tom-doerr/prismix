import json
import random
from pathlib import Path
from dataclasses import dataclass
import dspy
from typing import List, Dict, Any, Tuple
from prismix.core.file_operations import FileEditor

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
    
class EditDatasetGenerator:
    def __init__(self):
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
        if not file_context.error and file_context.changes:
            edited_script = file_context.content
        else:
            # Generate a modified version if FileEditor didn't make changes
            modified_result = self.script_generator(
                theme=theme,
                instruction=edit_instruction
            )
            edited_script = modified_result.script.strip()
            if edited_script.startswith("```python"):
                edited_script = edited_script[8:].strip()
            if edited_script.endswith("```"):
                edited_script = edited_script[:-3].strip()
        
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
    lm = dspy.LM(model="gpt-4", max_tokens=2000)
    dspy.configure(lm=lm)
    
    # Generate dataset
    generator = EditDatasetGenerator()
    generator.generate_dataset(
        num_examples=10,
        output_file="data/edit_dataset.json"
    )

if __name__ == "__main__":
    main()
