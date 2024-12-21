import os
import sys

import dspy

from code_edit_signature import CodeEdit, CodeFile, Context
from code_edit_utils import add_line_numbers, apply_code_edit
from qdrant_retriever import QdrantRetriever

# Setup the LLM
llm = dspy.LM(model="gpt-4o-mini", api_key=os.environ.get("OPENAI_API_KEY"))
dspy.settings.configure(lm=llm)

# Initialize the retriever
retriever = QdrantRetriever()
retriever.add_files(include_glob="*.py", exclude_glob="*test*")

if __name__ == "__main__":
    predict = dspy.ChainOfThought(CodeEdit)

    if len(sys.argv) < 3:
        print("Usage: python main.py <instruction> <file_path_1> [<file_path_2> ...]")
        sys.exit(1)

    instruction = sys.argv[1]
    file_paths = sys.argv[2:]

    code_files = []
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            sys.exit(1)
        with open(file_path, 'r') as f:
            file_content = f.read()
        numbered_content = add_line_numbers(file_content)
        code_files.append(CodeFile(filepath=file_path, filecontent=numbered_content))

    retrieved_context = retriever.retrieve(query=instruction)
    context = Context(retrieved_context="\n".join(retrieved_context), online_search="")

    try:
        response = predict(instruction=instruction, code_files=code_files, context=context)

        print("--- Output Values ---")
        print(f"Search Query: {response.search_query}")

        for edit_instruction in response.edit_instructions.edit_instructions:
            file_path = edit_instruction.filepath
            start_line = int(edit_instruction.start_line)
            end_line = int(edit_instruction.end_line)
            replacement_text = edit_instruction.replacement_text

            file_content = next((f.filecontent for f in code_files if f.filepath == file_path), None)
            if file_content is None:
                print(f"Error: File not found in code_files: {file_path}")
                continue

            edited_content = apply_code_edit(
                file_content=file_content,
                start_line=start_line,
                end_line=end_line,
                replacement_text=replacement_text
            )

            def remove_line_numbers(text: str) -> str:
                lines = text.splitlines()
                unumbered_lines = [line[7:] if len(line) > 7 else line for line in lines]
                return "\n".join(unumbered_lines)

            unumbered_edited_content = remove_line_numbers(edited_content)
            print("--- Original content ---")
            print(file_content)
            print("--- Edited content ---")
            print(unumbered_edited_content)

            with open(file_path, 'w') as f:
                f.write(unumbered_edited_content)
            print(f"File {file_path} updated.")


    except Exception as e:
        print(f"An error occurred: {e}")
