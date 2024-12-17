"""
Manages Qdrant operations for storing and querying ColBERT embeddings.
"""

import logging
from typing import List, Dict
from qdrant_client import QdrantClient, models


class QdrantManager:
    """Manages Qdrant operations for storing and querying ColBERT embeddings."""

    def __init__(self, collection_name: str = "colbert_embeddings"):
        self.client = QdrantClient(":memory:")
        self.collection_name = collection_name
        self._create_collection()
        logging.basicConfig(level=logging.INFO)

    def _create_collection(self):
        """Create a Qdrant collection with the appropriate configuration."""
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=128,
                    distance=models.Distance.COSINE,
                ),
            )
            logging.info("Collection '%s' created.", self.collection_name)
        else:
            logging.info("Collection '%s' already exists.", self.collection_name)

    def insert_embeddings(self, embeddings: List[Dict[str, any]]):
        """Insert embeddings into the Qdrant collection."""
        self.client.upsert(
            collection_name=self.collection_name,
            points=embeddings,
        )
        logging.info("Embeddings inserted into collection '%s'.", self.collection_name)


    def _embed_code(self, content: str) -> List[float]:
        return self.embed_code(content)

    def search_embeddings(
        self, query_embedding: List[float], top_k: int = 3
    ) -> List[Dict[str, any]]:
        """Search for similar embeddings in the Qdrant collection."""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
        )
        if not results:
            logging.warning("No results found for query embedding: %s", query_embedding)
        else:
            logging.info("Found %d results for query embedding.", len(results))
        return results
