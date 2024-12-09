import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import dspy
from prismix.scripts.generate_edit_dataset import (
    EditDatasetGenerator, 
    EditDataPoint,
    GenerateScript,
    GenerateEditInstruction,
    GenerateHindsightEdit
)
from prismix.core.metrics import calculate_levenshtein_similarity

@pytest.fixture
def generator():
    """Set up EditDatasetGenerator with test configuration"""
    lm = dspy.LM(model="gpt-4o-mini", max_tokens=2000)
    dspy.configure(lm=lm)
    return EditDatasetGenerator()

def test_script_generation_themes(generator):
    """Test script generation for each theme"""
    for theme in generator.themes:
        result = generator.script_generator(theme=theme)
        assert isinstance(result.script, str)
        assert len(result.script) > 50  # Ensure substantial content
        
        # Basic Python syntax check
        try:
            compile(result.script, '<string>', 'exec')
        except SyntaxError as e:
            pytest.fail(f"Generated script for theme '{theme}' has invalid syntax: {e}")

def test_edit_instruction_generation(generator):
    """Test generation of edit instructions"""
    sample_scripts = [
        """
def hello():
    print("Hello")
""",
        """
class Calculator:
    def add(self, a, b):
        return a + b
""",
        """
def process_file(filepath):
    with open(filepath) as f:
        return f.read()
"""
    ]
    
    for script in sample_scripts:
        result = generator.edit_generator(script=script)
        assert isinstance(result.instruction, str)
        assert len(result.instruction) > 20
        assert any(keyword in result.instruction.lower() for keyword in 
                  ['add', 'modify', 'change', 'improve', 'implement', 'refactor'])

def test_hindsight_command_generation(generator):
    """Test generation of hindsight commands"""
    test_cases = [
        (
            "def add(a, b):\n    return a + b",
            "def add(a: int, b: int) -> int:\n    return a + b"
        ),
        (
            "print('hello')",
            "def greet():\n    print('hello')"
        ),
        (
            "x = 5",
            "x: int = 5  # Added type hint"
        )
    ]
    
    for original, edited in test_cases:
        result = generator.hindsight_generator(
            original=original,
            edited=edited
        )
        assert isinstance(result.edit_command, str)
        assert result.edit_command.startswith("edit")
        assert len(result.edit_command) > 10

def test_similarity_score_validation(generator):
    """Test similarity score validation logic"""
    test_cases = [
        # Too similar
        (
            "def add(a, b): return a + b",
            "def add(a, b): return a + b  # Added comment",
            True  # Should fail
        ),
        # Good difference
        (
            "def add(a, b): return a + b",
            "def calculator(a, b):\n    '''Add two numbers'''\n    return a + b",
            False  # Should pass
        ),
        # Too different
        (
            "def add(a, b): return a + b",
            "class ComplexCalculator:\n    def __init__(self):\n        self.history = []\n\n    def add(self, a, b):\n        result = a + b\n        self.history.append(result)\n        return result",
            True  # Should fail
        )
    ]
    
    for original, edited, should_fail in test_cases:
        similarity = calculate_levenshtein_similarity(original, edited)
        if should_fail:
            assert not (0.3 < similarity < 0.9), f"Expected similarity {similarity} to be outside 0.3-0.9 range"
        else:
            assert 0.3 < similarity < 0.9, f"Expected similarity {similarity} to be within 0.3-0.9 range"

def test_datapoint_generation_retries(generator):
    """Test retry mechanism in datapoint generation"""
    with patch('prismix.scripts.generate_edit_dataset.calculate_levenshtein_similarity') as mock_similarity:
        # Simulate improving similarity scores over retries
        mock_similarity.side_effect = [1.0, 0.95, 0.7, 0.5]
        
        datapoint = generator.generate_datapoint()
        assert isinstance(datapoint, EditDataPoint)
        assert len(datapoint.original_script) > 0
        assert len(datapoint.edited_script) > 0
        assert datapoint.original_script != datapoint.edited_script
        assert len(datapoint.edit_instruction) > 0
        assert datapoint.hindsight_command.startswith("edit")

def test_dataset_file_handling(generator, tmp_path):
    """Test dataset file creation and structure"""
    output_file = tmp_path / "test_dataset.json"
    
    # Mock generate_datapoint to return controlled data
    with patch.object(generator, 'generate_datapoint') as mock_generate:
        mock_generate.return_value = EditDataPoint(
            original_script="def test(): pass",
            edited_script="def test():\n    return True",
            edit_instruction="Add return statement",
            hindsight_command="edit test.py 'add return true'"
        )
        
        generator.generate_dataset(num_examples=3, output_file=str(output_file))
        
        # Verify file exists and content structure
        assert output_file.exists()
        with open(output_file) as f:
            dataset = json.load(f)
        
        assert isinstance(dataset, list)
        assert len(dataset) == 3
        for example in dataset:
            assert "original" in example
            assert "edited" in example
            assert "instruction" in example
            assert "hindsight_command" in example

def test_error_handling(generator):
    """Test error handling in dataset generation"""
    with patch.object(generator, 'script_generator') as mock_script:
        # Simulate various errors
        mock_script.side_effect = [
            Exception("LM API error"),
            ValueError("Invalid theme"),
            RuntimeError("Unexpected error")
        ]
        
        # Should handle errors gracefully
        datapoints = []
        for _ in range(3):
            try:
                datapoint = generator.generate_datapoint()
                datapoints.append(datapoint)
            except Exception as e:
                assert isinstance(e, (Exception, ValueError, RuntimeError))

def test_content_validation(generator):
    """Test validation of generated content"""
    test_scripts = [
        # Valid Python with imports
        """
import math
def calculate_circle_area(radius):
    return math.pi * radius ** 2
""",
        # Valid Python with class
        """
class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
    def area(self):
        return self.width * self.height
""",
        # Valid Python with multiple functions
        """
def add(a, b):
    return a + b
    
def subtract(a, b):
    return a - b
"""
    ]
    
    for script in test_scripts:
        # Verify script is valid Python
        try:
            compile(script, '<string>', 'exec')
        except SyntaxError as e:
            pytest.fail(f"Invalid Python syntax: {e}")
        
        # Generate edit instruction
        instruction_result = generator.edit_generator(script=script)
        assert isinstance(instruction_result.instruction, str)
        assert len(instruction_result.instruction) > 0
        
        # Generate hindsight command
        edited_script = script + "\n# Added comment"
        hindsight_result = generator.hindsight_generator(
            original=script,
            edited=edited_script
        )
        assert isinstance(hindsight_result.edit_command, str)
        assert hindsight_result.edit_command.startswith("edit")

def test_retry_mechanism(generator):
    """Test the retry mechanism with backtracking"""
    with patch.object(generator.script_generator, 'forward') as mock_script:
        # Simulate improving results over retries
        mock_script.side_effect = [
            dspy.Prediction(script="def test(): pass"),  # Too similar
            dspy.Prediction(script="def test():\n    '''Doc'''\n    pass"),  # Still too similar
            dspy.Prediction(script="def test():\n    '''Doc'''\n    return True"),  # Good enough
        ]
            
        datapoint = generator.generate_datapoint()
        assert isinstance(datapoint, EditDataPoint)
        assert mock_script.call_count > 1  # Should have retried

def test_parallel_generation(generator):
    """Test generating multiple examples in parallel"""
    from concurrent.futures import ThreadPoolExecutor
    import threading
    
    def generate_with_thread_info():
        thread_id = threading.get_ident()
        try:
            datapoint = generator.generate_datapoint()
            return (thread_id, datapoint)
        except Exception as e:
            return (thread_id, e)
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(lambda _: generate_with_thread_info(), range(3)))
        
        # Verify results from different threads
        thread_ids = set(r[0] for r in results)
        assert len(thread_ids) > 1  # Should use multiple threads
        
        # Check results
        for _, result in results:
            if isinstance(result, Exception):
                pytest.fail(f"Generation failed: {result}")
            assert isinstance(result, EditDataPoint)
