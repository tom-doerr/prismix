from prismix.core.file_editor_module import FileEditorModule

def test_apply_replacements():
    editor = FileEditorModule()
    content = "def foo():\n    pass"
    instruction = "Replace 'pass' with 'print(\"hello\")'"
    updated_content = editor.apply_replacements(content, instruction)
    assert updated_content == "def foo():\n    print(\"hello\")"

def test_read_file_existing():
    editor = FileEditorModule()
    # Create a dummy file for testing
    with open("test_file.txt", "w") as f:
        f.write("test content")
    file_context = editor.read_file("test_file.txt")
    assert file_context.content == "test content"
    assert file_context.error is None
    import os
    os.remove("test_file.txt")

def test_read_file_not_existing():
    editor = FileEditorModule()
    file_context = editor.read_file("non_existing_file.txt")
    assert file_context.content == ""
    assert file_context.error == "File does not exist"

def test_write_file():
    editor = FileEditorModule()
    content = "new content"
    file_context = editor.write_file("test_write_file.txt", content)
    assert file_context.content == content
    assert file_context.error is None
    with open("test_write_file.txt", "r") as f:
        file_content = f.read()
    assert file_content == content
    import os
    os.remove("test_write_file.txt")
