from pymilvus import MilvusClient
import numpy as np

# Path to the local database file
DB_FILE = "./milvus_demo.db"

def setup_milvus_local_db():
    """Setup the local Milvus database and create a collection."""
    client = MilvusClient(DB_FILE)
    client.create_collection(
        collection_name="demo_collection",
        dimension=384,  # Adjust as needed
        index_file_size=1024,  # Optional parameter
    )
    print("Milvus local database setup complete.")

def insert_data_into_milvus():
    """Insert sample data into the Milvus collection."""
    client = MilvusClient(DB_FILE)
    docs = [
        "Künstliche Intelligenz wurde als akademische Disziplin im Jahr 1956 gegründet.",
        "Alan Turing war der erste Mensch, der umfangreiche Forschung in der KI durchführte.",
        "Turing wurde in Maida Vale, London, geboren und wuchs in Südengland auf.",
    ]
    vectors = [[np.random.uniform(-1, 1) for _ in range(384)] for _ in range(len(docs))]
    data = [
        {"text": doc, "vector": vector} for doc, vector in zip(docs, vectors)
    ]
    client.insert(collection_name="demo_collection", data=data)
    print("Data successfully inserted into the collection.")

def search_milvus_collection():
    """Search the Milvus collection for similar documents."""
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
    print("\nSearch results:")
    for res in result:
        print(f"Document: {res['text']}, Distance: {res['distance']}")
