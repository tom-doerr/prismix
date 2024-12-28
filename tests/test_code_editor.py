import pytest
from code_editor import CodeEditor
from qdrant_retriever import QdrantRetriever
import dspy
import os
from unittest.mock import MagicMock

@pytest.fixture
def setup_code_editor(tmp_path):
    # Setup test environment
    llm = dspy.LM(model="deepseek/deepseek-chat", max_tokens=200, cache=False)
    dspy.settings.configure(lm=llm)
    
    # Use temporary directory for Qdrant data
    qdrant_path = tmp_path / "qdrant_data"
    # Use temporary directory for Qdrant data
    qdrant_path = tmp_path / "qdrant_data"
    retriever = QdrantRetriever(collection_name="test_collection", path=str(qdrant_path))
    predictor = dspy.ChainOfThought("instruction, context -> edit_instructions")
    editor = CodeEditor(retriever, predictor)
    
    # Create test file in temporary directory
    test_file = tmp_path / "test_file.py"
    with open(test_file, "w") as f:
        f.write("def hello():\n    print('hello')\n")
    
    # Add test file to Qdrant
    retriever.add_files(include_glob=str(test_file))
    
    yield editor, test_file
    
    # Cleanup
    if test_file.exists():
        test_file.unlink()
    backup_file = test_file.with_suffix(".py.bak")
    if backup_file.exists():
        backup_file.unlink()

def test_add_line_numbers():
    editor = CodeEditor(MagicMock(), MagicMock())
    content = "line1\nline2\nline3"
    expected = "   1 line1\n   2 line2\n   3 line3"
    assert editor.add_line_numbers(content) == expected

def test_remove_line_numbers():
    editor = CodeEditor(MagicMock(), MagicMock())
    numbered_content = "   1 line1\n   2 line2\n   3 line3"
    expected = "line1\nline2\nline3"
    result = editor.remove_line_numbers(numbered_content)
    assert result == expected, f"Expected '{expected}' but got '{result}'"

def test_load_code_files(tmp_path):
    editor = CodeEditor(MagicMock(), MagicMock())
    test_file = tmp_path / "test.py"
    test_file.write_text("test content")
    
    files = editor.load_code_files([str(test_file)])
    assert len(files) == 1
    assert files[0].filepath == str(test_file)
    assert "test content" in files[0].filecontent

def test_load_code_files_missing(tmp_path, capsys):
    editor = CodeEditor(MagicMock(), MagicMock())
    files = editor.load_code_files([str(tmp_path / "nonexistent.py")])
    assert len(files) == 0
    assert "Error: File not found" in capsys.readouterr().out

def test_validate_edit_instruction():
    editor = CodeEditor(MagicMock(), MagicMock())
    class MockInstruction:
        search_text = "find"
        replacement_text = "replace"
    assert editor.validate_edit_instruction(MockInstruction()) is True

def test_validate_edit_instruction_invalid():
    editor = CodeEditor(MagicMock(), MagicMock())
    class MockInstruction:
        pass
    assert editor.validate_edit_instruction(MockInstruction()) is False

def test_apply_edit_instruction():
    editor = CodeEditor(MagicMock(), MagicMock())
    class MockInstruction:
        search_text = "hello"
        replacement_text = "hi"
    content = "print('hello')"
    result = editor.apply_edit_instruction(content, MockInstruction())
    assert result == "print('hi')"

def test_backup_and_write_file(tmp_path):
    editor = CodeEditor(MagicMock(), MagicMock())
    test_file = tmp_path / "test.py"
    test_file.write_text("original")
    
    assert editor.backup_and_write_file(str(test_file), "original", "new") is True
    assert test_file.read_text() == "new"
    assert (tmp_path / "test.py.bak").read_text() == "original"

def test_backup_and_write_file_line_count_mismatch(tmp_path, capsys):
    editor = CodeEditor(MagicMock(), MagicMock())
    test_file = tmp_path / "test.py"
    test_file.write_text("line1\nline2")
    
    assert editor.backup_and_write_file(str(test_file), "line1\nline2", "single_line") is False
    assert "Warning: Line count mismatch" in capsys.readouterr().out

def test_process_edit_instruction(setup_code_editor, tmp_path):
    editor, test_file = setup_code_editor
    instruction = "Change 'hello' to 'goodbye' in the print statement"
    
    # Mock predictor response
    class MockPrediction(dspy.Prediction):
        def __init__(self):
            super().__init__()
            self.edit_instructions = '{"edit_instructions": [{"filepath": "' + str(test_file) + '", "search_text": "hello", "replacement_text": "goodbye"}]}'
            self.search_query = ""
            self.reasoning = "Mock reasoning"
    
    editor.predictor = MagicMock(return_value=MockPrediction())
    
    # Test dry run
    assert editor.process_edit_instruction(instruction, dry_run=True)
    
    # Test actual edit
    assert editor.process_edit_instruction(instruction, dry_run=False)
    assert "print('goodbye')" in test_file.read_text()

def test_process_edit_instruction_invalid_json(setup_code_editor):
    editor, _ = setup_code_editor
    instruction = "Change something"
    
    # Mock predictor with invalid JSON
    class MockPrediction:
        edit_instructions = "invalid json"
        search_query = ""
    
    editor.predictor = MagicMock(return_value=MockPrediction())
    
    with pytest.raises(dspy.DSPyAssertionError):
        editor.process_edit_instruction(instruction)

def test_process_edit_instruction_missing_files(setup_code_editor, tmp_path):
    editor, test_file = setup_code_editor
    instruction = "Change something"
    
    # Mock predictor response with non-existent file
    class MockPrediction:
        edit_instructions = '{"edit_instructions": [{"filepath": "nonexistent.py", "search_text": "a", "replacement_text": "b"}]}'
        search_query = ""
    
    editor.predictor = MagicMock(return_value=MockPrediction())
    
    # Should raise FileNotFoundError when no valid files are found
    with pytest.raises(FileNotFoundError):
        editor.process_edit_instruction(instruction)

def test_process_edit_instruction_empty_instruction(setup_code_editor):
    editor, _ = setup_code_editor
    with pytest.raises(ValueError):
        editor.process_edit_instruction("")

def test_process_edit_instruction_file_not_found(setup_code_editor, tmp_path):
    editor, test_file = setup_code_editor
    test_file.unlink()
    with pytest.raises(FileNotFoundError):
        editor.process_edit_instruction("Change something")
