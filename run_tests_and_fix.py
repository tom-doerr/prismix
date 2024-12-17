"""
Script to run pylint and ruff checks on the project.
"""

import subprocess
import glob
import os


def run_pylint():
    """Runs pylint on the entire project and captures the output."""
    try:
        result = subprocess.run(
            ["pylint", "."],
            check=True,
            capture_output=True,  # Capture both stdout and stderr
            text=True,
        )
        pylint_result_output = result.stdout + result.stderr  # Combine stdout and stderr
    except subprocess.CalledProcessError as e:
        pylint_output = f"Error running pylint: {e}\n{e.stdout}\n{e.stderr}"
        return False, pylint_output
    return True, pylint_output


def run_ruff_fix():
    """Runs ruff to fix code style issues and captures the output."""
    try:
        result = subprocess.run(
            ["ruff", ".", "--fix"],
            check=True,
            capture_output=True,  # Capture both stdout and stderr
            text=True,
        )
        ruff_result_output = result.stdout + result.stderr  # Combine stdout and stderr
    except subprocess.CalledProcessError as e:
        ruff_output = f"Error running ruff fix: {e}\n{e.stdout}\n{e.stderr}"
        return False, ruff_output
    return True, ruff_output


def is_test_file(file_path):
    return file_path.endswith("_test.py") or "tests" in file_path.split("/")


MAX_RECURSION_DEPTH = 1


def find_related_files(file_path):

    if is_test_file(file_path):
        base_name = os.path.basename(file_path).replace("_test.py", ".py")
        potential_related_file = os.path.join(os.path.dirname(file_path), base_name)
        if os.path.exists(potential_related_file):
            return [file_path, potential_related_file]
    return [file_path]


def call_aider(file_paths, combined_output):
    """Call aider to fix issues based on combined output."""
    try:
        print(f"Calling aider to fix issues in {', '.join(file_paths)}...")
        command = (
            [
                "aider",
                "--deepseek",
                "--edit-format",
                "diff",
                "--yes-always",
                "--no-suggest-shell-commands",
            ]
            + [item for file_path in file_paths for item in ["--file", file_path]]
            + ["--message", f"Output: {combined_output}. Fix it"]
        )
        print("Aider command:", " ".join(command))
        subprocess.run(command, check=True)
        print(f"Aider fixed issues in {', '.join(file_paths)}.")
    except subprocess.CalledProcessError as e:
        print(f"Error calling aider on {', '.join(file_paths)}: {e}")


if __name__ == "__main__":
    all_files = glob.glob("**/*.py", recursive=True)
    pylint_success, pylint_output = run_pylint()
    ruff_success, ruff_output = run_ruff_fix()
    combined_output = (
        f"Pylint output:\n{pylint_output}\nRuff output:\n{ruff_output}"
    )
    combined_output = (
        f"Pylint output:\n{pylint_output}\nRuff output:\n{ruff_output}"
    )
    for file_path in all_files:
        call_aider(find_related_files(file_path), combined_output)
    if pylint_success and ruff_success:
        print("Pylint and Ruff checks and fixes applied successfully.")
