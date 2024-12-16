"""
Test module for file editor module.
"""

import pytest
import tempfile
import dspy
import os
from prismix.core.file_editor_module import FileEditorModule
from prismix.core.file_operations import FileManager, FileContext

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
    os.remove(temp_file_path)



def test_file_edit_module_no_change(file_editor_module, temp_file):
    # Test file edit with no change
    updated_content = file_editor_module.forward(
        context=f"File: {temp_file}\nContent: def hello():\n    print('hello')\n",
        instruction="Do not change 'print('hello')'.",
    )
    
    # Ensure the file was written
    assert updated_content.content == "def hello():\n    print('hello')\n"


def test_file_edit_module_multiple_replacements(file_editor_module, temp_file):
    # Test file edit with multiple replacements
    updated_content = file_editor_module.forward(
        context=f"File: {temp_file}\nContent: def hello():\n    print('hello')\n",
        instruction="Replace 'print(\\'hello\\')' with 'print(\\'hi\\')' and Replace 'def hello()' with 'def greet()'",
    )

    # Ensure the file was written
    assert updated_content.content == "def greet():\n    print('hi')\n"


def test_file_edit_module_overlapping_replacements(file_editor_module, temp_file):
    # Test file edit with overlapping replacements
    updated_content = file_editor_module.forward(
        context=f"File: {temp_file}\nContent: def hello():\n    print('hello')\n",
        instruction="Replace 'print(\\'hello\\')' with 'print(\\'hi\\')' and Replace 'hello' with 'greet'",
    )

    # Ensure the file was written
    assert updated_content.content == "def greet():\n    print('hi')\n"


def test_file_edit_module_empty_file(file_editor_module):
    # Test file edit with an empty file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("")
        temp_file_path = f.name

    updated_content = file_editor_module.forward(
        context=f"File: {temp_file_path}\nContent: ",
        instruction="Replace 'print(\\'hello\\')' with 'print(\\'hi\\')'.",
    )

    # Ensure the file remains empty
    assert updated_content.content == ""

    # Read the file again to ensure the changes were written
    with open(temp_file_path, "r") as f:
        final_content = f.read()

    assert final_content == ""



def test_file_edit_module_file_not_found(file_editor_module):
    # Test file edit with file not found
    result = file_editor_module.forward(
        context="non_existent_file.py def hello():\n    print('hello')\n",
        instruction="Replace 'print(\\'hello\\')' with 'print(\\'hi\\')'.",
    )
    assert "Error reading file" in result.error


def test_apply_single_replacement_function_def(file_editor_module):
    content = "def hello():\n    print('hello')\n"
    search_pattern = "def hello():"
    replacement_code = "def greet():\n    print('hi')"
    updated_content = file_editor_module.apply_single_replacement(
        content, search_pattern, replacement_code
    )
    assert updated_content == "def greet():\n    print('hi')\n"


def test_apply_single_replacement_simple(file_editor_module):
    content = "This is a test string."
    search_pattern = "test"
    replacement_code = "sample"
    updated_content = file_editor_module.apply_single_replacement(
        content, search_pattern, replacement_code
    )
    assert updated_content == "This is a sample string."


def test_read_file(file_editor_module, temp_file):
    file_context = file_editor_module.read_file(temp_file)
    assert file_context.content == "def hello():\n    print('hello')\n"
    assert file_context.filepath == temp_file
    assert not file_context.error


def test_read_file_not_found(file_editor_module):
    file_context = file_editor_module.read_file("non_existent_file.py")
    assert file_context.content == ""
    assert file_context.filepath == "non_existent_file.py"
    assert file_context.error == "File does not exist"


def test_write_file(file_editor_module, temp_file):
    new_content = "def greet():\n    print('hi')\n"
    file_context = file_editor_module.write_file(temp_file, new_content)
    assert file_context.content == new_content
    assert file_context.filepath == temp_file
    assert not file_context.error

    # Read the file again to ensure the changes were written
    with open(temp_file, "r") as f:
        final_content = f.read()
    assert final_content == new_content


def test_forward_with_valid_edit(file_editor_module, temp_file):
    instruction = "Replace 'print(\\'hello\\')' with 'print(\\'hi\\')'"
    file_context = file_editor_module.forward(
        context=f"{temp_file} def hello():\n    print('hello')\n",
        instruction=instruction,
    )
    assert file_context.content == "def hello():\n    print('hi')\n"
    assert not file_context.error


def test_forward_with_no_change(file_editor_module, temp_file):
    instruction = "Do not change 'print(\\'hello\\')'"
    file_context = file_editor_module.forward(
        context=f"{temp_file} def hello():\n    print('hello')\n",
        instruction=instruction,
    )
    assert file_context.content == "def hello():\n    print('hello')\n"
    assert not file_context.error


def test_forward_with_file_not_found(file_editor_module):
    instruction = "Replace 'print(\\'hello\\')' with 'print(\\'hi\\')'"
    file_context = file_editor_module.forward(
        context="non_existent_file.py def hello():\n    print('hello')\n",
        instruction=instruction,
    )
    assert "Error reading file" in file_context.error
