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
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def hello():\n    print('hello')\n")
        temp_file_path = f.name
    yield temp_file_path
    import os
    os.remove(temp_file_path)

def test_file_edit_module(file_editor_module, temp_file):
    # Test successful file edit
    result = file_editor_module.forward(
        context="Edit the hello function to print 'hi' instead of 'hello'.",
        instruction="Replace 'print('hello')' with 'print('hi')'.",
        inputs="def hello():\n    print('hello')\n"
    )
    
    file_manager = FileManager()
    file_context = file_manager.read_file(result.filename)
    assert file_context.content == "def hello():\n    print('hi')\n"
    assert result.error is None

def test_file_edit_module_no_change(file_editor_module, temp_file):
    # Test file edit with no change
    result = file_editor_module.forward(
        context="Do not change the hello function.",
        instruction="Do not change 'print('hello')'.",
        inputs="def hello():\n    print('hello')\n"
    )
    
    file_manager = FileManager()
    file_context = file_manager.read_file(result.filename)
    assert file_context.content == "def hello():\n    print('hello')\n"
    assert result.error is None

def test_file_edit_module_file_not_found(file_editor_module):
    # Test file edit with file not found
    result = file_editor_module.forward(
        context="Edit a non-existent file.",
        instruction="Replace 'print('hello')' with 'print('hi')'.",
        inputs="def hello():\n    print('hello')\n"
    )
    assert "Error reading file" in result.error
