from qdrant_client import QdrantClient, models
from typing import List, Dict

class QdrantManager:
    """Manages Qdrant operations for storing and querying ColBERT embeddings."""

    def __init__(self, collection_name: str = "colbert_embeddings"):
        self.client = QdrantClient(":memory:")
        self.collection_name = collection_name
        self._create_collection()

    def _create_collection(self):
        """Create a Qdrant collection with the appropriate configuration."""
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=128,
                distance=models.Distance.COSINE,
                multivector_config=models.MultiVectorConfig(
                    comparator=models.MultiVectorComparator.MAX_SIM
                ),
            ),
        )

    def insert_embeddings(self, embeddings: List[Dict[str, any]]):
        """Insert embeddings into the Qdrant collection."""
        self.client.upsert(
            collection_name=self.collection_name,
            points=embeddings,
        )

    def search_embeddings(self, query_embedding: List[float], top_k: int = 3) -> List[Dict[str, any]]:
        """Search for similar embeddings in the Qdrant collection."""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
        )
        return results
