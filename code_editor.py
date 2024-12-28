from typing import List, Optional, Dict, Any
import os
import json
from pathlib import Path
from prismix.core.models import SearchReplaceEditInstruction, Context
from qdrant_retriever import QdrantRetriever
import dspy

class EditApplicationError(Exception):
    """Raised when an edit cannot be applied to content."""
    pass

class FileWriteError(Exception):
    """Raised when file operations fail."""
    pass

class CodeEditor:
    """Handles code editing operations using search/replace instructions."""
    
    def __init__(self, retriever: QdrantRetriever, predictor: Any):
        self.retriever = retriever
        self.predictor = predictor

    def _add_line_numbers(self, content: str) -> str:
        """Add line numbers to code content."""
        return "\n".join(f"{i+1:4} {line}" for i, line in enumerate(content.splitlines()))

    def _remove_line_numbers(self, text: str) -> str:
        """Remove line numbers from code content."""
        return "\n".join(line[5:] if len(line) > 5 else line for line in text.splitlines())

    def _load_code_file(self, file_path: str) -> Optional[Dict[str, str]]:
        """Load a single code file with line numbers."""
        try:
            if not Path(file_path).exists():
                print(f"Error: File not found at {file_path}")
                return None
                
            with open(file_path, 'r') as f:
                return {
                    'filepath': file_path,
                    'content': self._add_line_numbers(f.read())
                }
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def _validate_edit(self, instruction: Dict[str, str]) -> bool:
        """Validate that edit instruction has required fields."""
        return all(key in instruction for key in ['filepath', 'search_text', 'replacement_text'])

    def _apply_edit(self, content: str, instruction: Dict[str, str]) -> str:
        """Apply a single edit instruction to content.
        
        Args:
            content: The original file content
            instruction: Dictionary containing filepath, search_text, and replacement_text
            
        Returns:
            str: The modified content
            
        Raises:
            ValueError: If instruction is invalid
            EditApplicationError: If edit cannot be applied
        """
        if not self._validate_edit(instruction):
            raise ValueError(f"Invalid edit instruction: {instruction}")
            
        search_text = instruction['search_text']
        replacement = instruction['replacement_text']
        
        # Handle multi-line replacements
        if '\n' in replacement:
            # Find indentation of first matching line
            lines = content.splitlines()
            indentation = ''
            for line in lines:
                if search_text in line:
                    indentation = line[:len(line) - len(line.lstrip())]
                    break
            
            # Apply indentation to all but first line
            replacement_lines = replacement.splitlines()
            if indentation:
                replacement_lines = [replacement_lines[0]] + [
                    indentation + line for line in replacement_lines[1:]
                ]
            replacement = '\n'.join(replacement_lines)
            
        # Replace all occurrences
        if search_text not in content:
            raise EditApplicationError(f"Search text not found in content: {search_text}")
            
        return content.replace(search_text, replacement)

    def _backup_and_write(self, file_path: str, original: str, new: str) -> bool:
        """Create backup and write new content to file.
        
        Args:
            file_path: Path to the file being edited
            original: Original content for backup
            new: New content to write
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            FileWriteError: If file operations fail
            ValueError: If inputs are invalid
        """
        # Validate inputs
        if not isinstance(file_path, str) or not file_path.strip():
            raise ValueError("File path must be a non-empty string")
            
        if not isinstance(original, str) or not isinstance(new, str):
            raise ValueError("Content must be strings")
        backup_path = f"{file_path}.bak"
        try:
            # Create numbered backup if one already exists
            if Path(backup_path).exists():
                counter = 1
                while Path(f"{backup_path}.{counter}").exists():
                    counter += 1
                backup_path = f"{backup_path}.{counter}"
                
            # Write backup first
            with open(backup_path, 'w') as backup:
                backup.write(original)
                
            # Write new content
            with open(file_path, 'w') as f:
                f.write(new)
                
            print(f"File {file_path} updated. Backup saved to {backup_path}")
            return True
            
        except Exception as e:
            raise FileWriteError(f"Error writing file {file_path}: {e}")

    def process_edit_instruction(self, instruction: str, dry_run: bool = False) -> bool:
        """Process an edit instruction.
        
        Args:
            instruction: The edit instruction to process
            dry_run: If True, only preview changes without saving
            
        Returns:
            bool: True if edits were successfully applied
            
        Raises:
            ValueError: If instruction is invalid
            FileNotFoundError: If no relevant files found
            RuntimeError: If predictor fails to generate valid edits
            EditApplicationError: If edits cannot be applied
            FileWriteError: If file operations fail
        """
        # Validate input
        if not isinstance(instruction, str) or not instruction.strip():
            raise ValueError("Instruction must be a non-empty string")
            
        if not isinstance(dry_run, bool):
            raise ValueError("dry_run must be a boolean")
        if not instruction or not instruction.strip():
            raise ValueError("Instruction cannot be empty")
            
        try:
            # Search for relevant files
            search_query = instruction.split(" to ")[0].replace("change ", "").strip()
            print(f"Searching for files containing: '{search_query}'")
            
            search_results = self.retriever.retrieve(query=search_query, top_k=3)
            file_paths = list(set(result[0] for result in search_results))
            
            if not file_paths:
                raise FileNotFoundError("No relevant files found")
                
            print(f"Found {len(file_paths)} relevant files:")
            for i, path in enumerate(file_paths):
                print(f"{i+1}. {path}")
                
            # Load files with line numbers
            code_files = [f for f in (self._load_code_file(p) for p in file_paths) if f]
            if not code_files:
                raise FileNotFoundError("No valid code files found")

            # Get context and predict edits
            retrieved_results = self.retriever.retrieve(query=instruction, top_k=3)
            retrieved_context = "\n".join(f"File: {r[0]}\nCode:\n{r[1]}" for r in retrieved_results)
            context = Context(retrieved_context=retrieved_context, online_search="")
            
            response = self.predictor(instruction=instruction, context=context)
            
            if not hasattr(response, 'edit_instructions'):
                raise RuntimeError("Invalid response format from predictor - missing edit_instructions")
                
            try:
                # Parse and validate edit instructions
                edit_data = json.loads(response.edit_instructions)
                if not isinstance(edit_data, list):
                    raise ValueError("Edit instructions must be a list")
                    
                edits = []
                for instr in edit_data:
                    try:
                        # Validate each instruction
                        if not isinstance(instr, dict):
                            raise ValueError("Each instruction must be a dictionary")
                            
                        if not all(k in instr for k in ['filepath', 'search_text', 'replacement_text']):
                            raise ValueError("Missing required fields in instruction")
                            
                        # Create and validate the instruction
                        edit = SearchReplaceEditInstruction(**instr)
                        if edit.filepath not in [f['filepath'] for f in code_files]:
                            raise ValueError(f"File {edit.filepath} not found in relevant files")
                            
                        edits.append(edit)
                        
                    except Exception as e:
                        print(f"Invalid edit instruction: {e}\nInstruction: {instr}")
                        continue
                        
                if not edits:
                    raise ValueError("No valid edit instructions found after validation")
                    
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in edit instructions: {e}")

            # Apply edits
            success_count = 0
            failed_files = []
            
            for edit in edits:
                file = next((f for f in code_files if f['filepath'] == edit.filepath), None)
                if not file:
                    failed_files.append(edit.filepath)
                    continue

                original = self._remove_line_numbers(file['content'])
                edited = self._apply_edit(original, edit.dict())
                
                print("--- Original content ---")
                print(original)
                print("--- Edited content ---")
                print(edited)

                if not dry_run and self._backup_and_write(edit.filepath, original, edited):
                    success_count += 1

            if failed_files:
                print(f"Failed to process {len(failed_files)} files: {', '.join(failed_files)}")
                
            if success_count == 0:
                print("Warning: No changes were applied")
                
            return success_count > 0
            
        except Exception as e:
            print(f"Error processing edit instruction: {e}")
            raise
