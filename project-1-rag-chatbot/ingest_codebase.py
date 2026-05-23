from src.code_loader import load_codebase
from src.embedder import create_vector_store
import sys
import chromadb

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ingest_codebase.py <folder_path> <collection_name>")
        print("Example: python ingest_codebase.py data/codebase/payment-service payment-service")
        sys.exit(1)

    folder = sys.argv[1]
    collection = sys.argv[2]

    client = chromadb.PersistentClient(path="chroma_db")
    existing = [c.name for c in client.list_collections()]
    if collection in existing:
        client.delete_collection(collection)
        print(f"Cleared existing '{collection}' collection.")

    print(f"Scanning: {folder}")
    documents = load_codebase(folder, service=collection)

    if not documents:
        print("No code files found. Check the folder path and supported extensions.")
        sys.exit(1)

    print(f"Found {len(documents)} chunks. Embedding into collection '{collection}'...")
    create_vector_store(documents, collection_name=collection)
    print(f"Done. {len(documents)} chunks added to '{collection}' collection.")
