import os

import dspy

from code_edit_signature import CodeEdit, CodeFile
from code_edit_utils import apply_code_edit

# Setup the LLM
from dspy.teleprompt import BootstrapFewShot
from dspy.utils import openai_client
openai_client.api_key = os.environ.get("OPENAI_API_KEY")
llm = dspy.OpenAI(model="gpt-4o-mini")
dspy.settings.configure(lm=llm)

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

        code_files = [CodeFile(filepath=file_path, filecontent=file_content)]

        try:
            response = predict(instruction=instruction, code_files=code_files)

            print("--- Output Values ---")
            print(f"Start Line: {response.start_line}")
            print(f"End Line: {response.end_line}")
            print(f"Replacement Text: {response.replacement_text}")

            edited_content = apply_code_edit(
                file_content=code_files[0].filecontent,
                start_line=int(response.start_line),
                end_line=int(response.end_line),
                replacement_text=response.replacement_text
            )
            print("--- Original content ---")
            print(file_content)
            print("--- Edited content ---")
            print(edited_content)

            with open(file_path, 'w') as f:
                f.write(edited_content)
            print(f"File {file_path} updated.")

        except Exception as e:
            print(f"An error occurred: {e}")
