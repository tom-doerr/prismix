"""
This module provides functions to count words in a file and write the word count to another file.
"""

def count_words_in_file(input_file):
    """Counts the number of words in a given text file."""
    try:
        with open(input_file, "r", encoding="utf-8") as file:
            content = file.read()
            words = content.split()
            return len(words)
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
        return None
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def write_word_count_to_file(output_file, word_count):
    """Writes the word count to a specified output file."""
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(f"Word Count: {word_count}\n")
    except IOError as e:
        print(f"An error occurred while writing to the file: {e}")


def main():
    """
    Main function to count words in a file and write the count to another file.
    """
    input_file = "input.txt"  # Specify the input file name
    output_file = "output.txt"  # Specify the output file name

    word_count = count_words_in_file(input_file)
    if word_count is not None:
        write_word_count_to_file(output_file, word_count)
        print(f"The word count has been written to '{output_file}'.")


if __name__ == "__main__":
    main()
