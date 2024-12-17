"""
Test module for file editor module.
"""

import os
import tempfile

import dspy
import pytest
from prismix.core.file_editor_module import FileEditorModule

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


def test_file_edit_module_no_change(file_editor_module):
    """Test file edit with no change."""
    """Test file edit with no change."""
    updated_content = file_editor_module.apply_replacements(
        content="def hello():\n    print('hello')\n",
        instruction="Do not change 'print(\\'hello\\')'.",
    )

    # Ensure the file was written
    assert updated_content.content == "def hello():\n    print('hello')\n"
    assert updated_content.changes == []


def test_file_edit_module_multiple_replacements(file_editor_module):
    """Test file edit with multiple replacements."""
    # Test file edit with multiple replacements
    updated_content = file_editor_module.forward(
        context=f"File: {str(temp_file)}\nContent: def hello():\n    print('hello')\n",
        instruction="Replace 'print(\\'hello\\')' with 'print(\\'hi\\')' and Replace 'def hello()' with 'def greet()'",
    )

    # Ensure the file was written
    assert updated_content.content.strip() == "def greet():\n    print('hi')\n"
    assert updated_content.changes == [
        ("def hello():", "def greet():"),
        ("    print('hello')", "    print('hi')"),
    ]


def test_file_edit_module_overlapping_replacements(file_editor_module):
    """Test file edit with overlapping replacements."""
    """Test file edit with overlapping replacements."""
    # Test file edit with overlapping replacements
    updated_content = file_editor_module.forward(
        context=f"File: {str(temp_file)}\nContent: def hello():\n    print('hello')\n",
        instruction="Replace 'print(\\'hello\\')' with 'print(\\'hi\\')' and Replace 'hello' with 'greet'",
    )

    # Ensure the file was written
    assert updated_content.content == "def greet():\n    print('hi')\n"


def test_file_edit_module_empty_file(file_editor_module):
    """Test file edit with an empty file."""
    # Test file edit with an empty file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("")
        temp_file_path = f.name

    updated_content = file_editor_module.forward(
        context=f"File: {temp_file_path}\nContent: ",
        instruction="Replace 'print(\\'hello\\')' with 'print(\\'hi\\')'.",
    )

    # Ensure the file remains empty
    assert updated_content.content.strip() == ""
    assert updated_content.changes == []

    # Read the file again to ensure the changes were written
    with open(temp_file_path, "r", encoding="utf-8") as f:
        final_content = f.read()

    assert final_content == ""


def test_file_edit_module_file_not_found(file_editor_module):
    """Test file edit with file not found."""
    # Test file edit with file not found
    result = file_editor_module.forward(
        context="non_existent_file.py def hello():\n    print('hello')\n",
        instruction="Replace 'print(\\'hello\\')' with 'print(\\'hi\\')'.",
    )
    assert "Error reading file" in str(result.error)
    assert result.changes == []


def test_apply_single_replacement_function_def(file_editor_module):
    """Test apply single replacement with function definition."""
    content = "def hello():\n    print('hello')\n"
    search_pattern = "def hello():"
    replacement_code = "def greet():\n    print('hi')"
    updated_content = file_editor_module.apply_single_replacement(
        content, search_pattern, replacement_code
    )
    assert updated_content == "def greet():\n    print('hi')\n"


def test_apply_single_replacement_simple(file_editor_module):
    """Test apply single replacement with simple string."""
    content = "This is a test string."
    search_pattern = "test"
    replacement_code = "sample"
    updated_content = file_editor_module.apply_single_replacement(
        content, search_pattern, replacement_code
    )
    assert updated_content == "This is a sample string."


def test_read_file(file_editor_module):
    """Test reading an existing file."""
    file_context = file_editor_module.read_file(str(temp_file))
    assert file_context.content == "def hello():\n    print('hello')\n"
    assert file_context.filepath == temp_file
    assert not file_context.error
    assert file_context.changes == [], f"Unexpected changes: {file_context.changes}"


def test_read_file_not_found(file_editor_module):
    """Test reading a non-existing file."""
    file_context = file_editor_module.read_file("non_existent_file.py")
    assert file_context.content == ""
    assert file_context.filepath == "non_existent_file.py"
    assert file_context.error == "File does not exist"
    assert file_context.changes == []


def test_forward_with_no_file_content_in_context(file_editor_module):
    """Test forward method with no file content in context."""
    instruction = "Replace 'print(\\'hello\\')' with 'print(\\'hi\\')'"
    file_context = file_editor_module.forward(
        context=f"{temp_file} def hello():\n    print('hello')\n",
        instruction=instruction,
    )
    assert file_context.content == "def hello():\n    print('hi')\n"
    assert not file_context.error
    assert file_context.changes == [("    print('hello')", "    print('hi')")]


def test_write_file(file_editor_module):
    """Test writing to a file."""
    new_content = "def greet():\n    print('hi')\n"
    file_context = file_editor_module.write_file("test_write_file.txt", new_content)
    assert file_context.content == new_content
    assert file_context.filepath == temp_file
    assert not file_context.error
    assert file_context.changes == []

    # Read the file again to ensure the changes were written
    with open(temp_file, "r", encoding="utf-8") as f:
        final_content = f.read()
    assert final_content == new_content


def test_forward_with_valid_edit(file_editor_module):
    """Test forward method with valid edit."""
    instruction = "Replace 'print(\\'hello\\')' with 'print(\\'hi\\')'"
    file_context = file_editor_module.forward(
        context=f"{temp_file} def hello():\n    print('hello')\n",
        instruction=instruction,
    )
    assert file_context.content == "def hello():\n    print('hi')\n"
    assert not file_context.error
    assert file_context.changes == [("    print('hello')", "    print('hi')")]


def test_forward_with_no_change(file_editor_module):
    """Test forward method with no change."""
    instruction = "Do not change 'print(\\'hello\\')'"
    file_context = file_editor_module.forward(
        context=f"{temp_file} def hello():\n    print('hello')\n",
        instruction=instruction,
    )
    assert file_context.content == "def hello():\n    print('hello')\n"
    assert not file_context.error
    assert file_context.changes == []


def test_forward_with_multiline_replacement(file_editor_module):
    """Test forward method with multiline replacement."""
    # Test file edit with multiline replacement
    updated_content = file_editor_module.forward(
        context=f"File: {temp_file}\nContent: def hello():\n    print('hello')\n",
        instruction="Replace 'def hello():\\n    print(\\'hello\\')' with 'def greet():\\n    print(\\'hi\\')\\n    print(\\'there\\')'",
    )
    assert (
        updated_content.content == "def greet():\n    print('hi')\n    print('there')\n"
    )
    assert updated_content.changes == [
        (
            "def hello():\n    print('hello')",
            "def greet():\n    print('hi')\n    print('there')",
        )
    ]


def test_forward_with_no_replacements(file_editor_module):
    """Test forward method with no replacements."""
    # Test file edit with no replacements
    updated_content = file_editor_module.forward(
        context=f"File: {temp_file}\nContent: def hello():\n    print('hello')\n",
        instruction="Replace 'non_existent' with 'new_text'",
    )
    assert updated_content.content.strip() == "def hello():\n    print('hello')\n"
    assert updated_content.changes == []


def test_forward_with_different_replacements(file_editor_module):
    """Test forward method with different replacements."""
    # Test file edit with different types of replacements
    updated_content = file_editor_module.forward(
        context=f"File: {temp_file}\nContent: def hello():\n    print('hello')\n    return 1",
        instruction="Replace 'print(\\'hello\\')' with 'print(\\'hi\\')' and Replace 'def hello():' with 'def greet():'",
    )
    assert (
        updated_content.content.strip() == "def greet():\n    print('hi')\n    return 1"
    )
    assert updated_content.changes == [
        ("def hello():", "def greet():"),
        ("    print('hello')", "    print('hi')"),
    ]


def test_forward_with_edge_cases(file_editor_module):
    """Test forward method with edge cases."""
    # Test file edit with edge cases
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("# This is a comment\n")
        temp_file_path_comment = f.name

    updated_content_comment = file_editor_module.forward(
        context=f"File: {temp_file_path_comment}\nContent: # This is a comment\n",
        instruction="Replace '# This is a comment' with '# New comment'",
    )
    assert updated_content_comment.content == "# New comment\n"
    assert updated_content_comment.changes == [("# This is a comment", "# New comment")]
    os.remove(temp_file_path_comment)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("")
        temp_file_path_empty = f.name

    updated_content_empty = file_editor_module.forward(
        context=f"File: {temp_file_path_empty}\nContent: ",
        instruction="Replace 'non_existent' with 'new_text'",
    )
    assert updated_content_empty.content == ""
    assert updated_content_empty.changes == []
    os.remove(temp_file_path_empty)


def test_forward_with_file_not_found(file_editor_module):
    instruction = "Replace 'print(\\'hello\\')' with 'print(\\'hi\\')'"
    file_context = file_editor_module.forward(
        context="non_existent_file.py def hello():\n    print('hello')\n",
        instruction=instruction,
    )
    assert "Error reading file" in file_context.error
    assert file_context.changes == []
    assert file_context.changes == []
