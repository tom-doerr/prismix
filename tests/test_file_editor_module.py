"""
Test module for file editor module.
"""

import pytest
import tempfile
import dspy
from prismix.core.file_editor_module import FileEditorModule
from prismix.core.file_operations import FileManager

lm = dspy.LM(model="gpt-4o-mini", max_tokens=2000)
dspy.configure(lm=lm)


@pytest.fixture
def file_editor_module():
    return FileEditorModule()


@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def hello():\n    print('hello')\n")
        temp_file_path = f.name
    yield temp_file_path
    import os

    os.remove(temp_file_path)



def test_file_edit_module_no_change(file_editor_module, temp_file):
    # Test file edit with no change
    updated_content = file_editor_module.forward(
        context=f"File: {temp_file}\nContent: def hello():\n    print('hello')\n",
        instruction="Do not change 'print('hello')'.",
    )
    
    # Ensure the file was written
    assert updated_content == "def hello():\n    print('hello')\n"

def test_file_edit_module_multiple_replacements(file_editor_module, temp_file):
    # Test file edit with multiple replacements
    updated_content = file_editor_module.forward(
        context=f"File: {temp_file}\nContent: def hello():\n    print('hello')\n",
        instruction="Replace 'print('hello')' with 'print('hi')' and Replace 'def hello()' with 'def greet()'",
    )
    
    # Ensure the file was written
    assert updated_content == "def greet():\n    print('hi')\n"

def test_file_edit_module_overlapping_replacements(file_editor_module, temp_file):
    # Test file edit with overlapping replacements
    updated_content = file_editor_module.forward(
        context=f"File: {temp_file}\nContent: def hello():\n    print('hello')\n",
        instruction="Replace 'print('hello')' with 'print('hi')' and Replace 'hello' with 'greet'",
    )
    
    # Ensure the file was written
    assert updated_content == "def greet():\n    print('hi')\n"


def test_file_edit_module_empty_file(file_editor_module):
    # Test file edit with an empty file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("")
        temp_file_path = f.name

    updated_content = file_editor_module.forward(
        context=f"File: {temp_file_path}\nContent: ",
        instruction="Replace 'print('hello')' with 'print('hi')'.",
    )
    
    # Ensure the file remains empty
    assert updated_content == ""

    # Read the file again to ensure the changes were written
    with open(temp_file_path, "r") as f:
        final_content = f.read()
    
    assert final_content == ""



def test_file_edit_module_file_not_found(file_editor_module):
    # Test file edit with file not found
    result = file_editor_module.forward(
        context="def hello():\n    print('hello')\n",
        instruction="Replace 'print('hello')' with 'print('hi')'.",
    )
    assert "Error reading file" in result.error
