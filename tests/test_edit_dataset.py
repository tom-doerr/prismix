import pytest
import json
from pathlib import Path
import dspy
from prismix.scripts.generate_edit_dataset import (
    EditDatasetGenerator,
    EditDataPoint,
    GenerateScript,
    GenerateEditInstruction,
    GenerateHindsightEdit
)

@pytest.fixture
def generator():
    """Set up EditDatasetGenerator with test configuration"""
    lm = dspy.LM(model="gpt-4", max_tokens=2000)
    dspy.configure(lm=lm)
    return EditDatasetGenerator()

def test_generate_datapoint(generator, tmp_path):
    """Test generation of a single edit datapoint"""
    datapoint = generator.generate_datapoint()
    
    # Check datapoint structure
    assert isinstance(datapoint, EditDataPoint)
    assert isinstance(datapoint.original_script, str)
    assert isinstance(datapoint.edited_script, str)
    assert isinstance(datapoint.edit_instruction, str)
    assert isinstance(datapoint.hindsight_command, str)
    
    # Check content
    assert len(datapoint.original_script) > 0
    assert len(datapoint.edited_script) > 0
    assert datapoint.original_script != datapoint.edited_script
    assert datapoint.edit_instruction.strip() != ""
    assert datapoint.hindsight_command.startswith("edit")

def test_generate_dataset(generator, tmp_path):
    """Test generation of multiple examples"""
    output_file = tmp_path / "test_dataset.json"
    generator.generate_dataset(num_examples=2, output_file=str(output_file))
    
    # Check file was created
    assert output_file.exists()
    
    # Check content structure
    with open(output_file) as f:
        dataset = json.load(f)
    
    assert isinstance(dataset, list)
    assert len(dataset) == 2
    
    for example in dataset:
        assert "original" in example
        assert "edited" in example
        assert "instruction" in example
        assert "hindsight_command" in example

def test_script_generation(generator):
    """Test script generation with different themes"""
    for theme in generator.themes[:2]:  # Test first two themes
        result = generator.script_generator(theme=theme)
        assert isinstance(result.script, str)
        assert len(result.script) > 0
        # Basic Python syntax check
        compile(result.script, '<string>', 'exec')

def test_edit_instruction_generation(generator):
    """Test edit instruction generation"""
    sample_script = """
def hello():
    print("Hello")
"""
    result = generator.edit_generator(script=sample_script)
    assert isinstance(result.instruction, str)
    assert len(result.instruction) > 0

def test_hindsight_command_generation(generator):
    """Test hindsight command generation"""
    original = """
def hello():
    print("Hello")
"""
    edited = """
def hello():
    \"\"\"Say hello to the world\"\"\"
    print("Hello")
"""
    result = generator.hindsight_generator(
        original=original,
        edited=edited
    )
    assert isinstance(result.edit_command, str)
    assert result.edit_command.startswith("edit")
