import dspy
from prismix.core.file_operations import FileManager
from prismix.core.signatures import FileEdit

class FileEditorModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.file_edit_predictor = dspy.Predict(FileEdit)

    def forward(self, context: str, instruction: str, inputs: str) -> FileEdit:
        """Edits a file based on context, instruction, and inputs, and returns the FileEdit signature."""
        result = self.file_edit_predictor(
            context=context,
            instruction=instruction,
            inputs=inputs
        )
        
        filename = result.filename
        search_pattern = result.search
        replacement_code = result.replace
        
        file_manager = FileManager()
        file_context = file_manager.read_file(filename)
        if file_context.error:
            result.error = f"Error reading file: {file_context.error}"
            return result
        
        updated_content = file_context.content.replace(search_pattern, replacement_code)
        
        file_context = file_manager.write_file(filename, updated_content)
        if file_context.error:
            result.error = f"Error writing file: {file_context.error}"
            return result
        
        result.content = updated_content
        return result
