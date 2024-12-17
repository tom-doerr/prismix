"""
Utility module for handling litellm-related operations.
"""

import json
from importlib import resources

with resources.files("litellm.llms.tokenizers").joinpath(
    "anthropic_tokenizer.json"
).open() as f:
    tokenizer_data = json.load(f)
with resources.files("litellm.llms.tokenizers").joinpath(
    "anthropic_tokenizer.json"
).open() as f:
    pass
