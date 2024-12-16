import pytest
import tempfile
from prismix.core.file_editor_module import FileEditorModule
from prismix.core.file_operations import FileManager

@pytest.fixture
def file_editor_module():
    return FileEditorModule()

@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def hello():\n    print('hello')\n")
        temp_file_path = f.name
    yield temp_file_path
    import os
    os.remove(temp_file_path)

def test_file_edit_module(file_editor_module, temp_file):
    # Test successful file edit
    updated_content = file_editor_module.forward(
        filepath=temp_file,
        search_pattern="print('hello')",
        replacement_code="print('hi')"
    )
    
    file_manager = FileManager()
    file_context = file_manager.read_file(temp_file)
    assert file_context.content == "def hello():\n    print('hi')\n"
    assert "Error" not in updated_content

def test_file_edit_module_no_change(file_editor_module, temp_file):
    # Test file edit with no change
    updated_content = file_editor_module.forward(
        filepath=temp_file,
        search_pattern="print('world')",
        replacement_code="print('hi')"
    )
    
    file_manager = FileManager()
    file_context = file_manager.read_file(temp_file)
    assert file_context.content == "def hello():\n    print('hello')\n"
    assert "Error" not in updated_content

def test_file_edit_module_file_not_found(file_editor_module):
    # Test file edit with file not found
    updated_content = file_editor_module.forward(
        filepath="non_existent_file.py",
        search_pattern="print('hello')",
        replacement_code="print('hi')"
    )
    assert "Error reading file" in updated_content
