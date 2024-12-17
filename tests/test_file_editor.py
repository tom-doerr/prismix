"""
Test module for the FileEditorModule class.
"""

import os
from prismix.core.file_editor_module import FileEditorModule


def test_apply_replacements():
    """Test the apply_replacements method."""
    editor = FileEditorModule()
    content = "def foo():\n    pass"
    instruction = "Replace 'pass' with 'print(\"hello\")'"
    updated_content = editor.forward(
        context=f"Content: {content}", instruction=instruction
    )
    assert updated_content.content == 'def foo():\n    print("hello")\n'
    assert (
        editor.file_manager.write_file("test_file.py", updated_content.content).content
        == updated_content.content
    )


def test_read_file_existing():
    """Test reading an existing file."""
    editor = FileEditorModule()
    # Create a dummy file for testing
    with open("test_file.txt", "w", encoding="utf-8") as f:
        f.write("test content")
    file_context = editor.read_file("test_file.txt")
    assert file_context.content == "test content"
    assert file_context.error is None

    os.remove("test_file.txt")


def test_read_file_not_existing():
    """Test reading a non-existing file."""
    editor = FileEditorModule()
    file_context = editor.read_file("non_existing_file.txt")
    assert file_context.content == ""
    assert file_context.error == "File does not exist"


def test_write_file():
    """Test writing to a file."""
    editor = FileEditorModule()
    content = "new content"
    file_context = editor.write_file("test_write_file.txt", content)
    assert file_context.content == content
    assert file_context.error is None
    with open("test_write_file.txt", "r", encoding="utf-8") as f:
        file_content = f.read()
    assert file_content == content

    os.remove("test_write_file.txt")
    assert not os.path.exists("test_write_file.txt")
