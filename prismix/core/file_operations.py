import os
from dataclasses import dataclass
from typing import Optional, List, Union, Tuple
import dspy


@dataclass
class FileContext:
    """Context for file operations"""

    filepath: str
    content: str
    changes: List[str]
    error: Optional[str] = None


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


from abc import ABC, abstractmethod


class FileOperations(ABC):
    @abstractmethod
    def read_file(self, filepath: str) -> str:
        pass

    @abstractmethod
    def write_file(self, filepath: str, content: str) -> None:
        pass


class DefaultFileOperations(FileOperations):
    def read_file(self, filepath: str) -> str:
        with open(filepath, "r") as f:
            return f.read()

    def write_file(self, filepath: str, content: str) -> None:
        with open(filepath, "w") as f:
            f.write(content)


class FileManager:
    def __init__(self, file_operations: FileOperations):
        self.file_operations = file_operations

    def read_file(self, filepath: str) -> FileContext:
        try:
            content = self.file_operations.read_file(filepath)
            return FileContext(filepath=filepath, content=content, changes=[])
        except FileNotFoundError:
            return FileContext(
                filepath=filepath, content="", changes=[], error="File does not exist"
            )
        except Exception as e:
            return FileContext(filepath=filepath, content="", changes=[], error=str(e))

    def write_file(self, filepath: str, content: str) -> FileContext:
        try:
            self.file_operations.write_file(filepath, content)
            return FileContext(
                filepath=filepath,
                content=content,
                changes=["File updated successfully"],
            )
        except Exception as e:
            return FileContext(
                filepath=filepath, content=content, changes=[], error=str(e)
            )


class FileEditor:
    """Handles file editing operations"""

    def __init__(self):
        self.edit_generator = dspy.ChainOfThought(FileEdit)

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

        if isinstance(line_edits, str):
            # Parse string format (from LLM)
            edit_lines = line_edits.splitlines()
            for edit in edit_lines:
                try:
                    # Parse "MODE LINE_NUM | NEW_TEXT" format
                    parts = edit.split("|", 1)  # Split on first | only
                    if not parts:
                        continue

                    mode_line = parts[0].strip().split()  # Split on whitespace
                    if len(mode_line) < 2:
                        mode = "REPLACE"  # Default mode
                        line_num = -1  # Initialize to an invalid value
                        if mode_line:
                            try:
                                line_num = int(mode_line[0])
                            except ValueError:
                                pass  # If not a number, keep it as -1
                    else:
                        mode = mode_line[0].upper()
                        try:
                            line_num = int(mode_line[1])
                        except ValueError:
                            line_num = -1  # If not a number, keep it as -1

                    new_text = parts[1].strip() if len(parts) > 1 else ""

                    if line_num != -1:
                        if mode == "REPLACE" and 1 <= line_num <= len(lines):
                            old_text = lines[line_num - 1]
                            lines[line_num - 1] = new_text
                            changes.append(
                                f"Replaced line {line_num}: '{old_text}' -> '{new_text}'"
                            )
                        elif mode == "INSERT" and 1 <= line_num <= len(lines) + 1:
                            lines.insert(line_num - 1, new_text)
                            changes.append(f"inserted '{new_text}'")
                            # Adjust line numbers for subsequent edits after insert
                            for j in range(len(edit_lines)):
                                if j > edit_lines.index(edit):
                                    parts_j = edit_lines[j].split("|", 1)
                                    if len(parts_j) > 0:
                                        mode_line_j = parts_j[0].strip().split()
                                        if len(mode_line_j) >= 2:
                                            try:
                                                line_num_j = int(mode_line_j[1])
                                                if line_num_j >= line_num:
                                                    mode_line_j[1] = str(line_num_j + 1)
                                                    edit_lines[j] = (
                                                        " ".join(mode_line_j)
                                                        + "|"
                                                        + parts_j[1]
                                                    )
                                            except ValueError:
                                                pass
                        elif mode == "DELETE" and 1 <= line_num <= len(lines):
                            old_text = lines.pop(line_num - 1)
                            changes.append(f"deleted '{old_text}'")
                            # Adjust line numbers for subsequent edits after delete
                            for j in range(len(edit_lines)):
                                if j > edit_lines.index(edit):
                                    parts_j = edit_lines[j].split("|", 1)
                                    if len(parts_j) > 0:
                                        mode_line_j = parts_j[0].strip().split()
                                        if len(mode_line_j) >= 2:
                                            try:
                                                line_num_j = int(mode_line_j[1])
                                                if line_num_j > line_num:
                                                    mode_line_j[1] = str(line_num_j - 1)
                                                    edit_lines[j] = (
                                                        " ".join(mode_line_j)
                                                        + "|"
                                                        + parts_j[1]
                                                    )
                                            except ValueError:
                                                pass
                except (ValueError, IndexError) as e:
                    changes.append(
                        f"Failed to apply edit: Invalid line number {line_num}: {str(e)}"
                    )
                    continue
        else:
            # Handle direct mode/line/text tuples (from tests)
            for i, edit in enumerate(line_edits):
                if len(edit) == 2:
                    # Simple line number + text format
                    line_num, new_text = edit
                    mode = "REPLACE"
                else:
                    # Full mode + line + text format
                    mode, line_num, new_text = edit
                mode = mode.upper()
                try:
                    if mode == "REPLACE" and 1 <= line_num <= len(lines):
                        old_text = lines[line_num - 1]
                        lines[line_num - 1] = new_text
                        changes.append(
                            f"Replaced line {line_num}: '{old_text}' -> '{new_text}'"
                        )
                    elif mode == "INSERT" and 1 <= line_num <= len(lines) + 1:
                        lines.insert(line_num - 1, new_text)
                        changes.append(f"Inserted at line {line_num}: '{new_text}'")
                        # Update subsequent line numbers
                        for j in range(i + 1, len(line_edits)):
                            if isinstance(line_edits[j], tuple):
                                if len(line_edits[j]) == 3:
                                    mode_j, num_j, text_j = line_edits[j]
                                    if num_j >= line_num:
                                        line_edits[j] = (mode_j, num_j + 1, text_j)
                                else:
                                    num_j, text_j = line_edits[j]
                                    if num_j >= line_num:
                                        line_edits[j] = (num_j + 1, text_j)
                    elif mode == "DELETE" and 1 <= line_num <= len(lines):
                        old_text = lines.pop(line_num - 1)
                        changes.append(f"Deleted line {line_num}: '{old_text}'")
                        # Update subsequent line numbers
                        for j in range(i + 1, len(line_edits)):
                            if isinstance(line_edits[j], tuple):
                                if len(line_edits[j]) == 3:
                                    mode_j, num_j, text_j = line_edits[j]
                                    if num_j > line_num:
                                        line_edits[j] = (mode_j, num_j - 1, text_j)
                                else:
                                    num_j, text_j = line_edits[j]
                                    if num_j > line_num:
                                        line_edits[j] = (num_j - 1, text_j)
                except (ValueError, IndexError) as e:
                    changes.append(
                        f"Failed to apply {mode} at line {line_num}: {str(e)}"
                    )
                    continue

        return "\n".join(lines), changes

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
        result = self.file_manager.write_file(filepath, new_content)  # Use the instance here

        if not result.error:
            result.changes = changes

        return result
