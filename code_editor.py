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
            
        # Find the indentation of the search text line
        lines = file_content.splitlines()
        for i, line in enumerate(lines):
            if instruction.search_text in line:
                # Get the indentation (whitespace before first non-whitespace char)
                indentation = line[:len(line) - len(line.lstrip())]
                break
        else:
            # If search text not found, just do a simple replace
            return file_content.replace(
                instruction.search_text,
                instruction.replacement_text
            )
            
        # Split replacement text into lines and apply indentation
        replacement_lines = instruction.replacement_text.splitlines()
        if len(replacement_lines) > 1:
            # Apply indentation to all lines except first
            replacement_lines = [replacement_lines[0]] + [
                indentation + line for line in replacement_lines[1:]
            ]
            instruction.replacement_text = '\n'.join(replacement_lines)
            
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

    def _is_valid_json(self, text: str) -> bool:
        """Helper method to validate JSON format."""
        try:
            import json
            json.loads(text)
            return True
        except json.JSONDecodeError:
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
            if not hasattr(response, 'edit_instructions'):
                raise RuntimeError("Invalid response format from predictor - missing required fields")
                
            # Parse and validate edit instructions
            try:
                import json
                import re
                from prismix.core.models import EditInstructions
                
                # Clean and parse the response
                edit_text = response.edit_instructions.strip()
                
                # Remove markdown code block markers if present
                if edit_text.startswith("```json") and edit_text.endswith("```"):
                    edit_text = edit_text[7:-3].strip()
                elif edit_text.startswith("```") and edit_text.endswith("```"):
                    edit_text = edit_text[3:-3].strip()
                
                # Ensure complete JSON by checking for closing brackets
                if not edit_text.strip().endswith('}'):
                    # Try to complete the JSON
                    if 'edit_instructions' in edit_text and not edit_text.strip().endswith(']}'):
                        edit_text = edit_text.rstrip() + ']}'
                    elif not edit_text.strip().endswith('}'):
                        edit_text = edit_text.rstrip() + '}'
                
                # Validate JSON format with detailed feedback
                try:
                    import json
                    parsed = json.loads(edit_text)
                    
                    # Check basic structure
                    dspy.Assert(
                        isinstance(parsed, dict),
                        "Top level must be a JSON object with 'edit_instructions' array"
                    )
                    dspy.Assert(
                        'edit_instructions' in parsed,
                        "Missing 'edit_instructions' array in JSON"
                    )
                    dspy.Assert(
                        isinstance(parsed['edit_instructions'], list),
                        "'edit_instructions' must be an array of edit objects"
                    )
                    
                    # Validate each edit instruction
                    for i, instr in enumerate(parsed['edit_instructions']):
                        dspy.Assert(
                            isinstance(instr, dict),
                            f"Edit instruction {i+1} must be a JSON object"
                        )
                        dspy.Assert(
                            'filepath' in instr,
                            f"Edit instruction {i+1} missing 'filepath' field"
                        )
                        dspy.Assert(
                            'search_text' in instr,
                            f"Edit instruction {i+1} missing 'search_text' field"
                        )
                        dspy.Assert(
                            'replacement_text' in instr,
                            f"Edit instruction {i+1} missing 'replacement_text' field"
                        )
                        
                except json.JSONDecodeError as e:
                    from prismix.core.models import EditInstructions
                    edit_instructions_format = str(EditInstructions.model_json_schema())
                    error_msg = f"Error parsing edit_instructions: {str(e)}.\n"
                    error_msg += "edit_instructions must be of the following format:\n"
                    error_msg += edit_instructions_format + "\n\n"
                    error_msg += "Common issues:\n"
                    error_msg += "- Missing or extra commas\n"
                    error_msg += "- Unclosed quotes or brackets\n"
                    error_msg += "- Using single quotes instead of double quotes\n"
                    error_msg += "- Truncated JSON\n"
                    # Write the full received text to a file for debugging
                    with open("debug_received_text.txt", "w") as f:
                        f.write(edit_text)
                    dspy.Assert(False, error_msg)
                
                # Parse the validated JSON
                edit_data = json.loads(edit_text)
                
                # Log the complete JSON for debugging
                print("Complete JSON received:")
                full_json = json.dumps(edit_data, indent=2)
                print(full_json)
                # Write full JSON to a file for debugging
                with open("debug_edit_instructions.json", "w") as f:
                    f.write(full_json)
                
                # Validate using Pydantic model
                try:
                    edit_instructions = EditInstructions(**edit_data)
                except Exception as e:
                    raise dspy.DSPyAssertionError(
                        id="invalid_edit_schema",
                        msg=f"Edit instructions do not match required schema: {e}. Must match EditInstructions schema. Received: {edit_data}"
                    )
                
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
