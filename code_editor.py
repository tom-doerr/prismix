from typing import List, Optional, Dict, Any
import os
import json
from pathlib import Path
from prismix.core.models import SearchReplaceEditInstruction, Context
from qdrant_retriever import QdrantRetriever
import dspy

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
        """Apply a single edit instruction to content."""
        if not self._validate_edit(instruction):
            raise ValueError(f"Invalid edit instruction: {instruction}")
            
        # Find indentation of search text line
        lines = content.splitlines()
        for line in lines:
            if instruction['search_text'] in line:
                indentation = line[:len(line) - len(line.lstrip())]
                break
        else:
            # Simple replace if search text not found
            return content.replace(
                instruction['search_text'],
                instruction['replacement_text']
            )
            
        # Apply indentation to multi-line replacements
        replacement_lines = instruction['replacement_text'].splitlines()
        if len(replacement_lines) > 1:
            replacement_lines = [replacement_lines[0]] + [
                indentation + line for line in replacement_lines[1:]
            ]
            instruction['replacement_text'] = '\n'.join(replacement_lines)
            
        return content.replace(
            instruction['search_text'],
            instruction['replacement_text']
        )

    def _backup_and_write(self, file_path: str, original: str, new: str) -> bool:
        """Create backup and write new content to file."""
        backup_path = f"{file_path}.bak"
        try:
            with open(backup_path, 'w') as backup:
                backup.write(original)
            with open(file_path, 'w') as f:
                f.write(new)
            print(f"File {file_path} updated. Backup saved to {backup_path}")
            return True
        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
            return False

    def process_edit(self, instruction: str, dry_run: bool = False) -> bool:
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
        """
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
                raise RuntimeError("Invalid response format from predictor")
                
            # Process edit instructions
            edits = [
                SearchReplaceEditInstruction(**instr)
                for instr in response.edit_instructions
                if isinstance(instr, dict) and 
                   all(k in instr for k in ['filepath', 'search_text', 'replacement_text'])
            ]
            
            if not edits:
                raise ValueError("No valid edit instructions found")

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
