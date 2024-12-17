"""
Module for handling file editing operations.
"""

import dspy
import re
import logging
from typing import List, Tuple
from prismix.core.file_operations import FileManager, FileContext, DefaultFileOperations
from prismix.core.signatures import FileEdit


class FileEditorModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.file_edit_predictor = dspy.Predict(FileEdit)
        logging.basicConfig(level=logging.INFO)

    def read_file(self, filename: str) -> FileContext:
        """Reads the file and returns its content."""
        file_manager = FileManager(file_operations=DefaultFileOperations())
        try:
            return file_manager.read_file(filename)
        except FileNotFoundError:
            return FileContext(
                filepath=filename, content="", changes=[], error="File does not exist"
            )

    def apply_replacements(self, content: str, instruction: str) -> str:
        """Applies multiple replacements based on the instruction."""
        replacements = self.parse_instructions(instruction)
        for search_pattern, replacement_code in replacements:
            content = content.replace(search_pattern, replacement_code)
        return content

    def apply_single_replacement(
        self, content: str, search_pattern: str, replacement_code: str
    ) -> str:
        """Applies a single replacement to the content."""
        return content.replace(search_pattern, replacement_code)

    def parse_instructions(self, instruction: str) -> List[Tuple[str, str]]:
        """Parses the instruction string and returns a list of replacement pairs."""
        replacements = instruction.split(" and ")
        return [
            (
                part.split(" with ")[0].strip("'"),
                part.split(" with ")[1].strip("'"),
            )
            for part in replacements
            if "Replace" in part and len(part.split(" with ")) == 2
        ]

    def write_file(self, filename: str, content: str) -> FileContext:
        """Writes the updated content back to the file."""
        file_manager = FileManager(file_operations=DefaultFileOperations())
        return file_manager.write_file(filename, content)

    def forward(self, context: str, instruction: str) -> FileContext:
        """Edit the file based on the context and instruction."""
        # Extract filepath from context
        filepath = ""
        content = ""
        if "File: " in context:
            try:
                filepath = context.split("File: ")[1].split("\n")[0].strip()
            except IndexError:
                pass
        if "Content: " in context:
            try:
                content = context.split("Content: ")[1].strip()
            except IndexError:
                pass

        # Apply replacements
        updated_content = self.apply_replacements(content, instruction)

        # Write the updated content back to the file
        return self.write_file(filepath, updated_content)
from prismix.core.file_operations import FileManager, FileContext, DefaultFileOperations
import logging
