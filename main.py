import dspy

from code_edit_signature import CodeEdit, CodeFile
from code_edit_utils import apply_code_edit

# Setup the LLM
llm = dspy.OpenAI(model="gpt-4o-mini")
dspy.settings.configure(lm=llm)

# Example usage
if __name__ == "__main__":
    code_files = [
        CodeFile(
            filepath="example.py",
            filecontent="""def hello():
    print("hello")
"""
        )
    ]

    instruction = "Change the print statement to say 'Hello, world!'"

    predict = dspy.Predict(CodeEdit)

    response = predict(instruction=instruction, code_files=code_files)

    edited_content = apply_code_edit(
        file_content=code_files[0].filecontent,
        start_line=int(response.start_line),
        end_line=int(response.end_line),
        replacement_text=response.replacement_text
    )

    print("Original content:")
    print(code_files[0].filecontent)
    print("\nEdited content:")
    print(edited_content)
