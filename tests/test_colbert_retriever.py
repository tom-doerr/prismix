import pytest
from prismix.core.colbert_retriever import ColbertRetriever

@pytest.fixture
def colbert_retriever():
    return ColbertRetriever(url="http://example.com/colbert", k=3)

def test_colbert_retriever(colbert_retriever):
    query = "quantum computing"
    results = colbert_retriever.forward(query)
    assert len(results) == 3
    for result in results:
        assert query in result
