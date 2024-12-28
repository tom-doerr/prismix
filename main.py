import argparse
import os
import functools
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
import dspy
from qdrant_retriever import QdrantRetriever
from code_edit_signature import CodeEdit
from code_editor import CodeEditor

import logging
from typing import Optional

def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('code_editor.log'),
            logging.StreamHandler()
        ]
    )

def get_instruction(args) -> Optional[str]:
    """Get the edit instruction from command line or user input."""
    if args.instruction:
        return args.instruction
        
    try:
        instruction = input("Enter instruction (or 'exit' to quit): ")
        return instruction if instruction.lower() != "exit" else None
    except KeyboardInterrupt:
        print("\nExiting...")
        return None

def main() -> None:
    """Main entry point for the code editor."""
    setup_logging()
    
    try:
        # Setup the LLM
        llm = dspy.LM(model="deepseek/deepseek-chat", max_tokens=200, cache=False, temperature=1.0)
        dspy.settings.configure(lm=llm)

        # Initialize the retriever and predictor
        retriever = QdrantRetriever()
        retriever.add_files(
            include_glob="*.py", 
            exclude_glob="**/{__pycache__,build,dist,.cache,.mypy_cache,.pytest_cache,venv,env,node_modules}/*"
        )
        # Create predictor with backtracking
        base_predictor = dspy.ChainOfThought(CodeEdit)
        predictor = assert_transform_module(
            base_predictor,
            functools.partial(backtrack_handler, max_backtracks=10)
        )

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
            instruction = get_instruction(args)
            if instruction is None:
                break

            # Process the edit
            try:
                if editor.process_edit_instruction(instruction, args.dry_run):
                    edit_count += 1
                    logging.info(f"Successfully processed edit #{edit_count}")
                else:
                    logging.warning("Failed to process edit instruction")
            except ValueError as e:
                logging.error(f"Invalid instruction: {e}")
            except FileNotFoundError as e:
                logging.error(f"File error: {e}")
            except RuntimeError as e:
                logging.error(f"Edit generation failed: {e}")
            except dspy.DSPyAssertionError as e:
                logging.error(f"Validation error: {e.msg}")
            except Exception as e:
                logging.error(f"Unexpected error processing edit instruction: {e}", exc_info=True)

            if args.instruction:
                break

        logging.info(f"Completed {edit_count} edits")
        
    except Exception as e:
        logging.error(f"Fatal error in main: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()







