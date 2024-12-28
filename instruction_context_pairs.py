"""Contains predefined instruction-context pairs for code editing examples."""

INSTRUCTION_CONTEXT_PAIRS = [
    {
        "instruction": "Add a comment to the hello function that says 'This is a hello function.'",
        "context": """
from datetime import datetime

def hello():
    print('hello')

def print_datetime_nyc():
    print(datetime.now())

# This is a sample python file
# It contains a hello function
# that prints hello

if __name__ == "__main__":
    hello()
"""
    },
    {
        "instruction": "Change the print statement in the hello function to say 'hello world'",
        "context": """
from datetime import datetime

def hello():
    print('hello')

def print_datetime_nyc():
    print(datetime.now())

# This is a sample python file
# It contains a hello function
# that prints hello

if __name__ == "__main__":
    hello()
"""
    },
    # Add remaining instruction-context pairs here...
]
