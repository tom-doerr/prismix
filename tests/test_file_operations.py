import os
import pytest
from prismix.core.iterative_programmer import setup_agent
from prismix.core.file_operations import FileContext, FileManager

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

def test_file_edit(agent, test_file):
    """Test editing file content"""
    instruction = "add a docstring to the main function"
    result = agent.forward(f"edit {test_file} {instruction}")
    
    assert isinstance(result, FileContext)
    assert result.error is None
    assert '"""' in result.content  # Should have added docstring
    assert len(result.changes) > 0

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
