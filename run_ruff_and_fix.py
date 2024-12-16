import subprocess
import sys
import os
import re

def run_ruff(file_path):
    """Run ruff on the given file and return the output."""
    try:
        result = subprocess.run(
            ["ruff", file_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return e.stdout

def apply_search_replace(file_path, search_replace_blocks):
    """Apply the SEARCH/REPLACE blocks to the file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    for block in search_replace_blocks:
        search_pattern = block['search']
        replace_pattern = block['replace']
        content = re.sub(search_pattern, replace_pattern, content)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def parse_ruff_output(ruff_output):
    """Parse the ruff output to generate SEARCH/REPLACE blocks."""
    search_replace_blocks = []
    for line in ruff_output.splitlines():
        if line.startswith("FIX:"):
            parts = line.split("|")
            if len(parts) == 3:
                search_pattern = parts[1].strip()
                replace_pattern = parts[2].strip()
                search_replace_blocks.append({
                    'search': search_pattern,
                    'replace': replace_pattern
                })
    return search_replace_blocks

def main():
    """Main function to run ruff on all provided files and fix issues if any."""
    if len(sys.argv) < 2:
        print("Usage: python run_ruff_and_fix.py <file1> <file2> ...")
        sys.exit(1)

    for file_path in sys.argv[1:]:
        if not os.path.isfile(file_path):
            print(f"File not found: {file_path}")
            continue

        print(f"Running ruff on {file_path}...")
        ruff_output = run_ruff(file_path)

        if ruff_output.strip():
            print(f"Issues found in {file_path}. Fixing...")
            search_replace_blocks = parse_ruff_output(ruff_output)
            apply_search_replace(file_path, search_replace_blocks)
            print(f"Fixed issues in {file_path}.")
        else:
            print(f"No issues found in {file_path}. Skipping...")

if __name__ == "__main__":
    main()
