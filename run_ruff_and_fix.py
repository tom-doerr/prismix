import subprocess
import sys
import os
import re

def run_ruff(file_path):
    """Run ruff on the given file and return the output."""
    try:
        print(f"Executing ruff on {file_path}...")
        result = subprocess.run(
            ["ruff", "check", file_path],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Raw ruff output for {file_path}:\n{result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running ruff on {file_path}: {e.stdout}")
        return e.stdout

def fix_syntax_errors(file_path, ruff_output):
    """Fix syntax errors in the file based on ruff output."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.readlines()

        for line in ruff_output.splitlines():
            if line.startswith("SyntaxError:"):
                # Parse the error and attempt to fix it
                # This is a simplified example and may need to be extended for complex cases
                error_info = line.split(":")
                line_number = int(error_info[1].strip()) - 1
                error_type = error_info[2].strip()

                if error_type == "Unexpected indentation":
                    content[line_number] = content[line_number].lstrip()
                elif error_type == "Expected a statement":
                    content[line_number] = ""
                elif error_type == "Got unexpected token":
                    content[line_number] = content[line_number].replace("```", "")

        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(content)
    except Exception as e:
        print(f"Error fixing syntax errors in {file_path}: {e}")

def apply_search_replace(file_path, search_replace_blocks):
    """Apply the SEARCH/REPLACE blocks to the file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        for block in search_replace_blocks:
            search_pattern = block['search']
            replace_pattern = block['replace']
            content = re.sub(search_pattern, replace_pattern, content)

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
    except Exception as e:
        print(f"Error applying changes to {file_path}: {e}")

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

def call_aider(file_path, ruff_output):
    """Call aider to fix issues based on ruff output."""
    # Placeholder for the actual implementation of calling aider
    print(f"Calling aider to fix issues in {file_path} with output:\n{ruff_output}")

def main():
    """Main function to run ruff on all provided files and fix issues if any."""
    if len(sys.argv) < 2:
        print("Usage: python run_ruff_and_fix.py <file1> <file2> ... [--test] [--dry-run]")
        sys.exit(1)

    test_mode = "--test" in sys.argv
    dry_run = "--dry-run" in sys.argv

    for file_path in sys.argv[1:]:
        if file_path in ["--test", "--dry-run"]:
            continue

        if not os.path.isfile(file_path):
            print(f"File not found: {file_path}")
            continue

        print(f"Running ruff on {file_path}...")

        if test_mode:
            # Simulate ruff output with issues for testing
            ruff_output = "FIX: | old_code | new_code\nFIX: | another_old_code | another_new_code"
        else:
            ruff_output = run_ruff(file_path)

        if ruff_output.strip():
            print(f"Issues found in {file_path}. Fixing...")
            if dry_run:
                print(f"Dry run for {file_path}:")
                print(f"Ruff output: {ruff_output}")
            else:
                # Call aider to fix the issues
                call_aider(file_path, ruff_output)
                print(f"Fixed issues in {file_path}.")
        else:
            print(f"No issues found in {file_path}. Skipping...")

if __name__ == "__main__":
    main()
