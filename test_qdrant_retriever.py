import os

import pytest

from qdrant_retriever import QdrantRetriever


@pytest.fixture
def qdrant_retriever():
    """Fixture to create a QdrantRetriever instance for testing."""
    retriever = QdrantRetriever(collection_name="test_collection")
    retriever.clear_collection()  # Ensure a clean collection for each test
    return retriever


def test_add_and_retrieve_code_chunks(qdrant_retriever):
    """Tests adding and retrieving code chunks."""
    test_file_path = "test_file.py"
    test_file_content = """
def hello():
    print("hello")

class MyClass:
    def __init__(self):
        pass
"""
    qdrant_retriever.add_or_update_code_chunks(test_file_path, test_file_content)
    results = qdrant_retriever.retrieve("hello")
    assert len(results) > 0
    assert "hello" in results[0][1]
    assert test_file_path == results[0][0]

def test_add_and_retrieve_code_chunks_with_jina(qdrant_retriever):
    """Tests adding and retrieving code chunks with Jina embeddings."""
    if not os.environ.get("JINA_API_KEY"):
        pytest.skip("JINA_API_KEY not set, skipping Jina test")
    test_file_path = "test_file.py"
    test_file_content = """
def hello():
    print("hello")

class MyClass:
    def __init__(self):
        pass
"""
    qdrant_retriever.jina_api_key = os.environ.get("JINA_API_KEY")
    qdrant_retriever.add_or_update_code_chunks(test_file_path, test_file_content)
    results = qdrant_retriever.retrieve("hello")
    assert len(results) > 0
    assert "hello" in results[0][1]
    assert test_file_path == results[0][0]


def test_add_and_retrieve_code_chunks_no_ast(qdrant_retriever):
    """Tests adding and retrieving code chunks when AST parsing fails."""
    test_file_path = "test_file.py"
    test_file_content = "this is not valid python code"
    qdrant_retriever.add_or_update_code_chunks(test_file_path, test_file_content)
    results = qdrant_retriever.retrieve("not valid")
    assert len(results) > 0
    assert "not valid" in results[0][1]
    assert test_file_path == results[0][0]


def test_file_change_detection(qdrant_retriever):
    """Tests if file change detection works correctly."""
    test_file_path = "test_file.py"
    test_file_content_1 = "def hello():\n    print('hello')"
    test_file_content_2 = "def hello():\n    print('hello world')"

    qdrant_retriever.add_or_update_code_chunks(test_file_path, test_file_content_1)
    results1 = qdrant_retriever.retrieve("hello")
    assert "hello" in results1[0][1]

    qdrant_retriever.add_or_update_code_chunks(test_file_path, test_file_content_2)
    results2 = qdrant_retriever.retrieve("hello")
    assert "hello world" in results2[0][1]


def test_clear_collection(qdrant_retriever):
    """Tests if the clear collection method works correctly."""
    test_file_path = "test_file.py"
    test_file_content = "def hello():\n    print('hello')"
    qdrant_retriever.add_or_update_code_chunks(test_file_path, test_file_content)
    results = qdrant_retriever.retrieve("hello")
    assert len(results) > 0

    qdrant_retriever.clear_collection()
    results = qdrant_retriever.retrieve("hello")
    assert len(results) == 0
