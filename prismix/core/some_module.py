"""
This module demonstrates the use of Pydantic and litellm libraries.
"""

from importlib import resources

from pydantic import BaseModel, ConfigDict


class SomeModel(BaseModel):
    """
    A sample model class using Pydantic.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)


with resources.files("some_module").joinpath("some_file.txt").open() as f:
    content = f.read()
