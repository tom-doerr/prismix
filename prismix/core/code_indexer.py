import os
import fnmatch
from typing import List, Dict
from dataclasses import dataclass
from prismix.core.file_operations import FileManager


@dataclass
class IndexedCode:
    filepath: str
    content: str
    embedding: List[float]  # Placeholder for embedding


class CodeEmbedder:
    def embed_code(self, content: str) -> List[float]:
        # Placeholder for embedding logic
        return [0.0] * 128  # Dummy embedding


class CodeIndexer:
    DEFAULT_IGNORE_PATTERNS = ["*.pyc", "__pycache__"]

    def __init__(self, embedder: CodeEmbedder = None, ignore_patterns: List[str] = None):
        if embedder is None:
            embedder = CodeEmbedder()
        self.embedder = embedder
        self.ignore_patterns = ignore_patterns or self.DEFAULT_IGNORE_PATTERNS
        self.indexed_code: Dict[str, IndexedCode] = {}

    def index_directory(self, directory: str) -> None:
        for root, _, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                if not self._is_ignored(filepath):
                    try:
                        file_context = FileManager.read_file(filepath)
                        if file_context and file_context.content:
                            embedding = self.embedder.embed_code(file_context.content)
                            indexed_code = IndexedCode(
                                filepath, file_context.content, embedding
                            )
                            self.indexed_code[filepath] = indexed_code
                            print(f"Indexed: {filepath}")
                    except Exception as e:
                        print(f"Error indexing {filepath}: {e}")

    def search_code(self, query: str) -> List[IndexedCode]:
        """Search indexed code using a query."""
        query_embedding = self._embed_code(query)
        results = []
        for filepath, indexed_code in self.indexed_code.items():
            similarity = self._similarity(query_embedding, indexed_code.embedding)
            if similarity > 0.5:  # Arbitrary threshold for now
                results.append(indexed_code)
        return results

    def search_code_on_the_fly(self, directory: str, query: str) -> List[IndexedCode]:
        """Search code files in the given directory without using an index."""
        results = []
        for root, _, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                if not self._is_ignored(filepath):
                    try:
                        file_context = FileManager.read_file(filepath)
                        if (
                            file_context
                            and file_context.content
                            and query in file_context.content
                        ):
                            embedding = self._embed_code(file_context.content)
                            indexed_code = IndexedCode(
                                filepath, file_context.content, embedding
                            )
                            results.append(indexed_code)
                    except Exception as e:
                        print(f"Error searching {filepath}: {e}")
        return results

    def _is_ignored(self, filepath: str) -> bool:
        """Check if the file should be ignored based on the ignore patterns."""
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(filepath, pattern):
                return True
        return False
                    try:
                        file_context = FileManager.read_file(filepath)
                        if (
                            file_context
                            and file_context.content
                            and query in file_context.content
                        ):
                            embedding = self._embed_code(file_context.content)
                            indexed_code = IndexedCode(
                                filepath, file_context.content, embedding
                            )
                            results.append(indexed_code)
                    except Exception as e:
                        print(f"Error searching {filepath}: {e}")
        return results

    def _similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Calculate the similarity between two embeddings using cosine similarity."""
        dot_product = sum(x * y for x, y in zip(emb1, emb2))
        magnitude1 = sum(x**2 for x in emb1) ** 0.5
        magnitude2 = sum(y**2 for y in emb2) ** 0.5
        return (
            dot_product / (magnitude1 * magnitude2)
            if magnitude1 and magnitude2
            else 0.0
        )
