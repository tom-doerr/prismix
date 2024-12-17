"""
Test module for file operations.
"""

import os  # Move this to the top

import pytest

from prismix.core.file_operations import (
    DefaultFileOperations,
    FileContext,
    FileEditor,
    FileManager,
)
from prismix.core.iterative_programmer import setup_agent


@pytest.fixture
def test_file_fixture(tmp_path):
    """Create a temporary test file"""
    file_path = tmp_path / "test.py"
    content = """def main():
    print("Hello World!")

if __name__ == "__main__":
    main()
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return str(file_path)


@pytest.fixture
def agent():
    return setup_agent()


def test_file_read(test_file_fixture):
    """Test reading file content"""
    file_manager = FileManager(DefaultFileOperations())  # Create an instance here
    result = file_manager.read_file(test_file_fixture)  # Use the instance here
    assert isinstance(result, FileContext)
    assert result.error is None
    assert "def main():" in result.content
    assert result.filepath == test_file_fixture


def test_file_write(tmp_path):
    """Test writing file content"""
    file_path = str(tmp_path / "output.py")
    content = "print('test')"
    file_manager = FileManager(DefaultFileOperations())  # Create an instance here
    result = file_manager.write_file(file_path, content)  # Use the instance here

    assert isinstance(result, FileContext)
    assert result.error is None
    assert os.path.exists(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        assert f.read() == content


def test_line_numbering(test_file_fixture):
    """Test line numbering functionality"""
    editor = FileEditor()
    with open(test_file_fixture) as f:
        content = f.read()

    numbered = editor._number_lines(content)
    lines = numbered.splitlines()

    assert len(lines) > 0
    assert all(line.startswith("   ") for line in lines)  # Check padding
    assert all("|" in line for line in lines)  # Check separator
    assert lines[0].startswith("   1 |")  # Check first line number


def test_apply_line_edits_list():
    """Test applying line-specific edits with list format"""
    editor = FileEditor()
    original = "line 1\nline 2\nline 3"
    edits = [(2, "modified line 2")]

    new_content, changes = editor._apply_line_edits(original, edits)

    assert "modified line 2" in new_content
    assert len(changes) == 1
    assert "Replaced line 2" in changes[0]
    assert "line 2" in changes[0]
    assert "modified line 2" in changes[0]


def test_apply_line_edits_string():
    """Test applying line-specific edits with string format"""
    editor = FileEditor()
    original = "line 1\nline 2\nline 3"
    edits = "2 | modified line 2"

    new_content, changes = editor._apply_line_edits(original, edits)

    assert "modified line 2" in new_content
    assert len(changes) == 1
    assert "Replaced line 2" in changes[0]
    assert "line 2" in changes[0]
    assert "modified line 2" in changes[0]


def test_file_edit(agent, test_file_fixture):
    """Test editing file content"""
    instruction = "add a docstring to the main function"
    result = agent.forward(f"edit {test_file_fixture} '{instruction}'")

    assert isinstance(result, FileContext)
    assert result.error is None
    assert '"""' in result.content  # Should have added docstring
    assert len(result.changes) > 0


def test_replace_line():
    """Test replacing a line"""
    editor = FileEditor()
    content = "line 1\nline 2\nline 3"
    edits = [("replace", 2, "modified line 2")]

    new_content, changes = editor._apply_line_edits(content, edits)

    assert "modified line 2" in new_content
    assert len(changes) == 1
    assert "Replaced line 2" in changes[0]


def test_insert_line():
    """Test inserting a line"""
    editor = FileEditor()
    content = "line 1\nline 2\nline 3"
    edits = [("insert", 2, "new line")]

    new_content, changes = editor._apply_line_edits(content, edits)

    assert new_content.splitlines()[1] == "new line"
    assert len(new_content.splitlines()) == 4
    assert len(changes) == 1
    assert "Inserted at line 2" in changes[0]


def test_delete_line():
    """Test deleting a line"""
    editor = FileEditor()
    content = "line 1\nline 2\nline 3"
    edits = [("delete", 2, "")]

    new_content, changes = editor._apply_line_edits(content, edits)

    assert "line 2" not in new_content
    assert len(new_content.splitlines()) == 2
    assert len(changes) == 1
    assert "Deleted line 2" in changes[0]


def test_multiple_edit_modes():
    """Test multiple edits with different modes"""
    editor = FileEditor()
    content = "line 1\nline 2\nline 3\nline 4"
    edits = [
        ("replace", 1, "modified line 1"),
        ("insert", 3, "new line"),
        ("delete", 4, ""),
    ]

    new_content, changes = editor._apply_line_edits(content, edits)

    # Check content modifications
    assert "modified line 1" in new_content
    assert "new line" in new_content
    assert "line 4" not in new_content  # Ensure line 4 is deleted

    # Check changes list
    assert len(changes) == 3

    # Check final content structure
    lines = new_content.splitlines()
    assert len(lines) == 4
    assert lines[0] == "modified line 1"
    assert lines[1] == "line 2"
    assert lines[2] == "new line"
    assert lines[3] == "line 3"


def test_edit_line_numbers():
    """Test line number adjustments after edits"""
    editor = FileEditor()
    content = "line 1\nline 2\nline 3\nline 4"

    # Test that deleting a line adjusts subsequent line numbers
    edits = [
        ("delete", 2, ""),
        ("insert", 2, "new line"),  # Should insert at the original line 2 position
    ]

    new_content, changes = editor._apply_line_edits(content, edits)
    lines = new_content.splitlines()

    assert len(lines) == 4
    assert lines[0] == "line 1"
    assert lines[1] == "new line"
    assert lines[2] == "line 3"
    assert lines[3] == "line 4"


def test_edit_boundary_conditions():
    """Test edge cases in line editing"""
    editor = FileEditor()
    content = "line 1\nline 2"

    # Test invalid line numbers
    edits = [("replace", 0, "invalid"), ("replace", 999, "invalid")]
    new_content, changes = editor._apply_line_edits(content, edits)
    assert new_content == content  # Should not modify content
    assert all("Failed to apply" in change for change in changes)

    # Test empty content
    new_content, changes = editor._apply_line_edits("", [("insert", 1, "new line")])
    assert new_content == "new line"

    # Test inserting at end
    new_content, changes = editor._apply_line_edits(
        content, [("insert", 3, "new line")]
    )
    assert new_content.endswith("new line")


def test_edit_format_handling():
    """Test handling of different edit format inputs"""
    editor = FileEditor()
    content = "line 1\nline 2"

    # Test string format
    string_edits = "REPLACE 1 | modified line 1"
    new_content, changes = editor._apply_line_edits(content, string_edits)
    assert "modified line 1" in new_content
    assert len(changes) == 1
    assert "Replaced line 1: 'line 1' -> 'modified line 1'" in changes[0]

    # Test tuple format with explicit mode
    tuple_edits = [("REPLACE", 1, "modified again")]
    new_content, changes = editor._apply_line_edits(content, tuple_edits)
    assert "modified again" in new_content
    assert len(changes) == 1
    assert "Replaced line 1: 'line 1' -> 'modified again'" in changes[0]

    # Test tuple format without mode (should default to REPLACE)
    simple_edits = [(1, "simple modification")]
    new_content, changes = editor._apply_line_edits(content, simple_edits)
    assert "simple modification" in new_content
    assert len(changes) == 1
    assert "Replaced line 1: 'line 1' -> 'simple modification'" in changes[0]


def test_concurrent_edits():
    """Test multiple edits happening at the same line"""
    editor = FileEditor()
    content = "line 1\nline 2\nline 3"

    # Multiple edits targeting same line
    edits = [("replace", 2, "first change"), ("replace", 2, "second change")]
    new_content, changes = editor._apply_line_edits(content, edits)
    assert "second change" in new_content
    assert len(changes) == 2
    assert "Replaced line 2: 'line 2' -> 'first change'" in changes[0]
    assert "Replaced line 2: 'first change' -> 'second change'" in changes[1]


def test_edit_chain_effects():
    """Test how edits affect subsequent operations"""
    editor = FileEditor()
    content = "line 1\nline 2\nline 3\nline 4"

    # Chain of edits that affect each other
    edits = [
        ("delete", 2, ""),  # Deletes line 2
        ("insert", 2, "new line"),  # Inserts at the old line 2 position
        ("replace", 3, "line 3"),  # Keep original line 3
    ]
    new_content, changes = editor._apply_line_edits(content, edits)
    lines = new_content.splitlines()
    assert len(lines) == 4
    assert lines[0] == "line 1"
    assert lines[1] == "new line"
    assert lines[2] == "line 3"
    assert lines[3] == "line 4"
    assert len(changes) == 3


def test_whitespace_handling():
    """Test handling of whitespace in edits"""
    editor = FileEditor()
    content = "    indented line\n\tline with tab\nno indent"

    # Test preserving indentation
    edits = [
        ("replace", 1, "    new indented line"),
        ("replace", 2, "\tnew tabbed line"),
    ]
    new_content, changes = editor._apply_line_edits(content, edits)
    lines = new_content.splitlines()
    assert lines[0].startswith("    ")
    assert lines[1].startswith("\t")
    assert len(changes) == 2


def test_empty_and_whitespace_lines():
    """Test handling of empty and whitespace-only lines"""
    editor = FileEditor()
    content = "line 1\n\n    \nline 4"

    # Test operations on empty/whitespace lines
    edits = [("replace", 2, "new line 2"), ("replace", 3, "new line 3")]
    new_content, changes = editor._apply_line_edits(content, edits)
    assert len(new_content.splitlines()) == 4
    assert "new line 2" in new_content
    assert "new line 3" in new_content
    assert len(changes) == 2


def test_apply_line_edits_debug():
    """Debug test for line edits"""
    editor = FileEditor()
    content = "line 1\nline 2\nline 3\nline 4"

    # Test each edit type separately with debug output

    # Test REPLACE
    print("\nTesting REPLACE:")
    edits = [("replace", 2, "modified line 2")]
    new_content, changes = editor._apply_line_edits(content, edits)
    print(f"Content after replace:\n{new_content}")
    print(f"Changes: {changes}")

    # Test INSERT
    print("\nTesting INSERT:")
    edits = [("insert", 2, "new line")]
    new_content, changes = editor._apply_line_edits(content, edits)
    print(f"Content after insert:\n{new_content}")
    print(f"Changes: {changes}")

    # Test DELETE
    print("\nTesting DELETE:")
    edits = [("delete", 2, "")]
    new_content, changes = editor._apply_line_edits(content, edits)
    print(f"Content after delete:\n{new_content}")
    print(f"Changes: {changes}")

    # Test string format
    print("\nTesting string format:")
    string_edits = "REPLACE 2 | modified line 2"
    new_content, changes = editor._apply_line_edits(content, string_edits)
    print(f"Content after string edit:\n{new_content}")
    print(f"Changes: {changes}")

    # Test multiple edits
    print("\nTesting multiple edits:")
    edits = [
        ("replace", 1, "modified line 1"),
        ("insert", 3, "new line"),
        ("delete", 4, ""),
    ]
    new_content, changes = editor._apply_line_edits(content, edits)
    print(f"Content after multiple edits:\n{new_content}")
    print(f"Changes: {changes}")


def test_invalid_file():
    """Test handling non-existent file"""
    file_manager = FileManager(DefaultFileOperations())  # Create an instance here
    result = file_manager.read_file("nonexistent.py")  # Use the instance here
    assert isinstance(result, FileContext)
    assert result.error is not None
    assert "not exist" in result.error.lower()


def test_invalid_edit_command(agent):
    """Test handling invalid edit command"""
    result = agent.forward("edit")
    assert isinstance(result, FileContext)
    assert result.error is not None
    assert "invalid edit command" in result.error.lower()


def test_write_to_new_directory(tmp_path):
    """Test writing file to new directory"""
    file_path = str(tmp_path / "new_dir" / "test.py")
    os.makedirs(
        os.path.dirname(file_path), exist_ok=True
    )  # Ensure the directory exists
    content = "print('test')"
    file_manager = FileManager(DefaultFileOperations())  # Create an instance here
    result = file_manager.write_file(file_path, content)  # Use the instance here

    assert isinstance(result, FileContext)
    assert result.error is None
    assert os.path.exists(file_path)
    with open(file_path) as f:
        assert f.read() == content
