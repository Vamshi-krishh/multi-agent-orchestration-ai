from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_and_split_pdf(pdf_path):
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.split_documents(documents)
    
    print(f"Total pages loaded: {len(documents)}")
    print(f"Total chunks created: {len(chunks)}")
    print(f"\nSample chunk:\n{chunks[0].page_content[:300]}")
    
    return chunks
