import os

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

# Example usage
if __name__ == "__main__":
    predict = dspy.Predict(CodeEdit)

    while True:
        instruction = input("Enter instruction (or 'exit' to quit): ")
        if instruction.lower() == 'exit':
            break

        file_path = input("Enter file path: ")
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            continue

        with open(file_path, 'r') as f:
            file_content = f.read()

        numbered_content = add_line_numbers(file_content)
        code_files = [CodeFile(filepath=file_path, filecontent=numbered_content)]

        retrieved_context = retriever.retrieve(query=instruction)
        context = Context(retrieved_context="\n".join(retrieved_context), online_search="")

        try:
            response = predict(instruction=instruction, code_files=code_files, context=context)

            print("--- Output Values ---")
            print(f"Filepath: {response.filepath}")
            print(f"Start Line: {response.start_line}")
            print(f"End Line: {response.end_line}")
            print(f"Replacement Text: {response.replacement_text}")
            print(f"Search Query: {response.search_query}")

            edited_content = apply_code_edit(
                file_content=file_content,
                start_line=int(response.start_line),
                end_line=int(response.end_line),
                replacement_text=response.replacement_text
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
