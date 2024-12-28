import argparse
import os
import sys
from typing import List, Optional, Dict, Any

import dspy

from code_edit_signature import CodeEdit, Context, CodeFile
from code_edit_utils import apply_code_edit
from qdrant_retriever import QdrantRetriever

def add_line_numbers(content: str) -> str:
    """Add line numbers to code content"""
    lines = content.splitlines()
    return "\n".join(f"{i+1:4} {line}" for i, line in enumerate(lines))

def remove_line_numbers(text: str) -> str:
    """Remove line numbers from code content"""
    lines = text.splitlines()
    return "\n".join(line[7:] if len(line) > 7 else line for line in lines)

def validate_edit_instruction(instruction: Any) -> bool:
    """Validate that edit instruction has required fields"""
    return (hasattr(instruction, 'start_line') and 
            hasattr(instruction, 'end_line') and 
            hasattr(instruction, 'replacement_text')) or \
           (hasattr(instruction, 'search_text') and 
            hasattr(instruction, 'replacement_text'))

def load_code_files(file_paths: List[str]) -> List[CodeFile]:
    """Load and number code files"""
    code_files = []
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            continue
        try:
            with open(file_path, 'r') as f:
                file_content = f.read()
            numbered_content = add_line_numbers(file_content)
            code_files.append(CodeFile(filepath=file_path, filecontent=numbered_content))
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
    return code_files

def apply_edit_instruction(file_content: str, instruction: Any) -> Optional[str]:
    """Apply edit instruction to file content"""
    if not validate_edit_instruction(instruction):
        print(f"Error: Invalid edit instruction: {instruction}")
        return None
        
    if hasattr(instruction, 'start_line'):
        return apply_code_edit(
            file_content=file_content,
            start_line=int(instruction.start_line),
            end_line=int(instruction.end_line),
            replacement_text=instruction.replacement_text
        )
    else:
        return file_content.replace(
            instruction.search_text,
            instruction.replacement_text
        )

def backup_and_write_file(file_path: str, original_content: str, new_content: str) -> bool:
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

# Setup the LLM
llm = dspy.LM(model="gpt-4o-mini", api_key=os.environ.get("OPENAI_API_KEY"))
dspy.settings.configure(lm=llm)

# Initialize the retriever
retriever = QdrantRetriever()
retriever.add_files(include_glob="*.py", exclude_glob="*test*")

predict = dspy.ChainOfThought(CodeEdit)

parser = argparse.ArgumentParser(description="Edit code files based on instructions.")
parser.add_argument("instruction", type=str, nargs='?', default=None, help="Instruction for code modification.")
parser.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
parser.add_argument("--max-edits", type=int, default=10, help="Maximum number of edits to perform")
args = parser.parse_args()

def process_edit_instruction(instruction: str, retriever: QdrantRetriever, predictor: Any, dry_run: bool = False) -> bool:
    """Process a single edit instruction"""
    # Load code files
    file_paths = [f for f in retriever.collection.list_points().points if f.endswith('.py')]
    code_files = load_code_files(file_paths)
    
    if not code_files:
        print("No valid code files found to edit")
        return False

    # Get context and predict edits
    context = Context(
        retrieved_context=str(retriever.retrieve(query=instruction)),
        online_search=""
    )
    
    response = predictor(instruction=instruction, code_files=code_files, context=context)
    
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
        edited_content = apply_edit_instruction(file_content, edit_instruction)
        if edited_content is None:
            continue
            
        unumbered_edited_content = remove_line_numbers(edited_content)
        
        # Show changes
        print("--- Original content ---")
        print(file_content)
        print("--- Edited content ---")
        print(unumbered_edited_content)

        # Apply changes if not in dry-run mode
        if not dry_run:
            if not backup_and_write_file(file_path, file_content, unumbered_edited_content):
                continue

    return True

def main() -> None:
    """Main entry point for the code editor"""
    edit_count = 0
    while edit_count < args.max_edits:
        # Get instruction
        if not args.instruction:
            instruction = input("Enter instruction: ")
            if instruction.lower() == "exit":
                break
        else:
            instruction = args.instruction

        # Process the edit
        try:
            if process_edit_instruction(instruction, retriever, predict, args.dry_run):
                edit_count += 1
        except Exception as e:
            print(f"An error occurred: {e}")

        if args.instruction:
            break

if __name__ == "__main__":
    main()







