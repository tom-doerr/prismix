"""
CodeIndexer module: Indexes and searches code files using embeddings.
"""

import os
import fnmatch
from typing import List, Dict
from dataclasses import dataclass
from prismix.core.file_operations import FileManager

from prismix.core.file_operations import DefaultFileOperations

file_manager = FileManager(file_operations=DefaultFileOperations())


@dataclass
class IndexedCode:
    filepath: str
    content: str
    embedding: List[float]  # Placeholder for embedding


class CodeEmbedder:
    """Class responsible for embedding code content into vectors."""

    def embed_code(self) -> List[float]:
        """Embed the given code content into a vector."""
        # Placeholder for embedding logic
        return [0.0] * 128  # Dummy embedding

    def another_method(self):
        """Another method in the CodeEmbedder class."""


class CodeIndexer:
    """
    Class responsible for indexing and searching code files using embeddings.

    This class provides methods to index code files in a directory and search for
    code snippets based on a query using embeddings.
    """

    DEFAULT_IGNORE_PATTERNS = ["*.pyc", "__pycache__"]

    def __init__(
        self, embedder: CodeEmbedder = None, ignore_patterns: List[str] = None
    ):
        """Initialize the CodeIndexer with an optional embedder and ignore patterns."""
        if embedder is None:
            embedder = CodeEmbedder()
        self.embedder = embedder
        self.ignore_patterns = ignore_patterns or self.DEFAULT_IGNORE_PATTERNS
        self.indexed_code: Dict[str, IndexedCode] = {}

    def index_directory(self, directory: str) -> None:
        """Index all code files in the given directory."""
        for root, _, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                if not self._is_ignored(filepath):
                    try:
                        file_context = FileManager(
                            file_operations=DefaultFileOperations()
                        ).read_file(filepath)
                        if file_context and file_context.content:
                            embedding = self.embedder.embed_code(file_context.content)
                            indexed_code = IndexedCode(
                                filepath, file_context.content, embedding
                            )
                            self.indexed_code[filepath] = indexed_code
                            print(
                                f"Indexed: {filepath}"
                            )  # Consider logging instead of printing
                    except (FileNotFoundError, PermissionError) as e:
                        print(f"Error accessing {filepath}: {e}")
                    except Exception as e:
                        print(
                            f"Unexpected error indexing {filepath}: {e}"
                        )  # Consider logging instead of printing

    def embed_code(self, content: str) -> List[float]:
        """Embed the given code content into a vector."""
        return self.embedder.embed_code(content)

    def search_code(self, query: str) -> List[IndexedCode]:
        """Search indexed code using a query."""
        query_embedding = self.embed_code(query)
        results = []
        for _, indexed_code in self.indexed_code.items():
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
                        file_context = FileManager(
                            file_operations=DefaultFileOperations()
                        ).read_file(filepath)
                        if (
                            file_context
                            and file_context.content
                            and query in file_context.content
                        ):
                            embedding = self.embedder.embed_code(file_context.content)
                            indexed_code = IndexedCode(
                                filepath, file_context.content, embedding
                            )
                            results.append(indexed_code)
                    except (FileNotFoundError, PermissionError) as e:
                        print(f"Error accessing {filepath}: {e}")
                    except Exception as e:
                        print(f"Unexpected error searching {filepath}: {e}")
        return results

    def _is_ignored(self, filepath: str) -> bool:
        """Check if the file should be ignored based on the ignore patterns."""
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(filepath, pattern):
                return True
        return False

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
