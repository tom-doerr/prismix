import glob
import os
from typing import List

import requests
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Batch
from sentence_transformers import SentenceTransformer


class QdrantRetriever:
    """Manages Qdrant operations for storing and querying text."""

    def __init__(self, collection_name: str = "my_documents"):
        self.client = QdrantClient(":memory:")
        self.collection_name = collection_name
        self.jina_api_key = os.environ.get("JINA_API_KEY")
        self.jina_model = "jina-embeddings-v3"
        self.model = None
        if not self.jina_api_key:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self._create_collection()

    def _create_collection(self):
        """Creates the Qdrant collection if it doesn't exist."""
        if self.model:
            embedding_size = self.model.get_sentence_embedding_dimension()
        else:
            embedding_size = 256
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(size=embedding_size, distance=models.Distance.COSINE),
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
        embedding = self._get_jina_embedding(text)
        point_id = hash(file_path)
        self.client.upsert(
            collection_name=self.collection_name,
            points=Batch(
                ids=[point_id],
                vectors=[embedding],
                payloads=[{"file_path": file_path, "text": text}]
            )
        )

    def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        """Retrieves the top_k most relevant documents for a given query."""
        if self.model:
            query_embedding = self.model.encode(query).tolist()
        else:
            query_embedding = self._get_jina_embedding(query)
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
        )
        return [hit.payload["text"] for hit in search_result]

    def _get_jina_embedding(self, text: str) -> List[float]:
        """Gets the Jina embedding for the given text."""
        if self.jina_api_key:
            url = "https://api.jina.ai/v1/embeddings"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jina_api_key}",
            }
            data = {
                "input": [text],
                "model": self.jina_model,
                "dimensions": self.embedding_size,
                "task": "retrieval.passage",
                "late_chunking": True,
            }
            response = requests.post(url, headers=headers, json=data)
            if response.status_code != 200:
                raise Exception(f"Jina API request failed with status code: {response.status_code}, response: {response.text}")
            response_json = response.json()
            if "data" in response_json and response_json["data"]:
                embeddings = response_json["data"][0]["embedding"]
                return embeddings
            else:
                raise KeyError(f"Unexpected response structure: {response_json}")
        else:
            return self.model.encode(text).tolist()


if __name__ == "__main__":
    retriever = QdrantRetriever()
    retriever.add_files(include_glob="*.py", exclude_glob="*test*")
    print("Added all python files (excluding test files)")

    query = "how to add line numbers to a file"
    results = retriever.retrieve(query)
    print(f"\nRetrieved results for query: '{query}':")
    for i, result in enumerate(results):
        print(f"{i+1}: {result[:200]}...")
