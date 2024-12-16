import dspy
import re
from typing import List, Tuple
from prismix.core.file_operations import FileManager, FileContext
from prismix.core.signatures import FileEdit


import subprocess
import logging
import tempfile
import os

class FileEditorModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.file_edit_predictor = dspy.Predict(FileEdit)
        logging.basicConfig(level=logging.INFO)

    def read_file(self, filename: str) -> FileContext:
        """Reads the file and returns its content."""
        file_manager = FileManager()
        try:
            return file_manager.read_file(filename)
        except FileNotFoundError:
            return FileContext(
                filepath=filename,
                content="",
                changes=[],
                error="File does not exist"
            )

    def apply_edit(self, content: str, search_pattern: str, replacement_code: str) -> str:
        """Applies the edit to the file content."""
        return content.replace(search_pattern, replacement_code)

    def parse_instructions(self, instruction: str) -> List[Tuple[str, str]]:
        """Parses the instruction string and returns a list of replacement pairs."""
        replacements = instruction.split(" and ")
        parsed_replacements = []
        for replacement in replacements:
            if "Replace" in replacement:
                parts = replacement.split(" with ")
                if len(parts) == 2:
                    search_pattern = parts[0].replace("Replace ", "").strip("'")
                    replacement_code = parts[1].strip("'")
                    parsed_replacements.append((search_pattern, replacement_code))
        return parsed_replacements

    def apply_single_replacement(self, content: str, search_pattern: str, replacement_code: str) -> str:
        """Applies a single replacement to the content."""
        if search_pattern.startswith("def "):
            # Replace the entire function definition
            content = re.sub(
                r"^(\s*)" + re.escape(search_pattern) + r"[\s\S]*?^(\s*)",
                r"\1" + replacement_code + "\n",
                content,
                flags=re.MULTILINE
            )
        else:
            content = self.apply_edit(content, search_pattern, replacement_code)
        return content

    def apply_replacements(self, content: str, instruction: str) -> str:
        """Applies multiple replacements based on the instruction."""
        replacements = self.parse_instructions(instruction)
        for search_pattern, replacement_code in replacements:
            content = self.apply_single_replacement(content, search_pattern, replacement_code)
        return content

    def write_file(self, filename: str, content: str) -> FileContext:
        """Writes the updated content back to the file."""
        file_manager = FileManager()
        return file_manager.write_file(filename, content)

    def _run_lint(self, content: str) -> None:
        """Runs ruff linter on the given content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            result = subprocess.run(
                ["ruff", "check", tmp_file_path],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode != 0:
                logging.error(f"Linting failed:\n{result.stdout}\n{result.stderr}")
                assert False, f"Linting failed:\n{result.stdout}\n{result.stderr}"
            else:
                logging.info("Linting passed.")
        finally:
            os.remove(tmp_file_path)


    def forward(self, context: str, instruction: str) -> FileEdit:
        """Edits a file based on context, instruction, and returns the FileEdit signature."""
        logging.info(f"Received context: {context}")
        logging.info(f"Received instruction: {instruction}")

        filename = context.split(" ")[0]

        result = self.file_edit_predictor(
            filename=filename,
            context=context,
            instruction=instruction,
        )

        search_pattern = result.search
        replacement_code = result.replacement

        logging.info(f"Predicted filename: {filename}")
        logging.info(f"Predicted search pattern: {search_pattern}")
        logging.info(f"Predicted replacement code: {replacement_code}")

        file_context = self.read_file(filename)
        if file_context.error:
            result.error = f"Error reading file: {file_context.error}"
            logging.error(f"Error reading file: {file_context.error}")
            return result

        logging.info(f"File content before update: {file_context.content}")

        # Handle "Do not change" instruction
        if "Do not change" in instruction:
            updated_content = file_context.content
        else:
            # Handle multiple replacements
            updated_content = self.apply_replacements(file_context.content, instruction)

        logging.info(f"File content after update: {updated_content}")
        logging.info(f"Applied replacements: {instruction}")

        # Run linting
        self._run_lint(updated_content)

        write_result = self.write_file(filename, updated_content)
        if write_result.error:
            result.error = f"Error writing file: {write_result.error}"
            logging.error(f"Error writing file: {write_result.error}")
            return result

        result.content = updated_content
        logging.info(f"File edit successful. Updated content: {updated_content}")
        result.content = updated_content
        logging.info(f"File edit successful. Updated content: {updated_content}")
        
        # Return the FileEdit object
        return result
