import os
import pytest
from prismix.core.iterative_programmer import setup_agent
from prismix.core.file_operations import FileContext, FileManager, FileEditor

@pytest.fixture
def test_file(tmp_path):
    """Create a temporary test file"""
    file_path = tmp_path / "test.py"
    content = """def main():
    print("Hello World!")

if __name__ == "__main__":
    main()
"""
    with open(file_path, 'w') as f:
        f.write(content)
    return str(file_path)

@pytest.fixture
def agent():
    return setup_agent()

def test_file_read(test_file):
    """Test reading file content"""
    result = FileManager.read_file(test_file)
    assert isinstance(result, FileContext)
    assert result.error is None
    assert "def main():" in result.content
    assert result.filepath == test_file

def test_file_write(tmp_path):
    """Test writing file content"""
    file_path = str(tmp_path / "output.py")
    content = "print('test')"
    result = FileManager.write_file(file_path, content)
    
    assert isinstance(result, FileContext)
    assert result.error is None
    assert os.path.exists(file_path)
    with open(file_path) as f:
        assert f.read() == content

def test_line_numbering(test_file):
    """Test line numbering functionality"""
    editor = FileEditor()
    with open(test_file) as f:
        content = f.read()
    
    numbered = editor._number_lines(content)
    lines = numbered.splitlines()
    
    assert len(lines) > 0
    assert all(line.startswith("   ") for line in lines)  # Check padding
    assert all("|" in line for line in lines)  # Check separator
    assert lines[0].startswith("   1 |")  # Check first line number

def test_apply_line_edits(test_file):
    """Test applying line-specific edits"""
    editor = FileEditor()
    original = "line 1\nline 2\nline 3"
    edits = [(2, "modified line 2")]
    
    new_content, changes = editor._apply_line_edits(original, edits)
    
    assert "modified line 2" in new_content
    assert len(changes) == 1
    assert "Line 2" in changes[0]
    assert "line 2" in changes[0]
    assert "modified line 2" in changes[0]

def test_file_edit(agent, test_file):
    """Test editing file content"""
    instruction = "add a docstring to the main function"
    result = agent.forward(f"edit {test_file} {instruction}")
    
    assert isinstance(result, FileContext)
    assert result.error is None
    assert '"""' in result.content  # Should have added docstring
    assert len(result.changes) > 0
    assert any("Line" in change for change in result.changes)  # Verify line number in changes

def test_multiple_line_edits(test_file):
    """Test multiple line edits at once"""
    editor = FileEditor()
    content = "line 1\nline 2\nline 3\nline 4"
    edits = [
        (1, "modified line 1"),
        (3, "modified line 3")
    ]
    
    new_content, changes = editor._apply_line_edits(content, edits)
    
    assert "modified line 1" in new_content
    assert "modified line 3" in new_content
    assert "line 2" in new_content  # Unchanged line
    assert len(changes) == 2

def test_invalid_file():
    """Test handling non-existent file"""
    result = FileManager.read_file("nonexistent.py")
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
    content = "print('test')"
    result = FileManager.write_file(file_path, content)
    
    assert isinstance(result, FileContext)
    assert result.error is None
    assert os.path.exists(file_path)
    with open(file_path) as f:
        assert f.read() == content
