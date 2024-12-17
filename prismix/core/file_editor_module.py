"""
Module for handling file editing operations.
"""

import re
from typing import List, Tuple

from pydantic import ConfigDict

from prismix.core.file_operations import (
    DefaultFileOperations,
    FileContext,
    FileManager,
)


class FileEditorModule:
    """Handles file editing operations."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self):
        self.file_manager = FileManager(file_operations=DefaultFileOperations())

    def read_file(self, filename: str) -> FileContext:
        """Read the content of a file."""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
            return FileContext(
                filepath=filename, content=content, changes=[], error=None
            )
        except FileNotFoundError:
            return FileContext(
                filepath=filename, content="", changes=[], error="File does not exist"
            )

    def write_file(self, filename: str, content: str) -> FileContext:
        """Write content to a file."""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            return FileContext(
                filepath=filename,
                content=content,
                changes=["File updated successfully"],
                error=None,
            )
        except FileNotFoundError:
            return FileContext(
                filepath=filename, content="", changes=[], error="File does not exist"
            )
        except PermissionError as e:
            return FileContext(
                filepath=filename,
                content="",
                changes=[],
                error=f"Permission error: {e}",
            )
        except (PermissionError, IOError) as e:
            return FileContext(
                filepath=filename, content="", changes=[], error=f"Error: {e}"
            )

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
        """Apply a single replacement to the content."""
        return content.replace(search_pattern, replacement_code)

    def apply_replacements(self, content: str, instruction: str) -> FileContext:
        """Apply multiple replacements based on the instruction."""
        changes: List[Tuple[str, str]] = []
        try:
            # Use regex to find all replacement instructions
            matches = re.findall(r"Replace\s+'([^']*)'\s+with\s+'([^']*)'", instruction)
            for search_pattern, replacement_code in matches:
                if search_pattern in content:
                    original_content = content
                    content = content.replace(search_pattern, replacement_code)
                    changes.append(
                        (search_pattern, replacement_code)
                    )  # Store the changes

                    if original_content == content:
                        print(
                            f"No change was made for pattern: '{search_pattern}' "
                            f"with replacement: '{replacement_code}'"
                        )

        except (re.error, IndexError) as e:
            return FileContext(
                filepath="",
                content=content,
                error=f"Error applying replacements: {e}",
            )

        if not changes:
            return FileContext(filepath="", content=content, changes=[])

        # Convert changes from tuples to strings
        changes_str = [f"Replaced '{old}' with '{new}'" for old, new in changes]

        return FileContext(
            filepath="", content=content, changes=changes_str, error=None
        )

    def forward(self, context: str, instruction: str) -> FileContext:
        """Apply the given instruction to the file content."""
        # Parse the context to get the file content
        file_content = context.split("Content: ")[1]

        # Parse the instruction to get the replacements
        replacements = self.parse_instructions(instruction)

        # Apply each replacement to the file content
        for search_pattern, replacement_code in replacements:
            file_content = self.apply_single_replacement(
                file_content, search_pattern, replacement_code
            )

        # Convert changes from tuples to strings
        changes_str = [f"Replaced '{old}' with '{new}'" for old, new in replacements]

        # Return the updated file content
        return FileContext(
            filepath="", content=file_content, changes=changes_str, error=None
        )

    def _parse_context(self, context: str) -> Tuple[str, str]:
        """Parses the context to extract the file path and content."""
        file_path = context.split(" ")[0]
        content = context.split("Content: ")[1] if "Content: " in context else ""
        return file_path, content

    def _apply_instructions(self, content: str, instruction: str) -> str:
        """Applies the instructions to the content."""
        replacements = self.parse_instructions(instruction)
        for search_pattern, replacement_code in replacements:
            content = self.apply_single_replacement(
                content, search_pattern, replacement_code
            )
        return content
