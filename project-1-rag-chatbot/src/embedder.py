import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

DEFAULT_COLLECTION = "general"

# Always resolve chroma_db relative to the project root (parent of src/),
# regardless of what the current working directory is when scripts are invoked.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CHROMA_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(_PROJECT_ROOT, "chroma_db"))

_embeddings_instance = None


def _get_embeddings():
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings_instance


BATCH_SIZE = 5000


def create_vector_store(chunks, collection_name: str = DEFAULT_COLLECTION):
    print(f"Loading embedding model...")
    embeddings = _get_embeddings()
    print(f"Adding {len(chunks)} chunks to collection '{collection_name}'...")
    vector_store = Chroma(
        collection_name=collection_name,
        persist_directory=DEFAULT_CHROMA_PATH,
        embedding_function=embeddings
    )
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        vector_store.add_documents(batch)
        print(f"  Batch {i // BATCH_SIZE + 1}: {len(batch)} chunks added")
    print(f"Total chunks in '{collection_name}': {vector_store._collection.count()}")
    return vector_store


def load_vector_store(collection_name: str = DEFAULT_COLLECTION):
    embeddings = _get_embeddings()
    return Chroma(
        collection_name=collection_name,
        persist_directory=DEFAULT_CHROMA_PATH,
        embedding_function=embeddings
    )


def list_collections() -> list[str]:
    import chromadb
    client = chromadb.PersistentClient(path=DEFAULT_CHROMA_PATH)
    return [col.name for col in client.list_collections()]
