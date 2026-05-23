import re
import os
from src.embedder import load_vector_store, list_collections, DEFAULT_CHROMA_PATH

KNOWN_SERVICES = {'icps', 'kos', 'icms', 'iads', 'ilps', 'igw', 'iam'}

_FLOW_KEYWORDS = {
    "flow", "explain", "step by step", "how does", "what happens",
    "walkthrough", "trace", "process", "creation flow", "end to end",
    "what is", "why", "what are", "relationship between", "difference between",
    "compare", "integration", "purpose", "types and their"
}

# Keywords that signal the user wants a broad architectural overview of a service.
# For these queries we pin extra COMPONENT_ARCHITECTURE.md chunks so the high-level
# design context is never crowded out by specific code/doc matches.
_ARCH_KEYWORDS = {
    "describe", "overview", "detail", "in detail", "responsibilities",
    "architecture", "what does", "tell me about", "explain the", "summarize",
    "main responsibilities", "key classes", "important methods"
}

_bm25_instance = None


def _should_boost_docs(question: str) -> bool:
    """Check if question is conceptual/explanatory and should boost documentation over code."""
    lower = question.lower()
    return any(kw in lower for kw in _FLOW_KEYWORDS)


def _is_arch_overview_query(question: str) -> bool:
    """True when user wants a broad architectural description of a service."""
    lower = question.lower()
    return any(kw in lower for kw in _ARCH_KEYWORDS)


def _pin_architecture_chunks(service_scope: str, collections: list[str], limit: int = 3) -> list:
    """
    Retrieves chunks from COMPONENT_ARCHITECTURE.md in the 'general' collection
    that contain the given service name. Called for arch-overview queries so the
    high-level design is guaranteed to appear alongside service-specific docs.
    """
    import chromadb
    from langchain_core.documents import Document

    if "general" not in collections:
        return []

    results = []
    client = chromadb.PersistentClient(path=DEFAULT_CHROMA_PATH)
    existing = [c.name for c in client.list_collections()]
    if "general" not in existing:
        return []

    try:
        col = client.get_collection("general")
        # Fetch all COMPONENT_ARCHITECTURE.md chunks, then filter by service name
        raw = col.get(
            where={"file_name": {"$eq": "COMPONENT_ARCHITECTURE.md"}},
            include=["documents", "metadatas"],
        )
        svc_upper = service_scope.upper()
        svc_lower = service_scope.lower()
        for doc_text, meta in zip(raw.get("documents", []), raw.get("metadatas", [])):
            if svc_upper in doc_text or svc_lower in doc_text:
                results.append(Document(page_content=doc_text, metadata=meta))
                if len(results) >= limit:
                    break
    except Exception as e:
        print(f"[Retriever] Error pinning arch chunks: {e}")

    return results


def _pin_flow_diagrams(question: str, collections: list[str], limit: int = 4) -> list:
    """
    Pins COMPONENT_ARCHITECTURE.md chunks containing Mermaid flow diagrams
    when user asks about flows (certificate order, DLMS, Matter, Auth, etc.).
    This ensures visual Mermaid diagrams are returned instead of text descriptions.
    """
    import chromadb
    from langchain_core.documents import Document

    if "general" not in collections:
        return []

    results = []
    client = chromadb.PersistentClient(path=DEFAULT_CHROMA_PATH)
    existing = [c.name for c in client.list_collections()]
    if "general" not in existing:
        return []

    try:
        col = client.get_collection("general")
        # Fetch COMPONENT_ARCHITECTURE.md chunks
        raw = col.get(
            where={"file_name": {"$eq": "COMPONENT_ARCHITECTURE.md"}},
            include=["documents", "metadatas"],
        )
        
        # Detect flow type from question
        lower_q = question.lower()
        flow_keywords = [
            "certificate order", "dlms", "mica", "dac", "matter", "reel",
            "manufacturing", "auth", "authentication", "authorization",
            "provisioning", "flow", "sequence", "diagram"
        ]
        
        for doc_text, meta in zip(raw.get("documents", []), raw.get("metadatas", [])):
            # Prioritize chunks with Mermaid sequenceDiagram syntax
            has_mermaid = "```mermaid" in doc_text and "sequenceDiagram" in doc_text
            # Also prioritize chunks with flow descriptions
            has_flow_keyword = any(kw in doc_text.lower() for kw in flow_keywords)
            
            if has_mermaid or has_flow_keyword:
                results.append(Document(page_content=doc_text, metadata=meta))
                if len(results) >= limit:
                    break
    except Exception as e:
        print(f"[Retriever] Error pinning flow diagrams: {e}")

    return results


def _get_bm25():
    global _bm25_instance
    if _bm25_instance is None:
        from src.bm25_retriever import BM25Retriever
        chroma_path = DEFAULT_CHROMA_PATH
        _bm25_instance = BM25Retriever(chroma_path, list_collections())
    return _bm25_instance


def parse_service_scope(question: str) -> str | None:
    lower = question.lower()
    found = set()
    for svc in KNOWN_SERVICES:
        if re.search(rf'\bin\s+{svc}\b', lower):
            found.add(svc)
        elif re.search(rf'\b{svc}\s+service\b', lower):
            found.add(svc)
        elif re.search(rf'\b{svc.upper()}\b', question):
            found.add(svc)
    return found.pop() if len(found) == 1 else None


def _extract_class_names(question: str) -> list[str]:
    matches = re.findall(r'\b([A-Z][a-z]+(?:[A-Z][a-zA-Z0-9]*)+(?:\.java)?)\b', question)
    seen = set()
    result = []
    for m in matches:
        name = m if m.endswith('.java') else m + '.java'
        if name not in seen:
            seen.add(name)
            result.append(name)
    return result


def _extract_method_names(question: str) -> list[str]:
    matches = re.findall(r'\b([a-z][a-z]+(?:[A-Z][a-zA-Z0-9]+)+)\b', question)
    seen = set()
    result = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            result.append(m)
    return result


def _extract_file_mentions(question: str) -> list[str]:
    """Detect explicit filename mentions like kos.yml, swagger.yaml, application.properties."""
    matches = re.findall(
        r'\b([\w\-]+\.(?:yml|yaml|xml|properties|json|txt|md))\b',
        question,
        re.IGNORECASE
    )
    seen = set()
    result = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            result.append(m)
    return result


def _doc_key(doc) -> str:
    # Stable unique key: source path + first 50 chars of content
    # More reliable than content[:100] which can collide across services
    source = doc.metadata.get('source', '')
    return f"{source}|{doc.page_content[:50]}"


def _search_by_filename(filename: str, collections: list[str]) -> list:
    import chromadb
    from langchain_core.documents import Document
    results = []
    chroma_path = DEFAULT_CHROMA_PATH
    client = chromadb.PersistentClient(path=chroma_path)
    existing = [c.name for c in client.list_collections()]
    for name in collections:
        if name not in existing:
            continue
        try:
            col = client.get_collection(name)
            raw = col.get(where={"file_name": {"$eq": filename}}, include=["documents", "metadatas"])
            for doc_text, meta in zip(raw["documents"], raw["metadatas"]):
                results.append(Document(page_content=doc_text, metadata=meta))
        except Exception:
            pass
    return results


def _search_by_keyword(term: str, collections: list[str]) -> list:
    import chromadb
    from langchain_core.documents import Document
    results = []
    chroma_path = DEFAULT_CHROMA_PATH
    client = chromadb.PersistentClient(path=chroma_path)
    existing = [c.name for c in client.list_collections()]
    for name in collections:
        if name not in existing:
            continue
        try:
            col = client.get_collection(name)
            raw = col.get(
                where_document={"$contains": term},
                include=["documents", "metadatas"],
                limit=2
            )
            for doc_text, meta in zip(raw.get("documents", []), raw.get("metadatas", [])):
                results.append(Document(page_content=doc_text, metadata=meta))
        except Exception:
            pass
    return results


def _hybrid_search(question: str, collections: list[str], k: int, service_scope: str = None) -> list:
    """
    Combines BM25 keyword search + semantic vector search via Reciprocal Rank Fusion.
    When service_scope is provided, boosts documents from that service by 50%.
    For conceptual/explanatory questions (what/why/how/explain/flow), boosts markdown
    docs by 2x so business context surfaces alongside code instead of being buried.
    """
    RRF_K = 60
    boost_docs = _should_boost_docs(question)

    bm25_results = _get_bm25().search(question, k=k * 2)

    semantic_results = []
    for name in collections:
        try:
            vector_store = load_vector_store(name)
            hits = vector_store.similarity_search_with_score(question, k=4)
            semantic_results.extend(hits)
        except Exception as e:
            print(f"[Retriever] Error searching '{name}': {e}")
    semantic_results.sort(key=lambda x: x[1])

    scores: dict[str, dict] = {}

    for rank, (doc, _) in enumerate(bm25_results):
        key = _doc_key(doc)
        entry = scores.setdefault(key, {'doc': doc, 'score': 0.0})
        entry['score'] += 1.0 / (RRF_K + rank + 1)

    for rank, (doc, _) in enumerate(semantic_results):
        key = _doc_key(doc)
        entry = scores.setdefault(key, {'doc': doc, 'score': 0.0})
        entry['score'] += 1.0 / (RRF_K + rank + 1)

    for entry in scores.values():
        doc = entry['doc']
        # Boost service-scoped results
        if service_scope and doc.metadata.get('service', '').lower() == service_scope:
            entry['score'] *= 1.5
        # Boost markdown docs for conceptual/explanatory questions so business context
        # isn't drowned out by the high frequency of Java code matches
        if boost_docs and doc.metadata.get('language', '') == 'Markdown':
            entry['score'] *= 2.0

    ranked = sorted(scores.values(), key=lambda x: x['score'], reverse=True)
    return [entry['doc'] for entry in ranked[:k]]


def _search_collection(question: str, collection_name: str, k: int):
    vector_store = load_vector_store(collection_name)
    return vector_store.similarity_search(question, k=k)


def get_relevant_chunks(question: str, k: int = 5, collection_name: str = None):
    if collection_name:
        return _search_collection(question, collection_name, k)
    return _search_all_collections(question, k)


def _search_all_collections(question: str, k: int):
    collections = list_collections()
    if not collections:
        return []

    service_scope = parse_service_scope(question)
    arch_query = _is_arch_overview_query(question)
    flow_query = _should_boost_docs(question)  # Detects flow/explain/walkthrough keywords

    # Bump k so there's room for both arch chunks and service-specific docs
    if arch_query and service_scope:
        k = max(k, 10)
    # Also bump k for flow queries to ensure Mermaid diagrams surface
    if flow_query:
        k = max(k, 8)

    pinned = []
    seen_pinned = set()

    def _add_pinned(docs, limit=2):
        for doc in docs[:limit]:
            key = _doc_key(doc)
            if key not in seen_pinned:
                seen_pinned.add(key)
                pinned.append(doc)

    # For flow queries, pin COMPONENT_ARCHITECTURE.md chunks with Mermaid diagrams FIRST
    # This ensures visual diagrams are returned instead of text-only descriptions
    if flow_query:
        flow_docs = _pin_flow_diagrams(question, collections, limit=4)
        _add_pinned(flow_docs, limit=4)
        print(f"[Retriever] Pinned {len(flow_docs)} flow diagram chunks for flow query")

    # For arch-overview queries, pin COMPONENT_ARCHITECTURE.md chunks first
    # so they can't be displaced by higher-scoring service-specific matches
    if arch_query and service_scope:
        arch_docs = _pin_architecture_chunks(service_scope, collections, limit=3)
        _add_pinned(arch_docs, limit=3)
        print(f"[Retriever] Pinned {len(arch_docs)} arch chunks for '{service_scope}' overview query")

    for class_name in _extract_class_names(question):
        _add_pinned(_search_by_filename(class_name, collections))

    for file_name in _extract_file_mentions(question):
        _add_pinned(_search_by_filename(file_name, collections))

    for method_name in _extract_method_names(question):
        _add_pinned(_search_by_keyword(method_name, collections))

    pinned = pinned[:8]

    hybrid = _hybrid_search(question, collections, k, service_scope=service_scope)

    seen = set(seen_pinned)
    unique = list(pinned)
    for doc in hybrid:
        key = _doc_key(doc)
        if key not in seen:
            seen.add(key)
            unique.append(doc)

    results = unique[:k + len(pinned)]

    # Filter out weak single-match services when one service clearly dominates.
    # Always keeps iotcommon (shared library used across all services).
    # Always keeps 'general' collection (cross-service architecture/flow docs).
    # Skip filtering entirely for flow/diagram queries so Mermaid chunks survive.
    if flow_query:
        return results[:k]

    service_counts = {}
    for doc in results:
        svc = doc.metadata.get("service", "")
        service_counts[svc] = service_counts.get(svc, 0) + 1

    if service_counts:
        top_svc = max(service_counts, key=service_counts.get)
        top_count = service_counts[top_svc]
        others = [v for s, v in service_counts.items() if s != top_svc]
        # Only filter when dominant service has 3+ results AND 2x more than any other
        if top_count >= 3 and (not others or top_count >= 2 * max(others)):
            filtered = [
                doc for doc in results
                if doc.metadata.get("service", "") == top_svc
                or doc.metadata.get("service", "") in ("iotcommon", "general")
                or service_counts.get(doc.metadata.get("service", ""), 0) >= 2
            ]
            if filtered:
                print(f"[Retriever] Filtered to {len(filtered)} results (dominant: {top_svc})")
                return filtered[:k]

    return results[:k]
