import dspy
import os
from typing import List
from prismix.core.code_indexer import CodeIndexer


def get_all_files_to_index(directory: str) -> List[str]:
    """Get all files that should be added to the index."""
    indexer = CodeIndexer()
    files_to_index = []
    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            if not indexer._is_ignored(filepath):
                files_to_index.append(filepath)
    return files_to_index


def add_data_to_db(directory: str):
    """Add data to the database."""
    indexer = CodeIndexer()
    files_to_index = get_all_files_to_index(directory)
    for filepath in files_to_index:
        try:
            file_context = FileManager.read_file(filepath)
            if file_context and file_context.content:
                embedding = indexer._embed_code(file_context.content)
                indexer.indexed_code[filepath] = IndexedCode(
                    filepath, file_context.content, embedding
                )
                print(f"Added to db: {filepath}")
        except Exception as e:
            print(f"Error adding {filepath} to db: {e}")







class ColbertRetriever(dspy.Retrieve):
    def __init__(self, url: str, k: int = 3):
        super().__init__(k=k)
        self.url = url

    def forward(self, query: str, k: int = None) -> List[str]:
        # Placeholder for actual Colbert retrieval logic
        # In a real implementation, this would send the query to the Colbert server
        # and retrieve the top-k passages based on semantic similarity.
        print(f"Retrieving top-{k or self.k} passages for query: {query}")
        # Dummy return for now
        return [f"Passage {i+1} for query: {query}" for i in range(k or self.k)]
