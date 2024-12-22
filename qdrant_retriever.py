import ast
import glob
import hashlib
import os
from typing import List

import requests
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Batch
from sentence_transformers import SentenceTransformer


class QdrantRetriever:
    """Manages Qdrant operations for storing and querying text."""

    def __init__(self, collection_name: str = "my_documents"):
        self.client = QdrantClient(path="./qdrant_data")
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
                self.add_or_update_code_chunks(file_path, file_content)

    def add_or_update_code_chunks(self, file_path: str, file_content: str):
        """Adds or updates code chunks in the Qdrant collection."""
        file_hash = self._hash_file_content(file_content)
        if self._check_if_file_changed(file_path, file_hash):
            self._delete_chunks_for_file(file_path)
            self._add_code_chunks(file_path, file_content)
        else:
            self._add_code_chunks(file_path, file_content)

    def _add_code_chunks(self, file_path: str, file_content: str):
        """Adds code chunks to the Qdrant collection."""
        try:
            tree = ast.parse(file_content)
            self._extract_chunks_recursive(file_path, file_content, tree, 0)
        except SyntaxError:
            self._add_chunk(file_path, file_content, 1)

    def _add_chunk(self, file_path: str, code_chunk: str, start_line: int):
        """Adds a single code chunk to the Qdrant collection."""
        embedding = self._get_jina_embedding(code_chunk)
        point_id = hash(f"{file_path}-{start_line}")
        if not self._check_if_chunk_exists(point_id):
            self.client.upsert(
                collection_name=self.collection_name,
                points=Batch(
                    ids=[point_id],
                    vectors=[embedding],
                    payloads=[{"file_path": file_path, "text": code_chunk, "start_line": start_line, "file_hash": self._hash_file_content(code_chunk)}]
                )
            )

    def _check_if_chunk_exists(self, point_id: int) -> bool:
        """Checks if a chunk with the given ID already exists in the collection."""
        try:
            self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id],
            )
            return True
        except Exception:
            return False

    def _hash_file_content(self, file_content: str) -> str:
        """Hashes the file content."""
        return hashlib.sha256(file_content.encode()).hexdigest()

    def _check_if_file_changed(self, file_path: str, current_hash: str) -> bool:
        """Checks if the file content has changed."""
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=[0] * 256,  # Dummy vector for metadata search
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="file_path",
                            match=models.MatchValue(value=file_path)
                        )
                    ]
                ),
                limit=1
            )
            if search_result:
                stored_hash = search_result[0].payload.get("file_hash")
                return stored_hash != current_hash
            return True
        except Exception:
            return True

    def _delete_chunks_for_file(self, file_path: str):
        """Deletes all chunks associated with a file path."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="file_path",
                            match=models.MatchValue(value=file_path)
                        )
                    ]
                )
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
        return [(hit.payload["file_path"], hit.payload["text"], hit.payload["start_line"]) for hit in search_result]

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
