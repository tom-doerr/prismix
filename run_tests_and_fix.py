import subprocess
import os
import glob

def run_pylint():
    """Runs pylint on the entire project."""
    try:
        subprocess.run(["pylint", "."], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running ruff or pylint: {e}")
        return False
    return True

def run_ruff_fix():
    """Runs ruff to fix code style issues."""
    try:
        subprocess.run(["ruff", ".", "--fix"], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running ruff fix: {e}")
        return False
    return True

def is_test_file(file_path):
    """Checks if a file is a test file."""
    return file_path.endswith("_test.py") or "tests" in file_path.split(os.sep)

def find_related_files(file_path):
    """Finds related files for a given file (very basic implementation)."""
    # This is a placeholder, you might need more sophisticated logic
    if is_test_file(file_path):
        base_name = os.path.basename(file_path).replace("_test.py", ".py")
        potential_related_file = os.path.join(os.path.dirname(file_path), base_name)
        if os.path.exists(potential_related_file):
            return [file_path, potential_related_file]
    return [file_path]

def call_aider(file_paths, ruff_output):
    """Call aider to fix issues based on ruff output."""
    try:
        print(f"Calling aider to fix issues in {', '.join(file_paths)}...")
        subprocess.run(
            ["aider", "--deepseek", "--edit-format", "diff", "--yes-always", "--no-suggest-shell-commands"] +
            [f"--file", file_path for file_path in file_paths] +
            ["--message", f"Ruff output: {ruff_output}. Fix it"],
            check=True
        )
        print(f"Aider fixed issues in {', '.join(file_paths)}.")
    except subprocess.CalledProcessError as e:
        print(f"Error calling aider on {', '.join(file_paths)}: {e}")

if __name__ == "__main__":
    all_files = glob.glob("**/*.py", recursive=True)
    if run_pylint():
        if run_ruff_fix():
            files_to_aider = []
            for file_path in all_files:
                files_to_aider.extend(find_related_files(file_path))
            call_aider(files_to_aider, "")
            print("Ruff and Pylint checks and fixes applied successfully.")
