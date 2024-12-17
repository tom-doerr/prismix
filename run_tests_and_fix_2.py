#!/usr/bin/env python

"""
Script to run random pytest tests and pylint checks on specified number of files.
"""

import argparse
import glob
import os
import random
import subprocess

from tqdm import tqdm


def run_pylint():
    """Runs pylint on the entire project and captures the output."""
    try:
        result = subprocess.run(
            ["pylint", "."],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        pylint_output_local = f"Error running pylint: {e}\n{e.stdout}"
        return False, pylint_output
    return True, result.stdout


# def run_random_pytest(n, all_files):
def run_random_pytest(files):
    """Runs n random pytest tests and captures the output."""
    # test_files = [file_path for file_path in all_files if is_test_file(file_path)]
    # random.shuffle(test_files)
    # selected_test_files = test_files[:n]
    pytest_output_local = ""
    if not files:
        return pytest_output

    # for test_file in selected_test_files:
    for test_file_local in files:
        try:
            result = subprocess.run(
                ["pytest", test_file],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            pytest_output += result.stdout
        except subprocess.CalledProcessError as e:
            pytest_output += (
                f"Error running pytest on {test_file}: {e}\nstdout: {e.stdout}"
            )
    return pytest_output


def run_pytest():
    """Runs all pytest tests and captures the output."""
    pytest_output = ""
    try:
        result = subprocess.run(
            ["pytest", "-v"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        pytest_output += result.stdout
    except subprocess.CalledProcessError as e:
        pytest_output += f"Error running pytest: {e}\nstdout: {e.stdout}"
    return pytest_output


def run_random_pylint(files):
    """Runs pylint on n random files and captures the output."""
    pylint_output_local = ""
    for file_path in files:
        try:
            result = subprocess.run(
                ["pylint", file_path],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            pylint_output += result.stdout
        except subprocess.CalledProcessError as e:
            pylint_output += (
                f"Error running pylint on {file_path}: {e}\nstdout: {e.stdout}"
            )
    return pylint_output


def run_ruff_fix(files):
    """Runs ruff to fix code style issues and captures the output."""
    files_str = " ".join([f"./{file}" for file in files])
    try:
        result = subprocess.run(
            ["ruff", "check", f"./{files_str}", "--fix"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        # ruff_result_output = result.stdout + result.stderr
        ruff_output_local = f"stdout: {result.stdout}"
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


import requests  # Move this to the top of the module

DEBUGGING_AND_TESTING_FILE_URL = (
    "https://gist.githubusercontent.com/mwanginjuguna/545f983b12c76af238861d9af2e551a5/"
    "raw/9d8a8d47ca64cc340db69960011b368ab00179a9/introduction-to-debugging-and-testing-software.md"
)
DEBUGGING_AND_TESTING_FILE = (
    "prompt_text/introduction-to-debugging-and-testing-software.md"
)

if not os.path.exists(DEBUGGING_AND_TESTING_FILE):
    os.makedirs(os.path.dirname(DEBUGGING_AND_TESTING_FILE), exist_ok=True)
    response = requests.get(DEBUGGING_AND_TESTING_FILE_URL, timeout=10)
    with open(DEBUGGING_AND_TESTING_FILE, "wb") as file:
        file.write(response.content)

try:
    with open(DEBUGGING_AND_TESTING_FILE, "r", encoding="utf-8") as file:
        DEBUGGING_AND_TESTING_CONTENT = file.read()
except FileNotFoundError:
    print(f"File {DEBUGGING_AND_TESTING_FILE} not found.")
    DEBUGGING_AND_TESTING_CONTENT = ""


def call_aider(file_paths, model):  # Remove 'combined_output'
    """Call aider to fix issues based on combined output."""
    try:
        print(f"Calling aider to fix issues in {', '.join(file_paths)}...")
        command = (
            [
                "aider",
                "--deepseek",
                "--architect",
                "--cache-prompts",
                "--yes-always",
                "--no-detect-urls",
                "--no-suggest-shell-commands",
            ]
            + ["--model", model]
            + [item for file_path in file_paths for item in ["--file", file_path]]
            + ["--file", "notes.md"]
            + ["--file", "questions.md"]
            + [
                "--message",
                f"{DEBUGGING_AND_TESTING_CONTENT}\n\n\nDon't work on too many things at the same time. "
                "There are multiple LLMs working on this project, if you have information that could be useful for others, "
                "please update notes.md. If you have questions, please write them into questions.md. "
                "I might update the notes.md with answers to those questions. If you have commands I should run, "
                "please put them into commands.sh. Refactor notes.md and questions.md when necessary to avoid redundancy "
                "and to reduce length. Output: {combined_output}. What should we do next?",
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
        ruff_success, ruff_output = (
            run_ruff_fix(selected_files) if selected_files else (True, "")
        )

        test_files = [
            file_path for file_path in all_python_files if is_test_file(file_path)
        ]
        random.shuffle(test_files)
        selected_test_files = test_files[: args.pytest_files]
        # pytest_output = run_random_pytest(args.pytest_files, all_python_files)
        pytest_output = run_random_pytest(selected_test_files)
        # pytest_output = run_pytest()
        num_pytest_output_chars = len(pytest_output)
        print("num_pytest_output_chars:", num_pytest_output_chars)
        pylint_result_output = (
            run_random_pylint(selected_files) if selected_files else ""
        )
        files_potentially_being_tested = []
        for file in all_python_files:
            for test_file in selected_test_files:
                if test_file.replace(".py", "").split("test_")[1] in file:
                    files_potentially_being_tested.append(file)

        print("files_potentially_being_tested:", files_potentially_being_tested)
        COMBINED_OUTPUT = (
            f"Pylint output:\n{pylint_result_output}\nPytest output:\n{pytest_output}"
        ).strip()
        if "All checks passed" not in ruff_output:
            COMBINED_OUTPUT += f"\nRuff output:\n{ruff_output}"
        files_to_fix = filter_files_by_output(COMBINED_OUTPUT, all_python_files)
        files_to_fix.extend(files_potentially_being_tested)
        files_to_fix.extend(selected_files)
        files_to_fix.extend(selected_test_files)

        files_to_fix_local = list(set(files_to_fix))
        # sort
        files_to_fix.sort()
        run_black(files_to_fix)
        files_to_fix = []
        if COMBINED_OUTPUT:
            call_aider(files_to_fix, COMBINED_OUTPUT, args.model)
        if pylint_success and ruff_success and not files_to_fix:
            print("No more issues found. Stopping early.")
            break

    print("All iterations completed.")
