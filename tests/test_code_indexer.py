"""
Test module for the CodeIndexer class.
"""

import os
import tempfile

import pytest

from prismix.core.code_indexer import CodeIndexer, IndexedCode
from prismix.core.file_operations import FileManager, DefaultFileOperations


@pytest.fixture
def code_indexer():
    """Fixture to create an instance of CodeIndexer."""
    file_manager = FileManager(DefaultFileOperations())
    return CodeIndexer(file_manager)


@pytest.fixture
def temp_dir():
    """Fixture to create a temporary directory with dummy files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some dummy files
        with open(os.path.join(tmpdir, "test1.py"), "w", encoding="utf-8") as f:
            f.write("def hello():\n    print('hello')\n")
        with open(os.path.join(tmpdir, "test2.txt"), "w", encoding="utf-8") as f:
            f.write("This is a test file with some text.")
        with open(os.path.join(tmpdir, "test3.py"), "w", encoding="utf-8") as f:
            f.write("def world():\n    print('world')\n")
        yield tmpdir


def test_search_code_on_the_fly(indexer, temp_directory):
    """Test the search_code_on_the_fly method."""
    # Test search with a query that exists in some files
    results = indexer.search_code_on_the_fly(temp_directory, "print")
    assert len(results) == 2
    assert any("test1.py" in r.filepath for r in results)
    assert any("test3.py" in r.filepath for r in results)
    assert all(isinstance(r, IndexedCode) for r in results)

    # Test search with a query that does not exist
    results = indexer.search_code_on_the_fly(temp_directory, "nonexistent")
    assert len(results) == 0

    # Test search with a query that exists in a specific file
    results = indexer.search_code_on_the_fly(temp_directory, "test file")
    assert len(results) == 1
    assert any("test2.txt" in r.filepath for r in results)

    # Test search with a query that is a substring of another word
    results = indexer.search_code_on_the_fly(temp_directory, "wor")
    assert len(results) == 1
    assert any("test3.py" in r.filepath for r in results)


import os
import tempfile
import pytest
from prismix.core.code_indexer import CodeIndexer, IndexedCode
from prismix.core.file_operations import FileManager, DefaultFileOperations
