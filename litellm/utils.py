"""
Utility module for handling litellm-related operations.
"""

from importlib import resources

with resources.files("litellm.llms.tokenizers").joinpath("anthropic_tokenizer.json").open() as f:
    pass
