from typing import List, Optional, Any
import os
from code_edit_signature import CodeEdit, CodeFile, Context
from qdrant_retriever import QdrantRetriever
import dspy

class CodeEditor:
    def __init__(self, retriever: QdrantRetriever, predictor: Any):
        self.retriever = retriever
        self.predictor = predictor

    def add_line_numbers(self, content: str) -> str:
        """Add line numbers to code content"""
        lines = content.splitlines()
        return "\n".join(f"{i+1:4} {line}" for i, line in enumerate(lines))

    def remove_line_numbers(self, text: str) -> str:
        """Remove line numbers from code content"""
        lines = text.splitlines()
        return "\n".join(line[7:] if len(line) > 7 else line for line in lines)

    def load_code_files(self, file_paths: List[str]) -> List[CodeFile]:
        """Load and number code files"""
        code_files = []
        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"Error: File not found at {file_path}")
                continue
            try:
                with open(file_path, 'r') as f:
                    file_content = f.read()
                numbered_content = self.add_line_numbers(file_content)
                code_files.append(CodeFile(filepath=file_path, filecontent=numbered_content))
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
        return code_files

    def validate_edit_instruction(self, instruction: Any) -> bool:
        """Validate that edit instruction has required fields"""
        return (hasattr(instruction, 'search_text') and 
                hasattr(instruction, 'replacement_text'))

    def apply_edit_instruction(self, file_content: str, instruction: Any) -> Optional[str]:
        """Apply edit instruction to file content using search/replace"""
        if not self.validate_edit_instruction(instruction):
            print(f"Error: Invalid edit instruction: {instruction}")
            return None
            
        return file_content.replace(
            instruction.search_text,
            instruction.replacement_text
        )

    def backup_and_write_file(self, file_path: str, original_content: str, new_content: str) -> bool:
        """Create backup and write new content to file"""
        backup_path = f"{file_path}.bak"
        try:
            # Create backup
            with open(backup_path, 'w') as backup:
                backup.write(original_content)
            
            # Validate line count
            if len(new_content.splitlines()) != len(original_content.splitlines()):
                print("Warning: Line count mismatch. Changes not applied.")
                return False
                
            # Write new content
            with open(file_path, 'w') as f:
                f.write(new_content)
            print(f"File {file_path} updated. Backup saved to {backup_path}")
            return True
        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
            return False

    def process_edit_instruction(self, instruction: str, dry_run: bool = False) -> bool:
        """Process a single edit instruction"""
        # Load code files
        file_paths = [f for f in self.retriever.collection.list_points().points if f.endswith('.py')]
        code_files = self.load_code_files(file_paths)
        
        if not code_files:
            print("No valid code files found to edit")
            return False

        # Get context and predict edits
        retrieved_context = "\n".join(self.retriever.retrieve(query=instruction, top_k=3))
        context = Context(
            retrieved_context=retrieved_context,
            online_search=""
        )
        
        response = self.predictor(instruction=instruction, context=context)
        
        if not response.edit_instructions or not response.edit_instructions.edit_instructions:
            print("No valid edit instructions generated")
            return False

        print("--- Output Values ---")
        print(f"Search Query: {response.search_query}")

        # Apply edits
        for edit_instruction in response.edit_instructions.edit_instructions:
            file_path = edit_instruction.filepath
            file_content = next((f.filecontent for f in code_files if f.filepath == file_path), None)
            if file_content is None:
                print(f"Error: File not found in code_files: {file_path}")
                continue

            # Apply edit and remove line numbers
            edited_content = self.apply_edit_instruction(file_content, edit_instruction)
            if edited_content is None:
                continue
                
            unumbered_edited_content = self.remove_line_numbers(edited_content)
            
            # Show changes
            print("--- Original content ---")
            print(file_content)
            print("--- Edited content ---")
            print(unumbered_edited_content)

            # Apply changes if not in dry-run mode
            if not dry_run:
                if not self.backup_and_write_file(file_path, file_content, unumbered_edited_content):
                    continue

        return True
