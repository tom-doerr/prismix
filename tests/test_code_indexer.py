import pytest
import tempfile
import os
from prismix.core.code_indexer import CodeIndexer
from prismix.core.file_operations import FileManager


@pytest.fixture
def code_indexer():
    return CodeIndexer()


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some dummy files
        with open(os.path.join(tmpdir, "test1.py"), "w") as f:
            f.write("def hello():\n    print('hello')\n")
        with open(os.path.join(tmpdir, "test2.txt"), "w") as f:
            f.write("This is a test file with some text.")
        with open(os.path.join(tmpdir, "test3.py"), "w") as f:
            f.write("def world():\n    print('world')\n")
        yield tmpdir


def test_search_code_on_the_fly(code_indexer, temp_dir):
    # Test search with a query that exists in some files
    results = code_indexer.search_code_on_the_fly(temp_dir, "print")
    assert len(results) == 2
    assert any("test1.py" in r.filepath for r in results)
    assert any("test3.py" in r.filepath for r in results)

    # Test search with a query that does not exist
    results = code_indexer.search_code_on_the_fly(temp_dir, "nonexistent")
    assert len(results) == 0

    # Test search with a query that exists in a specific file
    results = code_indexer.search_code_on_the_fly(temp_dir, "test file")
    assert len(results) == 1
    assert any("test2.txt" in r.filepath for r in results)

    # Test search with a query that is a substring of another word
    results = code_indexer.search_code_on_the_fly(temp_dir, "wor")
    assert len(results) == 1
    assert any("test3.py" in r.filepath for r in results)
