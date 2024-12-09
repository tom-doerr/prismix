n
import os
from collections import Counter

def read_file(file_path):
    """Read the content of a file and return it as a string."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def process_text(text):
    """Process the text to count word frequencies."""
    words = text.split()
    word_count = Counter(words)
    return word_count

def display_word_frequencies(word_count):
    """Display the word frequencies in a sorted manner."""
    for word, count in word_count.most_common():
        print(f"{word}: {count}")

def main(file_path):
    """Main function to execute the text processing."""
    try:
        text = read_file(file_path)
        word_count = process_text(text)
        display_word_frequencies(word_count)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Example usage: replace 'example.txt' with your file path
    main('example.txt')