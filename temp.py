n
import argparse
import os

def read_file(filename):
    """Read and return the contents of the file."""
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"The file {filename} does not exist.")
    
    with open(filename, 'r') as file:
        return file.read()

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='A simple command line tool to read a file.')
    parser.add_argument('filename', type=str, help='The name of the file to read')

    # Parse the arguments
    args = parser.parse_args()

    try:
        # Read and print the file contents
        contents = read_file(args.filename)
        print(contents)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()