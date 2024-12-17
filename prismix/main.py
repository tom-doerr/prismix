"""Main module for the Prismix application."""

import os
import re
import sys
from typing import NoReturn

from prismix.core.code_indexer import CodeIndexer
from prismix.core.colbert_retriever import ColbertRetriever  # Add this import
from prismix.core.iterative_programmer import setup_agent


def execute_instruction(instruction: str) -> None:
    """Execute the given instruction using AI."""
    print(f"Executing instruction: {instruction}\n")

    print("Initializing AI agent...")
    agent = setup_agent()

    print("Generating code...")
    print("-----------------")
    result = agent.forward(instruction)

    if result is None:
        print("Error: No result returned from the agent.")
        return

    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)

    if hasattr(result, "code"):
        # Handle CodeResult
        function_match = re.search(r"def\s+(\w+)", result.code)
        function_name = function_match.group(1) if function_match else "generated_code"

        output_file = f"output/{function_name}.py"
        os.makedirs("output", exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.code)

        print("\nGeneration Result:")
        print("----------------")
        print("Success:", result.success)
        if result.error:
            print("Error:", result.error)
        if result.output:
            print("\nExecution Output:", result.output)
        print("\nSafety Check:", "PASSED" if result.success else "FAILED")
        print("\nGenerated code saved to:", output_file)
        print("\nContents:")
        print("----------")
        print(result.code)
        print("----------")
    else:
        # Handle FileContext
        print("\nFile Edit Result:")
        print("----------------")
        if result.error:
            print("Error:", result.error)
        else:
            print("Changes made:")
            for change in result.changes:
                print(f"- {change}")
            print("\nUpdated file contents:")
            print("---------------------")
            print(result.content)
    print("----------")

    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)

    if hasattr(result, "code"):
        # Handle CodeResult

        function_match = re.search(r"def\s+(\w+)", result.code)
        function_name = function_match.group(1) if function_match else "generated_code"

        output_file = f"output/{function_name}.py"
        os.makedirs("output", exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.code)

        print("\nGeneration Result:")
        print("----------------")
        print("Success:", result.success)
        if result.error:
            print("Error:", result.error)
        if result.output:
            print("\nExecution Output:", result.output)
        print("\nSafety Check:", "PASSED" if result.success else "FAILED")
        print("\nGenerated code saved to:", output_file)
        print("\nContents:")
        print("----------")
        print(result.code)
        print("----------")
    else:
        # Handle FileContext
        print("\nFile Edit Result:")
        print("----------------")
        if result.error:
            print("Error:", result.error)
        else:
            print("Changes made:")
            for change in result.changes:
                print(f"- {change}")
            print("\nUpdated file contents:")
            print("---------------------")
            print(result.content)
    print("----------")


def print_usage():
    """Print usage instructions."""
    print(
        "Usage: codeweaver '<instruction>' or 'index <path>' or 'index_debug <path>'"
        " or 'search_colbert <query>' or 'milvus_setup' or 'milvus_insert'"
        " or 'milvus_search'"
    )
    print("Example: codeweaver 'create a hello world script'")
    print("Example: codeweaver index '.'")
    print("Example: codeweaver index_debug '.'")
    print("Example: codeweaver search_colbert 'quantum computing'")
    print("Example: codeweaver milvus_setup")
    print("Example: codeweaver milvus_insert")
    print("Example: codeweaver milvus_search")


def handle_index_command(path):
    """Handle the 'index' command."""
    print(f"Indexing code at path: {path}")
    indexer = CodeIndexer()
    indexer.index_directory(path)
    print("Indexing complete.")


def handle_index_debug_command(path):
    """Handle the 'index_debug' command."""
    print(f"Debugging indexer with path: {path}")
    indexer = CodeIndexer()
    print("Ignore patterns:", indexer.ignore_patterns)
    indexer.index_directory(path)
    print("Indexed files:")
    for filepath in indexer.indexed_code:
        print(f"- {filepath}")
    print("Indexing complete.")


def handle_search_command(path, query):
    """Handle the 'search' command."""
    print(f"Searching code at path: {path} for query: {query}")
    indexer = CodeIndexer()
    results = indexer.search_code_on_the_fly(path, query)
    if results:
        print("Search results:")
        for result in results:
            print(f"- {result.filepath}")
    else:
        print("No results found.")


def handle_qdrant_insert_command(path):
    """Handle the 'qdrant_insert' command."""
    print(f"Inserting data into Qdrant from path: {path}")
    retriever = ColbertRetriever(url="http://example.com/colbert")
    retriever.add_data_to_db(path)
    print("Insertion complete.")


def handle_qdrant_search_command(query):
    """Handle the 'qdrant_search' command."""
    print(f"Searching Qdrant for query: {query}")
    retriever = ColbertRetriever(url="http://example.com/colbert")
    results = retriever.forward(query)
    if results:
        print("Qdrant search results:")
        for result in results:
            print(f"- {result[:100]}...")  # Display first 100 chars
    else:
        print("No results found.")


def handle_command(command, args):
    """Handle different commands."""
    if command == "index":
        handle_index_command(args[0])
    elif command == "index_debug":
        handle_index_debug_command(args[0])
    elif command == "search":
        handle_search_command(args[0], args[1])
    elif command == "qdrant_insert":
        handle_qdrant_insert_command(args[0])
    elif command == "qdrant_search":
        handle_qdrant_search_command(args[0])
    else:
        execute_instruction(command)

def main() -> NoReturn:
    """Main function to execute the Prismix application."""
    print("CodeWeaver - AI-powered iterative code generation tool")
    if len(sys.argv) < 2:
        print_usage()
        return
    command = sys.argv[1]
    args = sys.argv[2:]
    handle_command(command, args)


if __name__ == "__main__":
    main()
# Ensure any references to 'Changes in prismix/main.py' are removed or corrected.
