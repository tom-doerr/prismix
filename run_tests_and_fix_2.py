#!/usr/bin/env python

"""
Script to run random pytest tests and pylint checks on specified number of files.
"""

import argparse
import subprocess
import os
import glob
import random
from tqdm import tqdm


def run_pylint():
    """Runs pylint on the entire project and captures the output."""
    try:
        result = subprocess.run(
            ["pylint", "."],
            check=True,
            capture_output=True,
            text=True,
        )
        pylint_result_output = result.stdout + result.stderr
    except subprocess.CalledProcessError as e:
        pylint_output = f"Error running pylint: {e}\n{e.stdout}\n{e.stderr}"
        return False, pylint_output
    return True, pylint_output


# def run_random_pytest(n, all_files):
def run_random_pytest(files):
    """Runs n random pytest tests and captures the output."""
    # test_files = [file_path for file_path in all_files if is_test_file(file_path)]
    # random.shuffle(test_files)
    # selected_test_files = test_files[:n]
    pytest_output = ""
    if not files:
        return pytest_output

    # for test_file in selected_test_files:
    for test_file in files:
        try:
            result = subprocess.run(
                ["pytest", test_file],
                check=True,
                capture_output=True,
                text=True,
            )
            pytest_output += result.stdout + result.stderr
        except subprocess.CalledProcessError as e:
            pytest_output += f"Error running pytest on {test_file}: {e}\nstdout: {e.stdout}\nstderr: {e.stderr}"
    return pytest_output


def run_pytest():
    """Runs all pytest tests and captures the output."""
    pytest_output = ""
    try:
        result = subprocess.run(
            ["pytest", "-v"],
            check=True,
            capture_output=True,
            text=True,
        )
        pytest_output += result.stdout + result.stderr
    except subprocess.CalledProcessError as e:
        pytest_output += (
            f"Error running pytest: {e}\nstdout: {e.stdout}\nstderr: {e.stderr}"
        )
    return pytest_output


def run_random_pylint(files):
    """Runs pylint on n random files and captures the output."""
    pylint_output = ""
    for file_path in files:
        try:
            result = subprocess.run(
                ["pylint", file_path],
                check=True,
                capture_output=True,
                text=True,
            )
            pylint_output += result.stdout + result.stderr
        except subprocess.CalledProcessError as e:
            pylint_output += f"Error running pylint on {file_path}: {e}\nstdout: {e.stdout}\nstderr: {e.stderr}"
    return pylint_output


def run_ruff_fix(files):
    """Runs ruff to fix code style issues and captures the output."""
    files_str = " ".join([f"./{file}" for file in files])
    try:
        result = subprocess.run(
            ["ruff", "check", f"./{files_str}", "--fix"],
            check=True,
            capture_output=True,
            text=True,
        )
        # ruff_result_output = result.stdout + result.stderr
        ruff_output = f"stdout: {result.stdout}\nstderr: {result.stderr}"
    except subprocess.CalledProcessError as e:
        ruff_output = f"Error running ruff fix: {e}\n{e.stdout}\n{e.stderr}"
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
        if os.path.exists(potential_related_file):
            return [file_path, potential_related_file]
    return [file_path]


def filter_files_by_output(output, all_files):
    """Filters files based on the output of pytest and pylint."""
    files_to_fix = set()
    for line in output.splitlines():
        file_path = line.split(":")[0].strip()
        if file_path in all_files:
            files_to_fix.add(file_path)
    return list(files_to_fix)


def call_aider(file_paths, combined_output, model):
    """Call aider to fix issues based on combined output."""
    try:
        print(f"Calling aider to fix issues in {', '.join(file_paths)}...")
        command = (
            [
                "aider",
                "--deepseek",
                "--architect",
                "--yes-always",
                "--no-detect-urls",
                "--no-suggest-shell-commands",
            ]
            + ["--model", model]
            + ["--file", "notes.md"]
            + ["--file", "questions.md"]
            + [item for file_path in file_paths for item in ["--file", file_path]]
            + [
                "--message",
                f"There are multiple LLMs working on this project, if you have information that could be useful for others, please update notes.md. If you have questions, please write them into questions.md. I might update the notes.md with answers to those questions. Refactor notes.md and questions.md when necessary to avoid redundancy and to reduce length. Output: {combined_output}. What should we do next?",
            ]
        )
        print("Aider command:", " ".join(command))
        subprocess.run(command, check=True)
        print(f"Aider fixed issues in {', '.join(file_paths)}.")
    except subprocess.CalledProcessError as e:
        print(f"Error calling aider on {', '.join(file_paths)}: {e}")


def run_black(file_paths):
    """Runs black on the specified files."""
    for file_path in file_paths:
        try:
            subprocess.run(["black", file_path], check=True)
            print(f"Formatted {file_path} with black.")
        except subprocess.CalledProcessError as e:
            print(f"Error running black on {file_path}: {e}")


if __name__ == "__main__":
    print("Starting ...")
    parser = argparse.ArgumentParser(
        description="Run random pytest tests and pylint checks on specified number of files."
    )
    parser.add_argument(
        "--pytest-files",
        type=int,
        default=1,
        help="Number of random pytest files to run.",
    )
    parser.add_argument(
        "--lint-files",
        type=int,
        default=3,
        help="Number of random pylint files to run.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Number of iterations to run the tests and fixes.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek",
        help="Model to use for aider.",
    )
    args = parser.parse_args()

    all_python_files = glob.glob("**/*.py", recursive=True)

    for iteration in tqdm(range(args.iterations), desc="Running iterations"):
        print(f"Starting iteration {iteration + 1} of {args.iterations}...")
        pylint_success, pylint_output = run_pylint()
        random.shuffle(all_python_files)
        selected_files = all_python_files[: args.lint_files]
        ruff_success, ruff_output = run_ruff_fix(selected_files)

        test_files = [
            file_path for file_path in all_python_files if is_test_file(file_path)
        ]
        random.shuffle(test_files)
        selected_test_files = test_files[: args.pytest_files]
        # pytest_output = run_random_pytest(args.pytest_files, all_python_files)
        # pytest_output = run_random_pytest(selected_test_files)
        pytest_output = run_pytest()
        num_pytest_output_chars = len(pytest_output)
        print("num_pytest_output_chars:", num_pytest_output_chars)
        pylint_result_output = run_random_pylint(selected_files)
        files_potentially_being_tested = []
        for file in all_python_files:
            for test_file in selected_test_files:
                if test_file.replace(".py", "").split("test_")[1] in file:
                    files_potentially_being_tested.append(file)

        print("files_potentially_being_tested:", files_potentially_being_tested)
        combined_output = (
            f"Pylint output:\n{pylint_result_output}\nPytest output:\n{pytest_output}"
        )
        if "All checks passed" not in ruff_output:
            combined_output += f"\nRuff output:\n{ruff_output}"
        files_to_fix = filter_files_by_output(combined_output, all_python_files)
        files_to_fix.extend(files_potentially_being_tested)
        files_to_fix.extend(selected_files)
        files_to_fix.extend(selected_test_files)

        files_to_fix = list(set(files_to_fix))
        run_black(files_to_fix)
        call_aider(files_to_fix, combined_output, args.model)
        if pylint_success and ruff_success and not files_to_fix:
            print("No more issues found. Stopping early.")
            break

    print("All iterations completed.")
