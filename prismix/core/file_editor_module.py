import dspy
from prismix.core.file_operations import FileManager
from prismix.core.signatures import FileEdit

class FileEditorModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.file_edit_predictor = dspy.Predict(FileEdit)

    def forward(self, filepath: str, search_pattern: str, replacement_code: str) -> str:
        """Edits a file and returns the updated content."""
        self.file_edit_predictor(
            filepath=filepath,
            search_pattern=search_pattern,
            replacement_code=replacement_code
        )
        
        file_manager = FileManager()
        file_context = file_manager.read_file(filepath)
        if file_context.error:
            return f"Error reading file: {file_context.error}"
        
        updated_content = file_context.content.replace(search_pattern, replacement_code)
        
        file_context = file_manager.write_file(filepath, updated_content)
        if file_context.error:
            return f"Error writing file: {file_context.error}"
        
        return updated_content
