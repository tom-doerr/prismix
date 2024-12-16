"""
Sample file processor module.
"""

def process_file(filepath: str) -> None:
    """Process a file and count the number of words."""
    with open(filepath, "r", encoding='utf-8') as f:
        content = f.read()

    words = content.split()
    word_count = len(words)

    with open(filepath + ".stats", "w", encoding='utf-8') as f:
        f.write(f"Word count: {word_count}")


import sys

def main():
    """Main function to process a file."""
    if len(sys.argv) != 2:
        print("Usage: python file_processor.py <filepath>")
        sys.exit(1)
    filepath = sys.argv[1]
    process_file(filepath)


if __name__ == "__main__":
    main()
