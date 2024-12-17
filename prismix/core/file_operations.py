"""
Module for handling file operations and editing.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Union

import dspy
from pydantic import BaseModel, ConfigDict


class FileContext(BaseModel):
    """Context for file operations"""

    filepath: str
    content: str
    changes: List[str]
    error: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class FileEdit(dspy.Signature):
    """Analyze file and propose line-by-line edits"""

    filepath = dspy.InputField(desc="Path to the file")
    numbered_content = dspy.InputField(desc="Current file content with line numbers")
    instruction = dspy.InputField(desc="Edit instruction")
    line_edits = dspy.OutputField(
        desc="""List of edits in format: 'MODE LINE_NUM | NEW_TEXT' where:
    - MODE is REPLACE/INSERT/DELETE
    - LINE_NUM is the target line number
    - NEW_TEXT is the new content, maintaining proper indentation
    
    Examples:
    'REPLACE 5 |     def hello():  # 4 spaces indent'
    'INSERT 2 |         return x + y  # 8 spaces indent'
    'DELETE 3 |'
    
    Rules:
    1. Maintain consistent indentation with surrounding code
    2. Align with the indentation of the target line or previous line
    3. Keep proper spacing around operators and after commas
    4. Include proper line endings and empty lines where needed"""
    )


class FileOperations(ABC):
    """Abstract base class for file operations."""

    @abstractmethod
    def read_file(self, filepath: str) -> str:
        """Read the content of a file."""

    @abstractmethod
    def write_file(self, filepath: str, content: str) -> None:
        """Write content to a file."""


class DefaultFileOperations(FileOperations):
    """Default implementation of file operations."""

    def read_file(self, filepath: str) -> str:
        """Read the content of a file."""
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def write_file(self, filepath: str, content: str) -> None:
        """Write content to a file."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)


class FileManager:
    """Manages file operations using a provided FileOperations implementation."""

    def __init__(self, file_operations: FileOperations):
        """Initialize the FileManager with a FileOperations instance."""
        self.file_operations = file_operations

    def read_file(self, filepath: str) -> FileContext:
        """Read the content of a file and return a FileContext."""
        try:
            content = self.file_operations.read_file(filepath)
            return FileContext(filepath=filepath, content=content, changes=[])
        except FileNotFoundError:
            return FileContext(
                filepath=filepath, content="", changes=[], error="File does not exist"
            )
        except PermissionError as e:
            return FileContext(
                filepath=filepath,
                content="",
                changes=[],
                error=f"Error reading file: {str(e)}",
            )

    def write_file(self, filepath: str, content: str) -> FileContext:
        """Write content to a file and return a FileContext."""
        try:
            self.file_operations.write_file(filepath, content)
            return FileContext(
                filepath=filepath,
                content=content,
                changes=["File updated successfully"],
            )
        except PermissionError as e:
            return FileContext(
                filepath=filepath, content=content, changes=[], error=str(e)
            )
        except IOError as e:
            return FileContext(
                filepath=filepath, content=content, changes=[], error=str(e)
            )


class FileEditor:
    """Handles file editing operations"""

    def __init__(self):
        self.edit_generator = dspy.ChainOfThought(FileEdit)
        self.file_manager = FileManager(DefaultFileOperations())

    def _number_lines(self, content: str) -> str:
        """Add line numbers to content"""
        lines = content.splitlines()
        return "\n".join(f"{i+1:4d} | {line}" for i, line in enumerate(lines))

    def _apply_line_edits(
        self, content: str, line_edits: Union[str, List[Tuple[str, int, str]]]
    ) -> tuple[str, list[str]]:
        """Apply line edits to content"""
        lines = content.splitlines()
        changes = []

        def apply_edit(mode, line_num, new_text):
            """Helper function to apply a single edit."""
            if mode == "REPLACE" and 1 <= line_num <= len(lines):
                old_text = lines[line_num - 1]
                lines[line_num - 1] = new_text
                changes.append(
                    f"Replaced line {line_num}: '{old_text}' -> '{new_text}'"
                )
            elif mode == "INSERT" and 1 <= line_num <= len(lines) + 1:
                lines.insert(line_num - 1, new_text)
                changes.append(f"Inserted at line {line_num}: '{new_text}'")
            elif mode == "DELETE" and 1 <= line_num <= len(lines):
                old_text = lines.pop(line_num - 1)
                changes.append(f"Deleted line {line_num}: '{old_text}'")

        if isinstance(line_edits, str):
            for edit in line_edits.splitlines():
                try:
                    parts = edit.split("|", 1)
                    if not parts:
                        continue

                    mode_line = parts[0].strip().split()
                    if len(mode_line) < 2:
                        mode = "REPLACE"
                        line_num = -1
                        if mode_line:
                            try:
                                line_num = int(mode_line[0])
                            except ValueError:
                                pass
                    else:
                        mode = mode_line[0].upper()
                        try:
                            line_num = int(mode_line[1])
                        except ValueError:
                            line_num = -1

                    new_text = parts[1].strip() if len(parts) > 1 else ""

                    if line_num != -1:
                        apply_edit(mode, line_num, new_text)
                except (ValueError, IndexError) as e:
                    changes.append(
                        f"Failed to apply edit: Invalid line number {line_num}: {str(e)}"
                    )
                    continue
        else:
            for edit in line_edits:
                if len(edit) == 2:
                    line_num, new_text = edit
                    mode = "REPLACE"
                else:
                    mode, line_num, new_text = edit
                mode = mode.upper()
                try:
                    apply_edit(mode, line_num, new_text)
                except (ValueError, IndexError) as e:
                    changes.append(
                        f"Failed to apply {mode} at line {line_num}: {str(e)}"
                    )
                    continue

        return "\n".join(lines), changes

    def apply_line_edits(
        self, content: str, line_edits: Union[str, List[Tuple[str, int, str]]]
    ) -> tuple[str, list[str]]:
        """Public method to apply line edits to content"""
        return self._apply_line_edits(content, line_edits)

    def edit_file(self, filepath: str, instruction: str) -> FileContext:
        """Edit file based on instruction"""
        # Read current file
        context = self.file_manager.read_file(filepath)  # Use the instance here
        if context.error:
            return context

        # Generate numbered content
        numbered_content = self._number_lines(context.content)

        # Generate edits
        edit_result = self.edit_generator(
            filepath=filepath,
            numbered_content=numbered_content,
            instruction=instruction,
        )

        # Apply line edits
        new_content, changes = self._apply_line_edits(
            context.content, edit_result.line_edits
        )

        # Write updated content
        result = self.file_manager.write_file(
            filepath, new_content
        )  # Use the instance here

        if not result.error:
            result.changes = changes

        return result
