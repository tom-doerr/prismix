"""
Sample file processor module.
"""

def process_file(filepath):
    """Process a file and count the number of words."""
    with open(filepath, "r", encoding='utf-8') as f:
        content = f.read()

    words = content.split()
    word_count = len(words)

    with open(filepath + ".stats", "w", encoding='utf-8') as f:
        f.write(f"Word count: {word_count}")


def main():
    """Main function to process a file."""
    process_file("input.txt")


if __name__ == "__main__":
    main()
