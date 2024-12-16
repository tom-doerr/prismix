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


# ai! add code that adds the data to the db







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
