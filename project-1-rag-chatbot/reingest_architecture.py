"""
Quick script to re-ingest COMPONENT_ARCHITECTURE.md after updates.
Run this after updating architecture documentation to refresh the chatbot's knowledge.
"""
import os
import chromadb
from pathlib import Path
from src.embedder import create_vector_store, DEFAULT_CHROMA_PATH
from src.code_loader import load_codebase

COMPONENTS_ROOT = Path(r"C:\vamshi\COMPONENTS")
KNOWLEDGE_BASE = COMPONENTS_ROOT / "knowledge-base"

def reingest_architecture():
    """Re-ingest COMPONENT_ARCHITECTURE.md into the 'general' collection."""
    arch_file = KNOWLEDGE_BASE / "COMPONENT_ARCHITECTURE.md"
    
    if not arch_file.exists():
        print(f"❌ File not found: {arch_file}")
        return
    
    print(f"📄 Loading {arch_file.name}...")
    # Use load_codebase on the knowledge-base folder to load all .md files
    documents = load_codebase(str(KNOWLEDGE_BASE), service="general")
    
    if not documents:
        print("❌ No documents loaded")
        return
    
    print(f"✅ Loaded {len(documents)} chunks from knowledge-base/")
    print(f"🔄 Embedding into 'general' collection...")
    
    # Delete existing 'general' collection first to avoid duplicates
    client = chromadb.PersistentClient(path=DEFAULT_CHROMA_PATH)
    existing = [c.name for c in client.list_collections()]
    if "general" in existing:
        client.delete_collection("general")
        print(f"   Cleared existing 'general' collection")
    
    create_vector_store(documents, collection_name="general")
    
    print(f"✅ Successfully re-ingested knowledge-base docs")
    print(f"   Collection: general")
    print(f"   Chunks: {len(documents)}")
    print(f"   Location: {DEFAULT_CHROMA_PATH}")
    print("\n🎉 Chatbot now has the latest architecture diagrams!")

if __name__ == "__main__":
    reingest_architecture()
