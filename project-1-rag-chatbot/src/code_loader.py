import re
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

LANGUAGE_MAP = {
    ".py":   Language.PYTHON,
    ".js":   Language.JS,
    ".ts":   Language.JS,
    ".java": Language.JAVA,
    ".go":   Language.GO,
}

TEXT_EXTENSIONS = {".xml", ".yaml", ".yml", ".properties", ".md", ".txt", ".json"}

SKIP_DIRS = {"target", "node_modules", ".git", "__pycache__", "venv", ".venv", "build", "dist", ".idea", ".vscode"}


def _extract_java_symbols(content: str) -> dict:
    """Extract class name and public method names from Java source."""
    symbols = {'class_name': None, 'methods': []}

    class_match = re.search(r'public\s+(?:class|interface|enum)\s+(\w+)', content)
    if class_match:
        symbols['class_name'] = class_match.group(1)

    method_pattern = r'(?:public|private|protected)\s+(?:static\s+)?[\w<>\[\],\s]+\s+(\w+)\s*\('
    methods = re.findall(method_pattern, content)
    # Deduplicate, filter out Java keywords that can appear, limit to 15
    skip = {'if', 'for', 'while', 'switch', 'catch', 'new', 'return', 'class'}
    symbols['methods'] = list({m for m in methods if m not in skip})[:15]

    return symbols


def load_codebase(root_folder: str, service: str = "") -> list[Document]:
    root = Path(root_folder)
    documents = []

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if any(skip in file_path.parts for skip in SKIP_DIRS):
            continue

        suffix = file_path.suffix.lower()
        if suffix not in LANGUAGE_MAP and suffix not in TEXT_EXTENSIONS:
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if not content.strip():
                continue

            relative_path = str(file_path.relative_to(root))
            language_name = _get_language_name(suffix)
            file_name = file_path.name

            if suffix in LANGUAGE_MAP:
                chunks = _split_code(content, suffix, relative_path, language_name, file_name, service)
            else:
                chunks = _split_text(content, relative_path, language_name, file_name, service)

            documents.extend(chunks)
        except Exception as e:
            print(f"Skipping {file_path}: {e}")

    return documents


def _split_code(content: str, suffix: str, relative_path: str, language_name: str, file_name: str, service: str) -> list[Document]:
    lang = LANGUAGE_MAP[suffix]

    class_name = None
    methods_str = ''
    if suffix == '.java':
        symbols = _extract_java_symbols(content)
        class_name = symbols['class_name']
        methods_str = ','.join(symbols['methods'])

    splitter = RecursiveCharacterTextSplitter.from_language(
        language=lang,
        chunk_size=4000,
        chunk_overlap=200
    )
    chunks = splitter.create_documents(
        texts=[content],
        metadatas=[{
            "source":      relative_path,
            "source_type": "code",
            "language":    language_name,
            "file_name":   file_name,
            "service":     service,
            "class_name":  class_name or '',
            "methods":     methods_str,
            "page":        0
        }]
    )
    return chunks


def _split_text(content: str, relative_path: str, language_name: str, file_name: str, service: str) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
    chunks = splitter.create_documents(
        texts=[content],
        metadatas=[{
            "source":      relative_path,
            "source_type": "config",
            "language":    language_name,
            "file_name":   file_name,
            "service":     service,
            "class_name":  '',
            "methods":     '',
            "page":        0
        }]
    )
    return chunks


def _get_language_name(suffix: str) -> str:
    names = {
        ".py": "Python", ".java": "Java", ".js": "JavaScript",
        ".ts": "TypeScript", ".go": "Go", ".xml": "XML",
        ".yaml": "YAML", ".yml": "YAML", ".properties": "Properties",
        ".md": "Markdown", ".json": "JSON", ".txt": "Text"
    }
    return names.get(suffix, "Unknown")
