import dspy
from prismix.core.file_operations import FileManager
from prismix.core.signatures import FileEdit


import logging

class FileEditorModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.file_edit_predictor = dspy.Predict(FileEdit)
        logging.basicConfig(level=logging.INFO)

    def forward(self, context: str, instruction: str) -> FileEdit:
        """Edits a file based on context, instruction, and returns the FileEdit signature."""
        logging.info(f"Received context: {context}")
        logging.info(f"Received instruction: {instruction}")

        result = self.file_edit_predictor(
            context=context,
            instruction=instruction,
        )

        filename = result.filename
        search_pattern = result.search
        replacement_code = result.replacement

        logging.info(f"Predicted filename: {filename}")
        logging.info(f"Predicted search pattern: {search_pattern}")
        logging.info(f"Predicted replacement code: {replacement_code}")

        file_manager = FileManager()
        file_context = file_manager.read_file(filename)
        if file_context.error:
            result.error = f"Error reading file: {file_context.error}"
            logging.error(f"Error reading file: {file_context.error}")
            return result

        logging.info(f"File content before update: {file_context.content}")

        updated_content = file_context.content.replace(search_pattern, replacement_code)

        logging.info(f"File content after update: {updated_content}")

        file_context = file_manager.write_file(filename, updated_content)
        if file_context.error:
            result.error = f"Error writing file: {file_context.error}"
            logging.error(f"Error writing file: {file_context.error}")
            return result

        result.content = updated_content
        logging.info(f"File edit successful. Updated content: {updated_content}")
        
        # Return the updated content directly
        return updated_content
