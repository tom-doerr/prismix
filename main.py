import argparse
import os
import dspy
from qdrant_retriever import QdrantRetriever
from code_edit_signature import CodeEdit
from code_editor import CodeEditor

def main() -> None:
    """Main entry point for the code editor."""
    # Setup the LLM
    llm = dspy.LM(model="gpt-4o-mini", api_key=os.environ.get("OPENAI_API_KEY"))
    dspy.settings.configure(lm=llm)

    # Initialize the retriever and predictor
    retriever = QdrantRetriever()
    retriever.add_files(include_glob="*.py", exclude_glob="*test*")
    predictor = dspy.ChainOfThought(CodeEdit)

    # Create code editor
    editor = CodeEditor(retriever, predictor)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Edit code files based on instructions.")
    parser.add_argument("instruction", type=str, nargs='?', default=None, 
                       help="Instruction for code modification.")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Preview changes without saving")
    parser.add_argument("--max-edits", type=int, default=10, 
                       help="Maximum number of edits to perform")
    args = parser.parse_args()

    # Main edit loop
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
            if editor.process_edit_instruction(instruction, args.dry_run):
                edit_count += 1
        except Exception as e:
            print(f"An error occurred: {e}")

        if args.instruction:
            break

if __name__ == "__main__":
    main()







