"""
This module demonstrates the use of Pydantic and litellm libraries.
"""

import importlib.resources

from pydantic import BaseModel, ConfigDict


class SomeModel(BaseModel):
    """
    A sample model class using Pydantic.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)


with importlib.resources.open_text("some_module", "some_file.txt") as f:
    content = f.read()
