"""
Test module for the CodeIndexer class.
"""

import os
import tempfile

import pytest

from prismix.core.code_indexer import CodeEmbedder, CodeIndexer, IndexedCode


@pytest.fixture
def code_indexer_fixture():
    """Fixture to create an instance of CodeIndexer."""
    code_embedder = CodeEmbedder()
    code_embedder.embed_code = lambda x: [0.0] * 128  # Mock embedding
    return CodeIndexer(code_embedder)


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


def test_search_code_on_the_fly(code_indexer_fixture: CodeIndexer, temp_dir: str):
    """Test the search_code_on_the_fly method."""
    indexer = code_indexer_fixture
    directory = temp_dir
    results = indexer.search_code_on_the_fly(directory, "print")
    assert len(results) == 2
    assert any("test1.py" in r.filepath for r in results)
    assert any("test3.py" in r.filepath for r in results)
    assert all(
        isinstance(r, IndexedCode) for r in results
    )  # Check if all results are IndexedCode

    # Test search with a query that does not exist
    results = code_indexer_fixture.search_code_on_the_fly(temp_dir, "nonexistent")
    assert len(results) == 0

    # Test search with a query that exists in a specific file
    results = code_indexer_fixture.search_code_on_the_fly(temp_dir, "test file")
    assert len(results) == 1
    assert any("test2.txt" in r.filepath for r in results)

    # Test search with a query that is a substring of another word
    results = code_indexer_fixture.search_code_on_the_fly(temp_dir, "wor")
    assert len(results) == 1
    assert any("test3.py" in r.filepath for r in results)
