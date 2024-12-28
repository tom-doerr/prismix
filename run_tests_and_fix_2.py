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
    pylint_output_local = ""
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
        return False, pylint_output_local
    return True, result.stdout


# def run_random_pytest(n, all_files):
def run_random_pytest(files):
    """Runs n random pytest tests and captures the output."""
    pytest_output = ""
    if not files:
        return pytest_output

    for test_file in files:
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
    print("pytest_output:", pytest_output)
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
            pylint_output_local += result.stdout
        except subprocess.CalledProcessError as e:
            pylint_output_local += (
                f"Error running pylint on {file_path}: {e}\nstdout: {e.stdout}"
            )
    return pylint_output_local


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
        ruff_output_local = f"stdout: {result.stdout}"
    except subprocess.CalledProcessError as e:
        ruff_output = f"Error running ruff fix: {e}\n{e.stdout}"
        return False, ruff_output
    ruff_output = ""
    return True, ruff_output


def run_radon_cc(files):
    """Runs radon cc on the specified files and captures the output."""
    radon_cc_output = ""
    for file_path in files:
        try:
            result = subprocess.run(
                ["radon", "cc", file_path],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            radon_cc_output += result.stdout
        except subprocess.CalledProcessError as e:
            radon_cc_output += (
                f"Error running radon cc on {file_path}: {e}\nstdout: {e.stdout}"
            )
    return radon_cc_output


def run_radon_mi(files):
    """Runs radon mi on the specified files and captures the output."""
    radon_mi_output = ""
    for file_path in files:
        try:
            result = subprocess.run(
                ["radon", "mi", file_path],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            radon_mi_output += result.stdout
        except subprocess.CalledProcessError as e:
            radon_mi_output += (
                f"Error running radon mi on {file_path}: {e}\nstdout: {e.stdout}"
            )
    return radon_mi_output


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


import requests

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


def call_aider(file_paths, model, combined_output):
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
                "--subtree-only",
                # "--restore-chat-history",
            ]
            + ["--model", model]
            + [item for file_path in file_paths for item in ["--file", file_path]]
            + ["--file", "notes.md"]
            + ["--file", "questions.md"]
            + ["--chat-history-file", ".rtaf_aider.chat.history.md"]
            # + ["--max-chat-history-tokens", "10000"]
            + [
                "--message",
                (
                    f"{DEBUGGING_AND_TESTING_CONTENT}\n\n\nDon't work on too many things at the same time. "
                    "There are multiple LLMs working on this project, if you have information that could be useful for others, "
                    "please update notes.md. If you have questions, please write them into questions.md. "
                    "I might update the notes.md with answers to those questions. If you have commands I should run, "
                    "please put them into commands.sh. Refactor notes.md and questions.md when necessary to avoid redundancy "
                    f"and to reduce length. Output: {combined_output}. What should we do next? Implement your suggestions."
                ),
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
        help="Number of random pytest files to run when --pytest-mode is 'selected'.",
    )
    parser.add_argument(
        "--pytest-mode",
        type=str,
        choices=["all", "selected"],
        default="all",
        help="Mode for running pytest tests. 'all' runs all tests, 'selected' runs a random selection.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek",
        help="Model to use for aider.",
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
        default=100,
        help="Number of iterations to run the tests and fixes.",
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
        if args.pytest_mode == "all":
            pytest_output = run_pytest()
        else:
            pytest_output = run_random_pytest(selected_test_files)
        num_pytest_output_chars = len(pytest_output)
        print("num_pytest_output_chars:", num_pytest_output_chars)
        pylint_result_output = (
            run_random_pylint(selected_files) if selected_files else ""
        )
        files_potentially_being_tested = []
        if False:
            for file in all_python_files:
                for test_file in selected_test_files:
                    if test_file.replace(".py", "").startswith("test_"):
                        files_potentially_being_tested.append(file)
                    if test_file.replace(".py", "").split("test_")[1] in file:
                        files_potentially_being_tested.append(file)

            radon_cc_output = run_radon_cc(files_potentially_being_tested)
            radon_mi_output = run_radon_mi(files_potentially_being_tested)

            print("files_potentially_being_tested:", files_potentially_being_tested)
        combined_output = (
            f"Pylint output:\n{pylint_result_output}\nPytest output:\n{pytest_output}"
        ).strip()
        if "All checks passed" not in ruff_output:
            combined_output += f"\nRuff output:\n{ruff_output}"
        # if radon_cc_output:
            # combined_output += f"\nRadon CC output:\n{radon_cc_output}"
        # if radon_mi_output:
            # combined_output += f"\nRadon MI output:\n{radon_mi_output}"
        files_to_fix = filter_files_by_output(combined_output, all_python_files)
        files_to_fix.extend(files_potentially_being_tested)
        files_to_fix.extend(selected_files)
        files_to_fix.extend(selected_test_files)

        files_to_fix_local = list(set(files_to_fix))
        # sort
        files_to_fix.sort()
        run_black(files_to_fix)
        files_to_fix = []
        if combined_output:
            call_aider(files_to_fix, args.model, combined_output)
        if (
            args.pytest_mode == "all"
            and pylint_success
            and ruff_success
            and not files_to_fix
            and "All tests passed" in pytest_output
        ):
            print("No more issues found. Stopping early.")
            break
        if (
            args.pytest_mode == "selected"
            and pylint_success
            and ruff_success
            and not files_to_fix
            and "All tests passed" in pytest_output
        ):
            print("No more issues found. Stopping early.")
            break
        if (
            args.pytest_mode == "selected"
            and pylint_success
            and ruff_success
            and not files_to_fix
            and "All tests passed" in pytest_output
        ):
            print("No more issues found. Stopping early.")
            break

    print("All iterations completed.")
