"""
Module for handling file editing operations.
"""

import os
from typing import List, Tuple
from prismix.core.file_operations import FileManager, FileContext, DefaultFileOperations


class FileEditorModule:
    """Handles file editing operations."""

    def __init__(self):
        self.file_manager = FileManager(file_operations=DefaultFileOperations())

    def read_file(self, filename: str) -> FileContext:
        """Reads the content of the file."""
        return self.file_manager.read_file(filename)

    def write_file(self, filename: str, content: str) -> FileContext:
        """Writes the updated content back to the file."""
        return self.file_manager.write_file(filename, content)

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

    def apply_single_replacement(
        self, content: str, search_pattern: str, replacement_code: str
    ) -> str:
        """Applies a single replacement to the content."""
        return content.replace(search_pattern, replacement_code)

    def apply_replacements(self, content: str, instruction: str) -> FileContext:
        """Applies replacements based on the instruction."""
        replacements = self.parse_instructions(instruction)
        changes = []
        for search_pattern, replacement_code in replacements:
            original_content = content
            content = self.apply_single_replacement(
                content, search_pattern, replacement_code
            )
            if original_content != content:
                changes.append((search_pattern, replacement_code))
        return FileContext(filepath="", content=content, changes=changes, error=None)

    def forward(self, context: str, instruction: str) -> FileContext:
        """Edit the file based on the context and instruction."""
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

        if not content and filepath:
            file_context = self.read_file(filepath)
            if file_context.error:
                return file_context
            content = file_context.content

        # Apply replacements
        file_context = self.apply_replacements(content, instruction)

        # Return a FileContext object with changes
        return FileContext(
            filepath=filepath,
            content=file_context.content,
            changes=file_context.changes,
            error=file_context.error,
        )
