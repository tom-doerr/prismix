import argparse
import subprocess
import os
import glob
import random

def run_pylint():
    """Runs pylint on the entire project and captures the output."""
    try:
        result = subprocess.run(["pylint", "."], check=True, capture_output=True, text=True)
        pylint_output = result.stdout
    except subprocess.CalledProcessError as e:
        pylint_output = f"Error running pylint: {e}\n{e.stdout}"
        return False, pylint_output
    return True, pylint_output

def run_random_pytest(n, all_files):
    """Runs n random pytest tests and captures the output."""
    test_files = [file_path for file_path in all_files if is_test_file(file_path)]
    random.shuffle(test_files)
    selected_test_files = test_files[:n]
    pytest_output = ""
    for test_file in selected_test_files:
        try:
            result = subprocess.run(["pytest", test_file], check=True, capture_output=True, text=True)
            pytest_output += result.stdout + "\n"
        except subprocess.CalledProcessError as e:
            pytest_output += f"Error running pytest on {test_file}: {e}\n"
    return pytest_output

def run_random_pylint(n, all_files):
    """Runs pylint on n random files and captures the output."""
    random.shuffle(all_files)
    selected_files = all_files[:n]
    pylint_output = ""
    for file_path in selected_files:
        try:
            result = subprocess.run(["pylint", file_path], check=True, capture_output=True, text=True)
            pylint_output += result.stdout + "\n"
        except subprocess.CalledProcessError as e:
            pylint_output += f"Error running pylint on {file_path}: {e}\n"
    return pylint_output

def run_ruff_fix():
    """Runs ruff to fix code style issues and captures the output."""
    try:
        result = subprocess.run(["ruff", ".", "--fix"], check=True, capture_output=True, text=True)
        ruff_output = result.stdout
    except subprocess.CalledProcessError as e:
        ruff_output = f"Error running ruff fix: {e}\n{e.stdout}"
        return False, ruff_output
    return True, ruff_output

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
    parser = argparse.ArgumentParser(description="Run random pytest tests and pylint checks on specified number of files.")
    parser.add_argument("--pytest-files", type=int, default=3, help="Number of random pytest files to run.")
    parser.add_argument("--pylint-files", type=int, default=3, help="Number of random pylint files to run.")
    args = parser.parse_args()

    all_files = glob.glob("**/*.py", recursive=True)
    pylint_success, pylint_output = run_pylint()
    ruff_success, ruff_output = run_ruff_fix()
    files_to_aider = []
    for file_path in all_files:
        files_to_aider.extend(find_related_files(file_path))
    
    # Combine the outputs
    combined_output = f"Pylint output:\n{pylint_output}\nRuff output:\n{ruff_output}"
    
    call_aider(files_to_aider, combined_output)
    
    # Run n random pytest tests and n random pylint checks
    pytest_output = run_random_pytest(args.pytest_files, all_files)
    pylint_output = run_random_pylint(args.pylint_files, all_files)
    
    # Combine the outputs
    combined_output = f"Pytest output:\n{pytest_output}\nPylint output:\n{pylint_output}"
    
    call_aider(files_to_aider, combined_output)
    
    if pylint_success and ruff_success:
        print("Ruff and Pylint checks and fixes applied successfully.")
