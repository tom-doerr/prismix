# Prismix

An AI-powered code synthesis tool that transforms natural language into production-ready Python code.

## Features

- Natural language to Python code generation
- Iterative improvement with error handling
- Built-in safety checks for generated code
- Test-driven development approach
- Isolated code execution environment

## Installation

```bash
# Install with poetry
poetry install

# Set up OpenAI API key
export OPENAI_API_KEY='your-api-key-here'
```

## Usage

Basic usage:
```bash
poetry run prismix "write a function that calculates factorial"
```

The tool will:
1. Generate program specifications
2. Implement the code
3. Run safety checks
4. Test the implementation
5. Save the code to output/

## Safety Features

- Automatic code safety analysis
- Restricted execution environment
- Import validation
- System call protection

## Development

Run tests:
```bash
poetry run pytest
```

## License

MIT License
