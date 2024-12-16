import subprocess
import os
import glob
import random

def run_pylint():
    """Runs pylint on the entire project."""
    try:
        subprocess.run(["pylint", "."], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running ruff or pylint: {e}")
        return False
    return True

def run_random_pytest(n):
    """Runs n random pytest tests."""
    test_files = [file_path for file_path in all_files if is_test_file(file_path)]
    random.shuffle(test_files)
    selected_test_files = test_files[:n]
    for test_file in selected_test_files:
        try:
            subprocess.run(["pytest", test_file], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running pytest on {test_file}: {e}")

def run_random_pylint(n):
    """Runs pylint on n random files."""
    random.shuffle(all_files)
    selected_files = all_files[:n]
    for file_path in selected_files:
        try:
            subprocess.run(["pylint", file_path], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running pylint on {file_path}: {e}")

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

MAX_RECURSION_DEPTH = 1

def find_related_files(file_path):
    """Finds related files for a given file."""

    if is_test_file(file_path):
        base_name = os.path.basename(file_path).replace("_test.py", ".py")
        potential_related_file = os.path.join(os.path.dirname(file_path), base_name)
        if os.path.exists(potential_related_file) :
            return [file_path, potential_related_file]
    return [file_path]

def call_aider(file_paths, ruff_output):
    """Call aider to fix issues based on ruff output."""
    try:
        print(f"Calling aider to fix issues in {', '.join(file_paths)}...")
        command = ["aider", "--deepseek", "--edit-format", "diff", "--yes-always", "--no-suggest-shell-commands"] + \
            [item for file_path in file_paths for item in ["--file", file_path]] + \
            ["--message", f"Ruff output: {ruff_output}. Fix it"]
        print("Aider command:", " ".join(command))
        subprocess.run(
            command,
            check=True
        )
        print(f"Aider fixed issues in {', '.join(file_paths)}.")
    except subprocess.CalledProcessError as e:
        print(f"Error calling aider on {', '.join(file_paths)}: {e}")

if __name__ == "__main__":
    all_files = glob.glob("**/*.py", recursive=True)
    pylint_success = run_pylint()
    ruff_success = run_ruff_fix()
    files_to_aider = []
    for file_path in all_files:
        files_to_aider.extend(find_related_files(file_path))
    call_aider(files_to_aider, "")
    
    # Run n random pytest tests and n random pylint checks
    n = 3  # Number of random tests and pylint checks to run
    run_random_pytest(n)
    run_random_pylint(n)
    
    if pylint_success and ruff_success:
        print("Ruff and Pylint checks and fixes applied successfully.")
