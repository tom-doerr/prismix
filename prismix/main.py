"""Main module for the Prismix application."""

import sys
import os
from typing import NoReturn
from prismix.core.iterative_programmer import setup_agent
from prismix.core.code_indexer import CodeIndexer
from prismix.core.colbert_retriever import ColbertRetriever  # Add this import


def execute_instruction(instruction: str) -> None:
    """Execute the given instruction using AI."""
    print(f"Executing instruction: {instruction}\n")

    print("Initializing AI agent...")
    agent = setup_agent()

    print("Generating code...")
    print("-----------------")
    result = agent.forward(instruction)

    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)

    if hasattr(result, "code"):
        # Handle CodeResult
        import re

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


def main() -> NoReturn:
    """Main function to execute the Prismix application."""
    print("CodeWeaver - AI-powered iterative code generation tool")

    if len(sys.argv) < 2:
        print("Usage: codeweaver '<instruction>' or 'index <path>' or 'index_debug <path>' or 'search_colbert <query>'")
        print("Example: codeweaver 'create a hello world script'")
        print("Example: codeweaver index '.'")
        print("Example: codeweaver index_debug '.'")
        print("Example: codeweaver search_colbert 'quantum computing'")
        return

    command = sys.argv[1]
    if command == "index":
        if len(sys.argv) < 3:
            print("Usage: codeweaver index <path>")
            return
        path = sys.argv[2]
        print(f"Indexing code at path: {path}")
        indexer = CodeIndexer()
        indexer.index_directory(path)
        print("Indexing complete.")
    elif command == "index_debug":
        if len(sys.argv) < 3:
            print("Usage: codeweaver index_debug <path>")
            return
        path = sys.argv[2]
        print(f"Debugging indexer with path: {path}")
        indexer = CodeIndexer()
        print("Ignore patterns:", indexer.ignore_patterns)
        indexer.index_directory(path)
        print("Indexed files:")
        for filepath in indexer.indexed_code:
            print(f"- {filepath}")
        print("Indexing complete.")
    elif command == "search":
        if len(sys.argv) < 4:
            print("Usage: codeweaver search <path> <query>")
            return
        path = sys.argv[2]
        query = sys.argv[3]
        print(f"Searching code at path: {path} for query: {query}")
        indexer = CodeIndexer()
        results = indexer.search_code_on_the_fly(path, query)
        if results:
            print("Search results:")
            for result in results:
                print(f"- {result.filepath}")
        else:
            print("No results found.")
    elif command == "search_colbert":
        if len(sys.argv) < 3:
            print("Usage: codeweaver search_colbert <query>")
            return
        query = sys.argv[2]
        print(f"Searching with Colbert for query: {query}")
        indexer = CodeIndexer()
        results = indexer.search_code(query)
        if results:
            print("Colbert search results:")
            for result in results:
                print(f"- {result.filepath}: {result.content[:100]}...")  # Display first 100 chars
        else:
            print("No results found.")
    else:
        execute_instruction(command)


if __name__ == "__main__":
    main()
