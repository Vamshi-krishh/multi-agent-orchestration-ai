import chromadb
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document


class BM25Retriever:
    """
    Builds a BM25 keyword index over all documents in ChromaDB.
    Used alongside semantic search for hybrid retrieval.
    Initialized lazily and cached — only built once per server startup.
    """

    def __init__(self, chroma_path: str, collection_names: list[str]):
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection_names = collection_names
        self.documents: list[str] = []
        self.doc_metadata: list[dict] = []
        self.bm25 = None
        self._build_index()

    def _build_index(self):
        print(f"[BM25] Building index across {len(self.collection_names)} collections...")
        for name in self.collection_names:
            try:
                col = self.client.get_collection(name)
                data = col.get(include=["documents", "metadatas"])
                for doc_text, meta in zip(data["documents"], data["metadatas"]):
                    self.documents.append(doc_text)
                    self.doc_metadata.append(meta)
            except Exception as e:
                print(f"[BM25] Skipping {name}: {e}")
                continue

        if not self.documents:
            print("[BM25] No documents found — BM25 index empty.")
            return

        tokenized = [doc.lower().split() for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized)
        print(f"[BM25] Index built: {len(self.documents)} documents.")

    def search(self, query: str, k: int = 10) -> list[tuple[Document, float]]:
        if not self.bm25:
            return []

        tokens = query.lower().split()
        scores = self.bm25.get_scores(tokens)

        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                doc = Document(
                    page_content=self.documents[idx],
                    metadata=self.doc_metadata[idx]
                )
                results.append((doc, float(scores[idx])))
        return results
