import glob
from typing import List

from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Batch, PointStruct
from sentence_transformers import SentenceTransformer


class QdrantRetriever:
    """Manages Qdrant operations for storing and querying text."""

    def __init__(self, collection_name: str = "my_documents", embedding_size: int = 768):
        self.client = QdrantClient(":memory:")
        self.collection_name = collection_name
        self.embedding_size = embedding_size
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self._create_collection()

    def _create_collection(self):
        """Creates the Qdrant collection if it doesn't exist."""
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(size=self.embedding_size, distance=models.Distance.COSINE),
        )

    def add_files(self, include_glob: str, exclude_glob: str = None):
        """Adds files matching the include glob, excluding those matching the exclude glob."""
        files = glob.glob(include_glob, recursive=True)
        if exclude_glob:
            exclude_files = glob.glob(exclude_glob, recursive=True)
            files = [f for f in files if f not in exclude_files]

        for file_path in files:
            with open(file_path, 'r') as f:
                file_content = f.read()
                self.add_text(file_path, file_content)

    def add_text(self, file_path: str, text: str):
        """Adds a text document to the Qdrant collection."""
        embedding = self.model.encode(text).tolist()
        point = PointStruct(id=hash(file_path), vector=embedding, payload={"file_path": file_path, "text": text})
        self.client.upsert(collection_name=self.collection_name, points=Batch(points=[point]))

    def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        """Retrieves the top_k most relevant documents for a given query."""
        query_embedding = self.model.encode(query).tolist()
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
        )
        return [hit.payload["text"] for hit in search_result]

if __name__ == "__main__":
    retriever = QdrantRetriever()
    retriever.add_files(include_glob="*.py", exclude_glob="*test*")
    print("Added all python files (excluding test files)")

    query = "how to add line numbers to a file"
    results = retriever.retrieve(query)
    print(f"\nRetrieved results for query: '{query}':")
    for i, result in enumerate(results):
        print(f"{i+1}: {result[:200]}...")
