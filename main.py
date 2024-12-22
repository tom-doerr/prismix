import os
import sys
import argparse

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

    predict = dspy.ChainOfThought(CodeEdit)

    parser = argparse.ArgumentParser(description="Edit code files based on instructions.")
    parser.add_argument("instruction", type=str, help="Instruction for code modification.")
    args = parser.parse_args()
    instruction = args.instruction

    if not instruction:
        print("Entering interactive mode. Type 'exit' to quit.")
        while True:
            instruction = input("Enter instruction: ")
            if instruction.lower() == "exit":
                break

            file_paths = retriever.collection.list_points().points
            file_paths = [point.id for point in file_paths]

            code_files = []
            for file_path in file_paths:
                if not os.path.exists(file_path):
                    print(f"Error: File not found at {file_path}")
                    continue
                with open(file_path, 'r') as f:
                    file_content = f.read()
                numbered_content = add_line_numbers(file_content)
                code_files.append(CodeFile(filepath=file_path, filecontent=numbered_content))

            retrieved_context = retriever.retrieve(query=instruction)
            context = Context(retrieved_context="\n".join(retrieved_context), online_search="")

            try:
                response = predict(instruction=instruction, code_files=code_files, context=context)
                print("response:", response)

                print("--- Output Values ---")
                print(f"Search Query: {response.search_query}")

                for edit_instruction in response.edit_instructions.edit_instructions:
                    file_path = edit_instruction.filepath
                    file_content = next((f.filecontent for f in code_files if f.filepath == file_path), None)
                    if file_content is None:
                        print(f"Error: File not found in code_files: {file_path}")
                        continue

                    if hasattr(edit_instruction, 'start_line') and hasattr(edit_instruction, 'end_line') and hasattr(edit_instruction, 'replacement_text'):
                        start_line = int(edit_instruction.start_line)
                        end_line = int(edit_instruction.end_line)
                        replacement_text = edit_instruction.replacement_text

                        edited_content = apply_code_edit(
                            file_content=file_content,
                            start_line=start_line,
                            end_line=end_line,
                            replacement_text=replacement_text
                        )
                    elif hasattr(edit_instruction, 'search_text') and hasattr(edit_instruction, 'replacement_text'):
                        search_text = edit_instruction.search_text
                        replacement_text = edit_instruction.replacement_text

                        def replace_text(text: str, search_text: str, replacement_text: str) -> str:
                            return text.replace(search_text, replacement_text)

                        edited_content = replace_text(file_content, search_text, replacement_text)
                    else:
                        print(f"Error: Invalid edit instruction: {edit_instruction}")
                        continue


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
        sys.exit(0)


    file_paths = retriever.collection.list_points().points
    file_paths = [point.id for point in file_paths]

    code_files = []
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            continue
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
            file_content = next((f.filecontent for f in code_files if f.filepath == file_path), None)
            if file_content is None:
                print(f"Error: File not found in code_files: {file_path}")
                continue

            if hasattr(edit_instruction, 'start_line') and hasattr(edit_instruction, 'end_line') and hasattr(edit_instruction, 'replacement_text'):
                start_line = int(edit_instruction.start_line)
                end_line = int(edit_instruction.end_line)
                replacement_text = edit_instruction.replacement_text

                edited_content = apply_code_edit(
                    file_content=file_content,
                    start_line=start_line,
                    end_line=end_line,
                    replacement_text=replacement_text
                )
            elif hasattr(edit_instruction, 'search_text') and hasattr(edit_instruction, 'replacement_text'):
                search_text = edit_instruction.search_text
                replacement_text = edit_instruction.replacement_text

                def replace_text(text: str, search_text: str, replacement_text: str) -> str:
                    return text.replace(search_text, replacement_text)

                edited_content = replace_text(file_content, search_text, replacement_text)
            else:
                print(f"Error: Invalid edit instruction: {edit_instruction}")
                continue


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
