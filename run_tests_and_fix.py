import subprocess
import glob
import os


def run_pylint():
    """Runs pylint on the entire project."""
    """Runs pylint on the entire project."""
    try:
        subprocess.run(["pylint", "."], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running pylint: {e}")
        return False
    return True


def run_ruff_fix():
    """Runs ruff to fix code style issues."""
    """Runs ruff to fix code style issues."""
    try:
        subprocess.run(
            ["ruff", ".", "--fix"], check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running ruff fix: {e}")
        return False
    return True


def is_test_file(file_path):
    """Checks if a file is a test file."""
    """Checks if a file is a test file."""
    return file_path.endswith("_test.py") or "tests" in file_path.split("/")


MAX_RECURSION_DEPTH = 1


def find_related_files(file_path):
    """Finds related files for a given file."""
    """Finds related files for a given file."""

    if is_test_file(file_path):
        base_name = os.path.basename(file_path).replace("_test.py", ".py")
        potential_related_file = os.path.join(os.path.dirname(file_path), base_name)
        if os.path.exists(potential_related_file):
            return [file_path, potential_related_file]
    return [file_path]


def call_aider(file_paths, ruff_output):
    """Call aider to fix issues based on ruff output."""
    """Call aider to fix issues based on ruff output."""
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
            + ["--message", f"Ruff output: {ruff_output}. Fix it"]
        )
        print("Aider command:", " ".join(command))
        subprocess.run(command, check=True)
        print(f"Aider fixed issues in {', '.join(file_paths)}.")
    except subprocess.CalledProcessError as e:
        print(f"Error calling aider on {', '.join(file_paths)}: {e}")


if __name__ == "__main__":
    all_files = glob.glob("**/*.py", recursive=True)
    pylint_success = run_pylint()
    ruff_success = run_ruff_fix()
    for file_path in all_files:
        call_aider(find_related_files(file_path), "")
    if pylint_success and ruff_success:
        print("Ruff and Pylint checks and fixes applied successfully.")
