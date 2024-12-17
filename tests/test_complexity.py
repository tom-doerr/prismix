"""
Test module for code complexity using radon.
"""

import subprocess
import pytest

@pytest.mark.parametrize(
    "filepath",
    [
        "prismix/core/code_embedder.py",
        "prismix/core/code_indexer.py",
        "prismix/core/colbert_retriever.py",
        "prismix/core/executor.py",
        "prismix/core/file_editor_module.py",
        "prismix/core/file_operations.py",
        "prismix/core/iterative_programmer.py",
        "prismix/core/qdrant_manager.py",
    ],
)
def test_code_complexity(filepath):
    """Test code complexity using radon."""
    max_complexity = 10  # Set a maximum complexity threshold
    command = ["radon", "cc", filepath]
    result = subprocess.run(command, capture_output=True, text=True, check=False)

    assert result.returncode == 0, f"radon command failed: {result.stderr}"

    output_lines = result.stdout.strip().split("\n")
    for line in output_lines:
        if filepath in line and "average" not in line:
            parts = line.split()
            if len(parts) > 2:
                try:
                    complexity = int(parts[2])
                    assert complexity <= max_complexity, f"Complexity {complexity} exceeds max {max_complexity} in {line}"
                except ValueError:
                    pass # Ignore lines that don't have a complexity score
