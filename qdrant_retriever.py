import ast
import glob
import os
import time
from typing import List

import requests
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Batch
from sentence_transformers import SentenceTransformer


class QdrantRetriever:
    """Manages Qdrant operations for storing and querying text."""

    def __init__(self, collection_name: str = "my_documents", path: str = "./qdrant_data"):
        self.client = QdrantClient(path=path)
        self.collection_name = collection_name
        self.jina_api_key = os.environ.get("JINA_API_KEY")
        self.jina_model = "jina-embeddings-v3"
        self.model = None
        if not self.jina_api_key:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self._create_collection()

    def _create_collection(self):
        """Creates the Qdrant collection if it doesn't exist."""
        try:
            if self.model:
                embedding_size = self.model.get_sentence_embedding_dimension()
            else:
                embedding_size = 256
                
            # Check if collection exists first
            collections = self.client.get_collections()
            if not collections:
                raise RuntimeError("Failed to get collections from Qdrant")
                
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                print(f"Creating new collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=embedding_size, 
                        distance=models.Distance.COSINE
                    ),
                )
                print(f"Created collection {self.collection_name} with embedding size {embedding_size}")
        except Exception as e:
            print(f"Error creating collection: {e}")
            raise

    def add_files(self, include_glob: str, exclude_glob: str = None):
        """Adds files matching the include glob, excluding those matching the exclude glob."""
        files = glob.glob(include_glob, recursive=True)
        if exclude_glob:
            exclude_files = glob.glob(exclude_glob, recursive=True)
            files = [f for f in files if f not in exclude_files]
            
        print(f"Indexing {len(files)} files:")
        for file in files:
            print(f"- {file}")

        for file_path in files:
            with open(file_path, 'r') as f:
                file_content = f.read()
                self.add_code_chunks(file_path, file_content)

    def add_code_chunks(self, file_path: str, file_content: str):
        """Collects code chunks from a file to be added to Qdrant."""
        try:
            tree = ast.parse(file_content)
            chunks = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    start_line = node.lineno
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno else start_line
                    code_chunk = '\n'.join(file_content.splitlines()[start_line - 1:end_line])
                    chunks.append((file_path, code_chunk, start_line))
            
            return chunks
        except SyntaxError:
            # Fallback for non-parsable files
            return [(file_path, file_content, 1)]

    def add_files(self, include_glob: str, exclude_glob: str = None, batch_size: int = 32):
        """Adds files matching the include glob, excluding those matching the exclude glob."""
        files = glob.glob(include_glob, recursive=True)
        if exclude_glob:
            exclude_files = glob.glob(exclude_glob, recursive=True)
            files = [f for f in files if f not in exclude_files]
            
        print(f"Indexing {len(files)} files:")
        for file in files:
            print(f"- {file}")

        # Collect all chunks first with progress tracking
        all_chunks = []
        total_files = len(files)
        for i, file_path in enumerate(files):
            try:
                with open(file_path, 'r') as f:
                    file_content = f.read()
                    chunks = self.add_code_chunks(file_path, file_content)
                    all_chunks.extend(chunks)
                    
                # Print progress every 10 files
                if (i + 1) % 10 == 0 or (i + 1) == total_files:
                    print(f"Processed {i+1}/{total_files} files ({len(all_chunks)} chunks)")
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
                continue

        # Get all embeddings in memory first
        all_embeddings = self._get_jina_embeddings([chunk[1] for chunk in all_chunks])

        # Process in batches with statistics
        points = []
        total_chunks = len(all_chunks)
        start_time = time.time()
        
        for i, ((file_path, code_chunk, start_line), embedding) in enumerate(zip(all_chunks, all_embeddings)):
            try:
                point_id = hash(f"{file_path}-{start_line}")
                points.append(models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "file_path": file_path,
                        "text": code_chunk,
                        "start_line": start_line
                    }
                ))
                
                # Upsert in batches
                if len(points) >= batch_size:
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=points
                    )
                    points = []
                    
                    # Print progress every 100 chunks
                    if (i + 1) % 100 == 0 or (i + 1) == total_chunks:
                        elapsed = time.time() - start_time
                        rate = (i + 1) / elapsed if elapsed > 0 else 0
                        print(f"Processed {i+1}/{total_chunks} chunks ({rate:.1f} chunks/sec)")
                        
            except Exception as e:
                print(f"Error processing chunk {i+1}: {e}")
                continue

        # Upsert remaining points
        if points:
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                print(f"Processed final batch of {len(points)} chunks")
            except Exception as e:
                print(f"Error processing final batch: {e}")

    def _add_chunk(self, file_path: str, code_chunk: str, start_line: int):
        """Adds a single code chunk to the Qdrant collection."""
        self._add_chunks_batch([(file_path, code_chunk, start_line)])


    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieves the top_k most relevant documents for a given query.
        
        Args:
            query: The search query
            top_k: Number of results to return
            
        Returns:
            List of tuples containing (file_path, text, start_line)
            
        Raises:
            RuntimeError: If retrieval fails
        """
        try:
            # First try exact string match across all files
            all_files = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000
            )[0]
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve files from Qdrant: {e}")
            
        # Extract specific search text from instruction
        search_text = query
        if " to " in query:
            search_text = query.split(" to ")[0].strip()
            if "change " in search_text:
                search_text = search_text.replace("change ", "").strip()
        
        # Check for exact matches
        exact_matches = []
        for hit in all_files:
            # Skip the test_retriever function itself
            if "test_retriever" in hit.payload["text"]:
                continue
                
            # Look for exact matches of the search text
            if search_text.lower() in hit.payload["text"].lower():
                # Prioritize exact matches at the start of lines
                lines = hit.payload["text"].splitlines()
                for i, line in enumerate(lines):
                    if search_text.lower() in line.lower():
                        # Calculate actual line number
                        actual_line = hit.payload["start_line"] + i
                        exact_matches.append((hit.payload["file_path"], line.strip(), actual_line))
                        break
        
        # Deduplicate matches
        unique_matches = []
        seen = set()
        for match in exact_matches:
            if match[0] not in seen:
                unique_matches.append(match)
                seen.add(match[0])
        
        if unique_matches:
            return unique_matches[:top_k]
            
        # Fall back to semantic search if no exact matches
        if self.model:
            query_embedding = self.model.encode(query).tolist()
        else:
            query_embedding = self._get_jina_embedding(query)
            
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
        )
        
        # Filter out test_retriever function and deduplicate
        results = []
        seen_files = set()
        for hit in search_result:
            if "test_retriever" in hit.payload["text"]:
                continue
            if hit.payload["file_path"] not in seen_files:
                results.append((hit.payload["file_path"], hit.payload["text"], hit.payload["start_line"]))
                seen_files.add(hit.payload["file_path"])
        
        # Log the search results
        print(f"Search results for '{query}':")
        for i, (file_path, text, _) in enumerate(results):
            print(f"{i+1}. {file_path} - {text[:100]}...")
            
        return results

    def _get_jina_embedding(self, text: str) -> List[float]:
        """Gets the Jina embedding for the given text."""
        return self._get_jina_embeddings([text])[0]

    def cleanup_old_collections(self, keep_last_n: int = 3):
        """Cleans up old collections, keeping only the most recent ones."""
        try:
            collections = self.client.get_collections()
            if not collections:
                return
                
            # Sort collections by creation date
            sorted_collections = sorted(
                collections.collections,
                key=lambda c: c.creation_time,
                reverse=True
            )
            
            # Delete old collections
            for collection in sorted_collections[keep_last_n:]:
                print(f"Deleting old collection: {collection.name}")
                self.client.delete_collection(collection.name)
                
        except Exception as e:
            print(f"Error cleaning up collections: {e}")

    def _get_jina_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Gets Jina embeddings for a batch of texts."""
        if self.jina_api_key:
            url = "https://api.jina.ai/v1/embeddings"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jina_api_key}",
            }
            data = {
                "input": texts,
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
                return [item["embedding"] for item in response_json["data"]]
            else:
                raise KeyError(f"Unexpected response structure: {response_json}")
        else:
            return self.model.encode(texts).tolist()


def test_retriever():
    """Test function for directly running the retriever."""
    retriever = QdrantRetriever()
    retriever.add_files(
        include_glob="*.py", 
        exclude_glob="**/{__pycache__,build,dist,.cache,.mypy_cache,.pytest_cache,venv,env,node_modules}/*"
    )
    print("Added all python files (excluding cache/build directories)")

    # Test exact match
    print("\nTesting exact match for 'start jkl'")
    results = retriever.retrieve("start jkl")
    for i, (file_path, text, line_num) in enumerate(results):
        print(f"{i+1}. {file_path} (line {line_num}): {text[:100]}...")

    # Test function search
    print("\nTesting function search for 'print_time_in_china'")
    results = retriever.retrieve("print_time_in_china")
    for i, (file_path, text, line_num) in enumerate(results):
        print(f"{i+1}. {file_path} (line {line_num}): {text[:100]}...")

    # Test semantic search
    print("\nTesting semantic search for 'time in China'")
    results = retriever.retrieve("time in China")
    for i, (file_path, text, line_num) in enumerate(results):
        print(f"{i+1}. {file_path} (line {line_num}): {text[:100]}...")

if __name__ == "__main__":
    test_retriever()
