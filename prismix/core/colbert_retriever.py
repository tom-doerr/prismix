"""
Module for retrieving and managing code embeddings using Qdrant and CodeIndexer.
"""

import dspy
import os
import logging
from typing import List
from prismix.core.qdrant_manager import QdrantManager
from prismix.core.code_indexer import CodeIndexer, IndexedCode
from prismix.core.file_operations import FileManager


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
            file_context = FileManager().read_file(filepath)
            if file_context and file_context.content:
                embedding = indexer._embed_code(file_context.content)
                indexer.indexed_code[filepath] = IndexedCode(
                    filepath, file_context.content, embedding
                )
                print(f"Added to db: {filepath}")
        except IOError as e:
            logging.error(f"Error reading file {filepath}: {e}")


from prismix.core.qdrant_manager import QdrantManager

import logging


class DataInserter:
    def __init__(self, qdrant_manager: QdrantManager):
        self.qdrant_manager = qdrant_manager

    def add_data_to_db(self, directory: str):
        indexer = CodeIndexer()
        files_to_index = get_all_files_to_index(directory)
        for filepath in files_to_index:
            try:
                file_context = FileManager().read_file(filepath)
                if file_context and file_context.content:
                    embedding = indexer._embed_code(file_context.content)
                    self.qdrant_manager.insert_embeddings(
                        [
                            {
                                "id": filepath,
                                "vector": embedding,
                                "payload": {"content": file_context.content},
                            }
                        ]
                    )
                    logging.info("Added to Qdrant: %s", filepath)
            except Exception as e:
                logging.error(f"Error adding {filepath} to Qdrant: {e}")


class ColbertRetriever(dspy.Retrieve):
    def __init__(self, url: str, k: int = 3):
        super().__init__(k=k)
        self.url = url
        self.qdrant_manager = QdrantManager(collection_name="colbert_embeddings")
        self.data_inserter = DataInserter(self.qdrant_manager)
        dspy.settings.configure(lm=dspy.OpenAI(api_key="your_openai_api_key"))

    def add_data_to_db(self, directory: str):
        self.data_inserter.add_data_to_db(directory)


import logging


def forward(self, query: str, k: int = None) -> List[str]:
    """Search for similar embeddings in Qdrant."""
    query_embedding = self.qdrant_manager._embed_code(query)
    results = self.qdrant_manager.search_embeddings(query_embedding, top_k=k or self.k)
    return [result["payload"]["content"] for result in results]


from prismix.core.file_operations import FileManager
from prismix.core.code_indexer import CodeIndexer
import logging
