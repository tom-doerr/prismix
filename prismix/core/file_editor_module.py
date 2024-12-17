"""
Module for handling file editing operations.
"""

import re
from importlib import resources
from typing import List, Tuple

from pydantic import ConfigDict

from prismix.core.file_operations import (
    DefaultFileOperations,
    FileContext,
    FileManager,
)


class FileEditorModule:
    """Handles file editing operations."""

    def __init__(self):
        self.file_manager = FileManager(file_operations=DefaultFileOperations())
        self.model_config = ConfigDict(arbitrary_types_allowed=True)

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
        self,
        content: str,
        search_pattern: str,
        replacement_code: str,
    ) -> str:
        """Apply a single replacement in the content."""
        with resources.files("litellm.llms.tokenizers").joinpath(
            "anthropic_tokenizer.json"
        ).open():
            updated_content = content.replace(search_pattern, replacement_code)

        return updated_content

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

        return FileContext(filepath="", content=content, changes=changes_str, error=None)

    def forward(self, context: str, instruction: str) -> FileContext:
        """Edit the file based on the context and instruction."""
        content = context.split("Content: ")[1] if "Content: " in context else context
        updated_content = self.apply_replacements(content, instruction)
        return FileContext(content=updated_content.content, filepath="test_file.py", changes=updated_content.changes, error=updated_content.error)
