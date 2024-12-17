from pymilvus import MilvusClient
"""
Module for setting up and interacting with a local Milvus database.
"""

from pymilvus import MilvusClient
import numpy as np
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Path to the local database file
DB_FILE = "./milvus_demo.db"


def setup_milvus_local_db():
    """Setup the local Milvus database and create a collection."""
    try:
        client = MilvusClient(DB_FILE)
        logging.info("MilvusClient initialized successfully.")
        client.create_collection(
            collection_name="demo_collection",
            dimension=384,  # Adjust as needed
            index_file_size=1024,  # Optional parameter
        )
        logging.info("Milvus local database setup complete.")
    except Exception as e:
        logging.error("Error setting up Milvus local database: %s", e)


def insert_data_into_milvus():
    """Insert sample data into the Milvus collection."""
    try:
        client = MilvusClient(DB_FILE)
        docs = [
            "Künstliche Intelligenz wurde als akademische Disziplin im Jahr 1956 gegründet.",
            "Alan Turing war der erste Mensch, der umfangreiche Forschung in der KI durchführte.",
            "Turing wurde in Maida Vale, London, geboren und wuchs in Südengland auf.",
        ]
        vectors = [
            [np.random.uniform(-1, 1) for _ in range(384)] for _ in range(len(docs))
        ]
        data = [{"text": doc, "vector": vector} for doc, vector in zip(docs, vectors)]
        client.insert(collection_name="demo_collection", data=data)
        logging.info("Data successfully inserted into the collection.")
        logging.info("Inserted %d documents.", len(data))
    except Exception as e:
        logging.error("Error inserting data into Milvus: %s", e)


def search_milvus_collection():
    """Search the Milvus collection for similar documents."""
    try:
        client = MilvusClient(DB_FILE)
        search_vectors = [[np.random.uniform(-1, 1) for _ in range(384)]]
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        result = client.search(
            collection_name="demo_collection",
            data=search_vectors,
            anns_field="vector",
            param=search_params,
            limit=3,
        )
        logging.info("Search results:")
        if len(result) == 0:
            logging.info("No results found.")
        for res in result:
            logging.info("Document: %s, Distance: %s", res['text'], res['distance'])
    except Exception as e:
        logging.error("Error searching Milvus collection: %s", e)


def main():
    """Main function to setup, insert data, and search in Milvus."""
    logging.info("Starting Milvus local database setup...")
    setup_milvus_local_db()

    logging.info("Inserting sample data into Milvus...")
    insert_data_into_milvus()

    logging.info("Searching Milvus collection...")
    search_milvus_collection()

    print("Script execution completed.")


if __name__ == "__main__":
    main()
