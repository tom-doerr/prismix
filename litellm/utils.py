from importlib import resources

# Use the file
with resources.files("litellm.llms.tokenizers").joinpath("anthropic_tokenizer.json").open() as f:
    pass
