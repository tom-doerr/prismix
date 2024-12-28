from pydantic import BaseModel, Field
from typing import List

class Context(BaseModel):
    retrieved_context: str = Field(..., desc="Context retrieved from the codebase.")
    online_search: str = Field(..., desc="Context from online search results.")

class CodeFile(BaseModel):
    filepath: str
    filecontent: str

class SearchReplaceEditInstruction(BaseModel):
    filepath: str = Field(..., desc="The path to the file that should be edited.")
    search_text: str = Field(..., desc="The text to search for.")
    replacement_text: str = Field(..., desc="The text to replace the found text with.")

class EditInstructions(BaseModel):
    edit_instructions: List[SearchReplaceEditInstruction] = Field(
        ..., desc="A list of search/replace edit instructions."
    )

class Scorer(BaseModel):
    score: float = Field(
        ..., ge=0, le=10, desc="The score of the edit, value between 0 and 10."
    )
