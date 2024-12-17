from pydantic import BaseModel, ConfigDict


class SomeModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


from litellm import files

with files("some_file.txt") as f:
    content = f.read()
