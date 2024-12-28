import pytest
from code_editor import CodeEditor
from qdrant_retriever import QdrantRetriever
import dspy
import os

@pytest.fixture
def setup_code_editor(tmp_path):
    # Setup test environment
    llm = dspy.LM(model="deepseek/deepseek-chat", max_tokens=200, cache=False)
    dspy.settings.configure(lm=llm)
    
    # Use temporary directory for Qdrant data
    qdrant_path = tmp_path / "qdrant_data"
    retriever = QdrantRetriever(collection_name="test_collection")
    predictor = dspy.ChainOfThought("instruction, context -> edit_instructions")
    editor = CodeEditor(retriever, predictor)
    
    # Create test file in temporary directory
    test_file = tmp_path / "test_file.py"
    with open(test_file, "w") as f:
        f.write("def hello():\n    print('hello')\n")
    
    # Add test file to Qdrant
    retriever.add_files(include_glob=str(test_file))
    
    yield editor
    
    # Cleanup - Qdrant data will be automatically cleaned up with tmp_path
    if test_file.exists():
        test_file.unlink()
    backup_file = test_file.with_suffix(".py.bak")
    if backup_file.exists():
        backup_file.unlink()

def test_basic_edit(setup_code_editor, tmp_path):
    editor = setup_code_editor
    instruction = "Change 'hello' to 'goodbye' in the print statement"
    
    # Test dry run
    assert editor.process_edit_instruction(instruction, dry_run=True)
    
    # Test actual edit
    assert editor.process_edit_instruction(instruction, dry_run=False)
    
    # Verify changes
    test_file = tmp_path / "test_file.py"
    with open(test_file) as f:
        content = f.read()
        assert "print('goodbye')" in content

def test_invalid_instruction(setup_code_editor):
    editor = setup_code_editor
    
    with pytest.raises(ValueError):
        editor.process_edit_instruction("")

def test_file_not_found(setup_code_editor, tmp_path):
    editor = setup_code_editor
    
    # Remove test file
    test_file = tmp_path / "test_file.py"
    if test_file.exists():
        test_file.unlink()
    
    with pytest.raises(FileNotFoundError):
        editor.process_edit_instruction("Change something")
