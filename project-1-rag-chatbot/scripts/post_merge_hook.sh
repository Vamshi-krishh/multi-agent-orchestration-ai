#!/bin/bash
# Git post-merge hook — auto re-ingests this service into ChromaDB after every git pull.
# Installed by: python scripts/install_hooks.py

SERVICE=$(basename "$(pwd)")
PYTHON="/c/vamshi/AI_Projects/project-1-rag-chatbot/venv/Scripts/python.exe"
INGEST="/c/vamshi/AI_Projects/project-1-rag-chatbot/ingest_all.py"

echo ""
echo "[RAG] Code updated in '$SERVICE' — re-ingesting into ChromaDB..."
"$PYTHON" "$INGEST" "$SERVICE"
echo "[RAG] Done."
