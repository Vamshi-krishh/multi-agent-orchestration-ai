import os
import sys
import chromadb
from src.code_loader import load_codebase
from src.embedder import create_vector_store, DEFAULT_CHROMA_PATH

COMPONENTS_ROOT = r"C:\vamshi\COMPONENTS"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(PROJECT_ROOT, "data")

SKIP_FOLDERS = {".github", ".metadata", ".pytest_cache", ".vscode", "knowledge-base", "mcp-server", "isep-ui"}


def ingest_all(only: list[str] = None):
    client = chromadb.PersistentClient(path=DEFAULT_CHROMA_PATH)

    folders = sorted([
        f for f in os.listdir(COMPONENTS_ROOT)
        if os.path.isdir(os.path.join(COMPONENTS_ROOT, f)) and f not in SKIP_FOLDERS
    ])

    if only:
        folders = [f for f in folders if f in only]
        print(f"Targeting {len(folders)} service(s): {folders}\n")
    else:
        print(f"Found {len(folders)} services to ingest: {folders}\n")

    for folder_name in folders:
        folder_path = os.path.join(COMPONENTS_ROOT, folder_name)
        collection_name = folder_name

        existing = [c.name for c in client.list_collections()]
        if collection_name in existing:
            client.delete_collection(collection_name)
            print(f"[{collection_name}] Cleared existing collection.")

        print(f"[{collection_name}] Scanning {folder_path}...")
        documents = load_codebase(folder_path, service=collection_name)

        if not documents:
            print(f"[{collection_name}] No files found — skipping.\n")
            continue

        print(f"[{collection_name}] {len(documents)} chunks found. Embedding...")
        create_vector_store(documents, collection_name=collection_name)
        print(f"[{collection_name}] Done.\n")

    print("All services ingested.")


def ingest_docs(only_services: list[str] = None):
    """
    Ingest markdown documentation from knowledge-base/components/{service}/
    and ADD to the existing service collection (no deletion — docs supplement code).

    Usage:
        python ingest_all.py --docs           → add docs for all services
        python ingest_all.py --docs kos       → add docs for kos only
    """
    kb_root = os.path.join(COMPONENTS_ROOT, "knowledge-base", "components")
    if not os.path.isdir(kb_root):
        print(f"No knowledge-base folder found at: {kb_root}")
        return

    services = sorted([
        s for s in os.listdir(kb_root)
        if os.path.isdir(os.path.join(kb_root, s))
    ])

    if only_services:
        services = [s for s in services if s in only_services]

    print(f"Ingesting docs for: {services}\n")

    for service_name in services:
        service_path = os.path.join(kb_root, service_name)
        print(f"[{service_name}-docs] Scanning {service_path}...")

        documents = load_codebase(service_path, service=service_name)

        if not documents:
            print(f"[{service_name}-docs] No files found — skipping.\n")
            continue

        print(f"[{service_name}-docs] {len(documents)} chunks found. Adding to '{service_name}' collection...")
        # No deletion — add_documents appends to the existing collection
        create_vector_store(documents, collection_name=service_name)
        print(f"[{service_name}-docs] Done.\n")

    print("Documentation ingested.")


def ingest_features(only_services: list[str] = None):
    """
    Ingest markdown docs from data/{service}/features/ inside this project.
    The service name is derived from the component folder — no extra config needed.

    Structure:
        data/
          kos/features/dlms/dlms-orders.md
          icps/features/auth/auth-flows.md
          bds/features/...

    Usage:
        python ingest_all.py --features           -> add docs for all components
        python ingest_all.py --features kos       -> add docs for kos only
        python ingest_all.py --features kos icps  -> add docs for kos and icps
    """
    if not os.path.isdir(DATA_ROOT):
        print(f"No data folder found at: {DATA_ROOT}")
        return

    components = sorted([
        c for c in os.listdir(DATA_ROOT)
        if os.path.isdir(os.path.join(DATA_ROOT, c, "features"))
    ])

    if only_services:
        components = [c for c in components if c in only_services]

    if not components:
        print("No component folders with a features/ subfolder found.")
        return

    print(f"Ingesting feature docs for: {components}\n")

    for service_name in components:
        features_path = os.path.join(DATA_ROOT, service_name, "features")
        features = sorted([
            f for f in os.listdir(features_path)
            if os.path.isdir(os.path.join(features_path, f))
        ])

        for feature_name in features:
            feature_path = os.path.join(features_path, feature_name)
            print(f"[{service_name}/{feature_name}] Scanning {feature_path}...")
            documents = load_codebase(feature_path, service=service_name)

            if not documents:
                print(f"[{service_name}/{feature_name}] No files found — skipping.\n")
                continue

            print(f"[{service_name}/{feature_name}] {len(documents)} chunks found. Adding to '{service_name}' collection...")
            create_vector_store(documents, collection_name=service_name)
            print(f"[{service_name}/{feature_name}] Done.\n")

    print("Feature docs ingested.")


if __name__ == "__main__":
    # Usage:
    #   python ingest_all.py                       → ingest all services (code)
    #   python ingest_all.py kos icms              → ingest specific services (code)
    #   python ingest_all.py --docs                → add knowledge-base docs for all services
    #   python ingest_all.py --docs kos            → add knowledge-base docs for kos only
    #   python ingest_all.py --features            -> add feature docs for all components
    #   python ingest_all.py --features kos        -> add feature docs for kos only
    #   python ingest_all.py --features kos icps   -> add feature docs for kos and icps
    args = sys.argv[1:]

    if args and args[0] == "--docs":
        only_services = args[1:] if len(args) > 1 else None
        ingest_docs(only_services=only_services)
    elif args and args[0] == "--features":
        only_services = args[1:] if len(args) > 1 else None
        ingest_features(only_services=only_services)
    else:
        only = args if args else None
        ingest_all(only=only)
