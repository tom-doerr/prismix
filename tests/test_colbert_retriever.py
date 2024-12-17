"""
Test module for the ColbertRetriever class.
"""

import os
import tempfile
import pytest
from prismix.core.colbert_retriever import ColbertRetriever
from prismix.core.qdrant_manager import QdrantManager


@pytest.fixture
def colbert_retriever():
    """Fixture to create an instance of ColbertRetriever."""
    qdrant_manager = QdrantManager(collection_name="colbert_embeddings")
    qdrant_manager.embed_code = lambda x: [0.0] * 128  # Mock embedding
    return ColbertRetriever(url="http://example.com/colbert", k=3)


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
            f.write("def world():\n    print('world')")
        with open(os.path.join(tmpdir, "test4.md"), "w", encoding="utf-8") as f:
            f.write("# Markdown file")
        yield tmpdir


def test_add_data_to_db_basic(colbert_retriever, temp_dir):
    """Test adding data to the database."""
    colbert_retriever.add_data_to_db(temp_dir)
    # Ensure that the data was added to the Qdrant database
    # This is a placeholder for a more detailed check
    count_result = colbert_retriever_instance.qdrant_manager.client.count(
        collection_name="colbert_embeddings"
    )
    assert (
        colbert_retriever.qdrant_manager.client.count(
            collection_name="colbert_embeddings"
        ).count
        > 0
    )


def test_colbert_retriever(colbert_retriever):
    """Test the ColbertRetriever class."""
    query = "quantum computing"
    colbert_retriever.forward = lambda q: [
        {"long_text": f"This is a dummy result for {q}"} for _ in range(3)
    ]
    results = colbert_retriever_instance.forward(query)
    assert len(results) == 3
    for result in results:
        assert "dummy result" in result["long_text"]
    assert (
        colbert_retriever_instance.qdrant_manager.client.count(
            collection_name="colbert_embeddings"
        ).count  # Access the count attribute
        > 0
    )
