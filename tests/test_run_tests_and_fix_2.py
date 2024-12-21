import argparse
import subprocess
import unittest
from unittest.mock import mock_open, patch

import run_tests_and_fix_2 as run_tests_and_fix


class TestRunTestsAndFix(unittest.TestCase):
    @patch("subprocess.run")
    def test_run_pylint(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Pylint output"
        success, output = run_tests_and_fix.run_pylint()
        self.assertTrue(success)
        self.assertEqual(output, "Pylint output")
        mock_run.assert_called_with(
            ["pylint", "."],
            check=True,
            stdout=-1,
            stderr=-2,
            text=True,
        )

        mock_run.return_value.returncode = 1
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["pylint", "."], stderr="Error output", stdout="Error output"
        )
        success, output = run_tests_and_fix.run_pylint()
        self.assertFalse(success)
        self.assertIn("Error running pylint", output)
        self.assertIn("Error output", output)

    @patch("subprocess.run")
    def test_run_random_pytest(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Pytest output"
        files = ["test1.py", "test2.py"]
        output = run_tests_and_fix.run_random_pytest(files)
        self.assertEqual(output, "Pytest outputPytest output")
        mock_run.assert_called_with(
            ["pytest", "test2.py"],
            check=False,
            stdout=-1,
            stderr=-2,
            text=True,
        )
        mock_run.return_value.returncode = 1
        mock_run.side_effect = subprocess.CalledProcessError(  # type: ignore
            1, ["pytest", "test1.py"], stderr="Error output", stdout="Error output"
        )
        output = run_tests_and_fix.run_random_pytest(files)
        self.assertIn("Error running pytest on test1.py", output)
        self.assertIn("stdout: Error output", output)

        output = run_tests_and_fix.run_random_pytest([])
        self.assertEqual(output, "")

    @patch("subprocess.run")
    def test_run_pytest(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Pytest output"
        output = run_tests_and_fix.run_pytest()
        self.assertEqual(output, "Pytest output")
        mock_run.assert_called_with(
            ["pytest", "-v"], check=False, stdout=-1, stderr=-2, text=True
        )

        mock_run.return_value.returncode = 1
        mock_run.side_effect = subprocess.CalledProcessError(  # type: ignore
            1, ["pytest", "-v"], stderr="Error output", stdout="Error output"
        )
        output = run_tests_and_fix.run_pytest()
        self.assertIn("Error running pytest", output)
        self.assertIn("stdout: Error output", output)

    @patch("subprocess.run")
    def test_run_random_pylint(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Pylint output"
        files = ["file1.py", "file2.py"]
        output = run_tests_and_fix.run_random_pylint(files)
        self.assertEqual(output, "Pylint outputPylint output")
        mock_run.assert_called_with(
            ["pylint", "file2.py"], check=False, stdout=-1, stderr=-2, text=True
        )

        mock_run.return_value.returncode = 1
        mock_run.side_effect = subprocess.CalledProcessError(  # type: ignore
            1, ["pylint", "file1.py"], stderr="Error output", stdout="Error output"
        )
        output = run_tests_and_fix.run_random_pylint(files)
        self.assertIn("Error running pylint on file1.py", output)
        self.assertIn("stdout: Error output", output)

        output = run_tests_and_fix.run_random_pylint([])
        self.assertEqual(output, "")

    @patch("subprocess.run")
    def test_run_ruff_fix(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Ruff output"
        files = ["file1.py", "file2.py"]
        success, output = run_tests_and_fix.run_ruff_fix(files)

        self.assertTrue(success)
        self.assertEqual(output, "stdout: Ruff output")
        mock_run.assert_called_with(
            ["ruff", "check", "./file1.py ./file2.py", "--fix"],
            check=False,
            stdout=-1,
            stderr=-2,
            text=True,
        )

        mock_run.return_value.returncode = 1
        mock_run.side_effect = subprocess.CalledProcessError(
            1,
            ["ruff", "check", "./file1.py ./file2.py", "--fix"],
            stderr="Error output",
            stdout="Error output",
        )
        success, output = run_tests_and_fix.run_ruff_fix(files)
        self.assertFalse(success)
        self.assertIn("Error running ruff fix", output)
        self.assertIn("Error output", output)

    @patch("subprocess.run")
    def test_run_radon_cc(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Radon CC output"
        files = ["file1.py", "file2.py"]
        output = run_tests_and_fix.run_radon_cc(files)
        self.assertEqual(output, "Radon CC outputRadon CC output")
        mock_run.assert_called_with(
            ["radon", "cc", "file2.py"], check=False, stdout=-1, stderr=-2, text=True
        )

        mock_run.return_value.returncode = 1
        mock_run.side_effect = subprocess.CalledProcessError(  # type: ignore
            1, ["radon", "cc", "file1.py"], stderr="Error output", stdout="Error output"
        )
        output = run_tests_and_fix.run_radon_cc(files)
        self.assertIn("Error running radon cc on file1.py", output)
        self.assertIn("stdout: Error output", output)

        output = run_tests_and_fix.run_radon_cc([])
        self.assertEqual(output, "")

    @patch("subprocess.run")
    def test_run_radon_mi(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Radon MI output"
        files = ["file1.py", "file2.py"]
        output = run_tests_and_fix.run_radon_mi(files)
        self.assertEqual(output, "Radon MI outputRadon MI output")
        mock_run.assert_called_with(
            ["radon", "mi", "file2.py"], check=False, stdout=-1, stderr=-2, text=True
        )

        mock_run.return_value.returncode = 1
        mock_run.side_effect = subprocess.CalledProcessError(  # type: ignore
            1, ["radon", "mi", "file1.py"], stderr="Error output", stdout="Error output"
        )
        output = run_tests_and_fix.run_radon_mi(files)
        self.assertIn("Error running radon mi on file1.py", output)
        self.assertIn("stdout: Error output", output)

        output = run_tests_and_fix.run_radon_mi([])
        self.assertEqual(output, "")

    def test_is_test_file(self):
        self.assertFalse(run_tests_and_fix.is_test_file("test_file.py"))
        self.assertTrue(run_tests_and_fix.is_test_file("tests/test_file.py"))
        self.assertFalse(run_tests_and_fix.is_test_file("file.py"))
        self.assertFalse(run_tests_and_fix.is_test_file("some/path/file.py"))

    def test_find_related_files(self):
        with patch("os.path.exists", return_value=True):  # type: ignore
            self.assertEqual(
                run_tests_and_fix.find_related_files("test_file_test.py"),
                ["test_file_test.py", "test_file.py"],
            )
            self.assertEqual(
                run_tests_and_fix.find_related_files("tests/test_file_test.py"),
                ["tests/test_file_test.py", "tests/test_file.py"],
            )
        with patch("os.path.exists", return_value=False):
            self.assertEqual(
                run_tests_and_fix.find_related_files("tests/test_file_test.py"),
                ["tests/test_file_test.py"],
            )
        self.assertEqual(run_tests_and_fix.find_related_files("file.py"), ["file.py"])

    def test_filter_files_by_output(self):
        output = "file1.py:10: Some error\nfile2.py:20: Another error"
        all_files = ["file1.py", "file2.py", "file3.py"]
        self.assertEqual(
            set(run_tests_and_fix.filter_files_by_output(output, all_files)),
            ["file1.py", "file2.py"],
        )
        output = "file1.py:10: Some error\nfile4.py:20: Another error"
        self.assertEqual(
            run_tests_and_fix.filter_files_by_output(output, all_files), ["file1.py"]
        )
        self.assertEqual(run_tests_and_fix.filter_files_by_output("", all_files), [])

    @patch("subprocess.run")
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="test content")
    def test_call_aider(self, mock_file, mock_exists, mock_run):
        files = ["file1.py", "file2.py"]
        run_tests_and_fix.call_aider(files, "deepseek")
        mock_run.assert_called()
        command = mock_run.call_args[0][0]
        self.assertIn("--file", command)
        self.assertIn("file1.py", command)
        self.assertIn("file2.py", command)
        self.assertIn("--model", command)
        self.assertIn("deepseek", command)
        self.assertIn("notes.md", command)
        self.assertIn("questions.md", command)
        self.assertIn("test content", " ".join(command))

        mock_run.side_effect = subprocess.CalledProcessError(  # type: ignore
            1, ["aider"], stderr="Error output", stdout="Error output"
        )
        run_tests_and_fix.call_aider(files, "deepseek")

    @patch("subprocess.run")
    def test_run_black(self, mock_run):
        files = ["file1.py", "file2.py"]
        run_tests_and_fix.run_black(files)
        mock_run.assert_called()
        mock_run.assert_called_with(["black", "file2.py"], check=True)

        mock_run.side_effect = subprocess.CalledProcessError(  # type: ignore
            1, ["black", "file1.py"], stderr="Error output", stdout="Error output"
        )
        run_tests_and_fix.run_black(files)

    @patch("run_tests_and_fix_2.run_pylint")
    @patch("run_tests_and_fix_2.run_ruff_fix")
    @patch("run_tests_and_fix_2.run_random_pytest")
    @patch("run_tests_and_fix_2.run_random_pylint")
    @patch("run_tests_and_fix_2.run_radon_cc")
    @patch("run_tests_and_fix_2.run_radon_mi")
    @patch("run_tests_and_fix_2.filter_files_by_output")
    @patch("run_tests_and_fix_2.call_aider")
    @patch("run_tests_and_fix_2.run_black")
    @patch("glob.glob", return_value=["file1.py", "file2.py", "test_file.py"])
    @patch("argparse.ArgumentParser.parse_args")
    @patch("random.shuffle")
    @patch("tqdm.tqdm", return_value=range(1))
    def test_main_loop(
        self,
        mock_tqdm,
        mock_shuffle,
        mock_glob,
        mock_parse_args,
        mock_run_black,
        mock_call_aider,
        mock_filter_files,
        mock_run_radon_mi,
        mock_run_radon_cc,
        mock_run_random_pylint,
        mock_run_random_pytest,
        mock_run_ruff_fix,
        mock_run_pylint,
    ):
        mock_run_pylint.return_value = True, "Pylint output"
        mock_run_ruff_fix.return_value = True, "Ruff output"
        mock_run_random_pytest.return_value = "Pytest output"
        mock_run_random_pylint.return_value = "Random Pylint output"
        mock_run_radon_cc.return_value = "Radon CC output"
        mock_run_radon_mi.return_value = "Radon MI output"
        mock_filter_files.return_value = ["file1.py"]

        parser = argparse.ArgumentParser()
        parser.add_argument("--pytest-files", type=int, default=1)
        parser.add_argument("--lint-files", type=int, default=1)
        parser.add_argument("--iterations", type=int, default=1)
        parser.add_argument("--model", type=str, default="deepseek")
        args = parser.parse_args()

        run_tests_and_fix.main()

        mock_run_pylint.assert_called_once()
        mock_run_ruff_fix.assert_called_once()
        mock_run_random_pytest.assert_called_once()
        mock_run_random_pylint.assert_called_once()
        mock_run_radon_cc.assert_called_once()
        mock_run_radon_mi.assert_called_once()
        mock_filter_files.assert_called_once()
        mock_call_aider.assert_called_once()
        mock_run_black.assert_called_once()

        mock_run_pylint.return_value = False, "Pylint output"
        run_tests_and_fix.main()
        mock_call_aider.assert_called()
        mock_run_black.assert_called()

        mock_run_pylint.return_value = True, "Pylint output"
        mock_run_ruff_fix.return_value = True, "All checks passed"
        mock_filter_files.return_value = []
        run_tests_and_fix.main()
        mock_call_aider.assert_called()
        mock_run_black.assert_called()


if __name__ == "__main__":
    unittest.main()
