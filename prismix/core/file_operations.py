import os
from dataclasses import dataclass
from typing import Optional, List
import dspy

@dataclass
class FileContext:
    """Context for file operations"""
    filepath: str
    content: str
    changes: List[str]
    error: Optional[str] = None

class FileEdit(dspy.Signature):
    """Analyze file and propose edits"""
    filepath = dspy.InputField(desc="Path to the file")
    content = dspy.InputField(desc="Current file content")
    instruction = dspy.InputField(desc="Edit instruction")
    changes = dspy.OutputField(desc="List of specific changes to make")
    updated_content = dspy.OutputField(desc="Complete updated file content")

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

    def edit_file(self, filepath: str, instruction: str) -> FileContext:
        """Edit file based on instruction"""
        # Read current file
        context = FileManager.read_file(filepath)
        if context.error:
            return context
        
        # Generate edits
        edit_result = self.edit_generator(
            filepath=filepath,
            content=context.content,
            instruction=instruction
        )
        
        # Apply changes
        result = FileManager.write_file(
            filepath=filepath,
            content=edit_result.updated_content
        )
        
        if not result.error:
            result.changes = edit_result.changes
        
        return result
