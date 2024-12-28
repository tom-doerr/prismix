from typing import List, Optional, Any
import os
from code_edit_signature import CodeEdit, CodeFile, Context
from qdrant_retriever import QdrantRetriever
import dspy

class CodeEditor:
    """Handles code editing operations including file loading, editing, and saving."""
    
    def __init__(self, retriever: QdrantRetriever, predictor: Any):
        """Initialize CodeEditor with retriever and predictor."""
        self.retriever = retriever
        self.predictor = predictor

    def add_line_numbers(self, content: str) -> str:
        """Add line numbers to code content."""
        lines = content.splitlines()
        return "\n".join(f"{i+1:4} {line}" for i, line in enumerate(lines))

    def remove_line_numbers(self, text: str) -> str:
        """Remove line numbers from code content."""
        lines = text.splitlines()
        return "\n".join(line[5:] if len(line) > 5 else line for line in lines)

    def load_code_files(self, file_paths: List[str]) -> List[CodeFile]:
        """Load and number code files."""
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
        """Validate that edit instruction has required fields."""
        return (hasattr(instruction, 'search_text') and 
                hasattr(instruction, 'replacement_text'))

    def apply_edit_instruction(self, file_content: str, instruction: Any) -> Optional[str]:
        """Apply edit instruction to file content using search/replace."""
        if not self.validate_edit_instruction(instruction):
            print(f"Error: Invalid edit instruction: {instruction}")
            return None
            
        return file_content.replace(
            instruction.search_text,
            instruction.replacement_text
        )

    def backup_and_write_file(self, file_path: str, original_content: str, new_content: str) -> bool:
        """Create backup and write new content to file."""
        backup_path = f"{file_path}.bak"
        try:
            # Create backup
            with open(backup_path, 'w') as backup:
                backup.write(original_content)
            
            # Write new content
            with open(file_path, 'w') as f:
                f.write(new_content)
            print(f"File {file_path} updated. Backup saved to {backup_path}")
            return True
        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
            return False

    def process_edit_instruction(self, instruction: str, dry_run: bool = False) -> bool:
        """Process a single edit instruction.
        
        Args:
            instruction: The edit instruction to process
            dry_run: If True, only preview changes without saving
            
        Returns:
            bool: True if edits were successfully applied, False otherwise
            
        Raises:
            ValueError: If the instruction is empty or invalid
            FileNotFoundError: If no valid code files are found
            RuntimeError: If the predictor fails to generate valid edit instructions
            dspy.AssertionError: If edit instructions fail validation
        """
        if not instruction or not instruction.strip():
            raise ValueError("Instruction cannot be empty")
            
        try:
            # Extract specific search text from instruction
            search_query = instruction
            if " to " in instruction:
                search_query = instruction.split(" to ")[0].strip()
                if "change " in search_query:
                    search_query = search_query.replace("change ", "").strip()
            
            # Search for relevant files based on extracted search text
            print(f"Searching for files containing: '{search_query}'")
            search_results = self.retriever.retrieve(query=search_query, top_k=3)
            file_paths = list(set(result[0] for result in search_results))
            
            if not file_paths:
                raise FileNotFoundError("No relevant files found for the instruction")
                
            print(f"Found {len(file_paths)} relevant files:")
            for i, file_path in enumerate(file_paths):
                print(f"{i+1}. {file_path}")
            code_files = self.load_code_files(file_paths)
            
            if not code_files:
                raise FileNotFoundError("No valid code files found to edit")

            # Get context and predict edits
            retrieved_results = self.retriever.retrieve(query=instruction, top_k=3)
            retrieved_context = "\n".join(f"File: {result[0]}\nCode:\n{result[1]}" for result in retrieved_results)
            context = Context(
                retrieved_context=retrieved_context,
                online_search=""
            )
            
            # Use assertions to validate the response
            response = self.predictor(instruction=instruction, context=context)
            
            # Ensure response has required attributes
            if not hasattr(response, 'edit_instructions') or not hasattr(response, 'search_query'):
                raise RuntimeError("Invalid response format from predictor - missing required fields")
                
            # Parse and validate edit instructions
            try:
                import json
                from prismix.core.models import EditInstructions
                
                # First try to parse as JSON
                try:
                    edit_data = json.loads(response.edit_instructions)
                except json.JSONDecodeError:
                    # If direct JSON parsing fails, try to extract JSON from markdown code block
                    try:
                        import re
                        json_match = re.search(r'```json\n(.*?)\n```', response.edit_instructions, re.DOTALL)
                        if json_match:
                            edit_data = json.loads(json_match.group(1))
                        else:
                            # Try to find JSON in the response text
                            json_match = re.search(r'\{.*\}', response.edit_instructions, re.DOTALL)
                            if json_match:
                                edit_data = json.loads(json_match.group())
                            else:
                                raise ValueError("Could not find valid JSON in response")
                    except Exception as e:
                        raise dspy.DSPyAssertionError(
                            id="invalid_json_format",
                            msg=f"Invalid edit instructions format: {e}. Must be valid JSON matching EditInstructions schema."
                        )
                
                # Validate using Pydantic model
                edit_instructions = EditInstructions(**edit_data)
                
            except Exception as e:
                raise dspy.DSPyAssertionError(
                    id="invalid_edit_instructions",
                    msg=f"Invalid edit instructions: {e}. Must match EditInstructions schema."
                )

            print("--- Output Values ---")
            print(f"Search Query: {response.search_query}")

            # Track success of edits
            success_count = 0
            failed_files = []
            
            # Apply edits
            for edit_instruction in edit_instructions.edit_instructions:
                file_path = edit_instruction.filepath
                file_content = next((f.filecontent for f in code_files if f.filepath == file_path), None)
                if file_content is None:
                    failed_files.append(file_path)
                    continue

                # Remove line numbers before applying edit
                original_unumbered = self.remove_line_numbers(file_content)
                
                # Apply edit to unnumbered content
                edited_content = self.apply_edit_instruction(original_unumbered, edit_instruction)
                if edited_content is None:
                    failed_files.append(file_path)
                    continue
                    
                # Show changes
                print("--- Original content ---")
                print(original_unumbered)
                print("--- Edited content ---")
                print(edited_content)

                # Apply changes if not in dry-run mode
                if not dry_run:
                    if self.backup_and_write_file(file_path, original_unumbered, edited_content):
                        success_count += 1

            if failed_files:
                print(f"Failed to process {len(failed_files)} files: {', '.join(failed_files)}")
                return False
                
            if success_count == 0:
                print("Warning: No changes were applied")
                return False
                
            return True
            
        except dspy.DSPyAssertionError as e:
            print(f"Validation error: {e}")
            raise
        except Exception as e:
            print(f"Error processing edit instruction: {e}")
            raise
