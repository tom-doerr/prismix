"""
This module demonstrates the use of Pydantic and litellm libraries.
"""


from pydantic import BaseModel


class SomeModel(BaseModel):
    """
    A sample model class using Pydantic.
    """

    model_config = {"arbitrary_types_allowed": True}


import importlib.resources as resources

with resources.files("some_module").joinpath("some_file.txt").open() as f:
    content = f.read()
