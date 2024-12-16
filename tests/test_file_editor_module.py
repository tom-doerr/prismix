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


def test_file_edit_module(file_editor_module, temp_file):
    # Test successful file edit
    updated_content = file_editor_module.forward(
        context=f"File: {temp_file}\nContent: def hello():\n    print('hello')\n",
        instruction="Replace 'print('hello')' with 'print('hi')'.",
    )
    
    # Ensure the file was written
    assert updated_content == "def hello():\n    print('hi')\n"

def test_file_edit_module_no_change(file_editor_module, temp_file):
    # Test file edit with no change
    updated_content = file_editor_module.forward(
        context=f"File: {temp_file}\nContent: def hello():\n    print('hello')\n",
        instruction="Do not change 'print('hello')'.",
    )
    
    # Ensure the file was written
    assert updated_content == "def hello():\n    print('hello')\n"


def test_file_edit_module_file_not_found(file_editor_module):
    # Test file edit with file not found
    result = file_editor_module.forward(
        context="def hello():\n    print('hello')\n",
        instruction="Replace 'print('hello')' with 'print('hi')'.",
    )
    assert "Error reading file" in result.error
