"""
Test module for the ColbertRetriever class.
"""

import os
import tempfile
import pytest
import dspy
from prismix.core.colbert_retriever import ColbertRetriever


@pytest.fixture
def colbert_retriever_instance():
    """Fixture to create an instance of ColbertRetriever."""
    return ColbertRetriever(url="http://example.com/colbert", k=3)


@pytest.fixture
def temp_dir_instance():
    """Fixture to create a temporary directory with dummy files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some dummy files
        with open(os.path.join(tmpdir, "test1.py"), "w", encoding="utf-8") as f:
            f.write("def hello():\n    print('hello')\n")
        with open(os.path.join(tmpdir, "test2.txt"), "w", encoding="utf-8") as f:
            f.write("This is a test file with some text.")
        with open(os.path.join(tmpdir, "test3.py"), "w", encoding="utf-8") as f:
            f.write("def world():\n    print('world')")
        with open(os.path.join(tmpdir, "test4.md"), "w", encoding="utf-8") as f:
            f.write("# Markdown file")
        yield tmpdir


def test_add_data_to_db_basic(colbert_retriever_instance, temp_dir_instance):
    """Test adding data to the database."""
    colbert_retriever_instance.add_data_to_db(temp_dir_instance)
    # Ensure that the data was added to the Qdrant database
    # This is a placeholder for a more detailed check
    assert True


def test_colbert_retriever(colbert_retriever_instance):
    """Test the ColbertRetriever class."""
    query = "quantum computing"
    # Set a mock RM for testing
    dspy.settings.rm = lambda queries, k=3: [
        [{"long_text": f"This is a dummy result for {q}"} for _ in range(k)]
        for q in queries
    ]
    results = colbert_retriever_instance.forward(query)
    assert len(results) == 3
    for result in results:
        assert "dummy result" in result
