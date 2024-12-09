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
    line_edits = dspy.OutputField(desc="List of line number and replacement text pairs")

class FileManager:
    """Handles file operations"""
    
    @staticmethod
    def read_file(filepath: str) -> FileContext:
        """Read file content safely"""
        try:
            if not os.path.exists(filepath):
                return FileContext(
                    filepath=filepath,
                    content="",
                    changes=[],
                    error="File does not exist"
                )
            
            with open(filepath, 'r') as f:
                content = f.read()
            return FileContext(
                filepath=filepath,
                content=content,
                changes=[]
            )
        except Exception as e:
            return FileContext(
                filepath=filepath,
                content="",
                changes=[],
                error=str(e)
            )

    @staticmethod
    def write_file(filepath: str, content: str) -> FileContext:
        """Write content to file safely"""
        try:
            # Create directories if they don't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w') as f:
                f.write(content)
            return FileContext(
                filepath=filepath,
                content=content,
                changes=["File updated successfully"]
            )
        except Exception as e:
            return FileContext(
                filepath=filepath,
                content=content,
                changes=[],
                error=str(e)
            )

class FileEditor:
    """Handles file editing operations"""
    
    def __init__(self):
        self.edit_generator = dspy.ChainOfThought(FileEdit)

    def _number_lines(self, content: str) -> str:
        """Add line numbers to content"""
        lines = content.splitlines()
        return '\n'.join(f"{i+1:4d} | {line}" for i, line in enumerate(lines))

    def _apply_line_edits(self, content: str, line_edits: Union[str, List[Tuple[int, str]]]) -> tuple[str, list[str]]:
        """Apply line edits to content"""
        lines = content.splitlines()
        changes = []
        
        if isinstance(line_edits, str):
            # Parse string format (from LLM)
            edit_lines = line_edits.splitlines()
            for edit in edit_lines:
                try:
                    # Parse "line_num | new_text" format
                    line_num = int(edit.split('|')[0].strip())
                    new_text = edit.split('|')[1].strip()
                    
                    if 1 <= line_num <= len(lines):
                        old_text = lines[line_num - 1]
                        lines[line_num - 1] = new_text
                        changes.append(f"Line {line_num}: '{old_text}' -> '{new_text}'")
                except (ValueError, IndexError):
                    continue
        else:
            # Handle direct line number/text pairs (from tests)
            for line_num, new_text in line_edits:
                if 1 <= line_num <= len(lines):
                    old_text = lines[line_num - 1]
                    lines[line_num - 1] = new_text
                    changes.append(f"Line {line_num}: '{old_text}' -> '{new_text}'")
        
        return '\n'.join(lines), changes

    def edit_file(self, filepath: str, instruction: str) -> FileContext:
        """Edit file based on instruction"""
        # Read current file
        context = FileManager.read_file(filepath)
        if context.error:
            return context
        
        # Generate numbered content
        numbered_content = self._number_lines(context.content)
        
        # Generate edits
        edit_result = self.edit_generator(
            filepath=filepath,
            numbered_content=numbered_content,
            instruction=instruction
        )
        
        # Apply line edits
        new_content, changes = self._apply_line_edits(
            context.content, 
            edit_result.line_edits
        )
        
        # Write updated content
        result = FileManager.write_file(filepath, new_content)
        
        if not result.error:
            result.changes = changes
        
        return result
