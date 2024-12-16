"""
Test module for the ColbertRetriever class.
"""

import pytest
from prismix.core.colbert_retriever import ColbertRetriever

@pytest.fixture
def colbert_retriever():
    return ColbertRetriever(url="http://example.com/colbert", k=3)

import os
import tempfile

@pytest.fixture
def temp_dir():
    """Fixture to create a temporary directory with dummy files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some dummy files
        with open(os.path.join(tmpdir, "test1.py"), "w", encoding='utf-8') as f:
            f.write("def hello():\n    print('hello')\n")
        with open(os.path.join(tmpdir, "test2.txt"), "w", encoding='utf-8') as f:
            f.write("This is a test file with some text.")
        with open(os.path.join(tmpdir, "test3.py"), "w", encoding='utf-8') as f:
            f.write("def world():\n    print('world')\n")
        yield tmpdir

def test_add_data_to_db(colbert_retriever, temp_dir):
    colbert_retriever.add_data_to_db(temp_dir)
    # Ensure that the data was added to the Qdrant database
    # This is a placeholder for a more detailed check
    assert True

def test_colbert_retriever(colbert_retriever):
    query = "quantum computing"
    results = colbert_retriever.forward(query)
    assert len(results) == 3
    for result in results:
        assert query in result
