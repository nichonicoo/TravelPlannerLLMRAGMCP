import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

document_folder = "RAG/documents"

def load_documents():
    docs = []

    for filename in os.listdir(document_folder):
        file_path = os.path.join(document_folder, filename)

        # TXT
        if filename.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                docs.append(Document(page_content=f.read()))

        # PDF
        elif filename.endswith(".pdf"):
            from langchain_community.document_loaders import PyMuPDFLoader
            loader = PyMuPDFLoader(file_path)
            pages = loader.load()
            docs.extend(pages)

    # Filter halaman kosong / hampir kosong
    filtered = []
    for d in docs:
        text = d.page_content.strip()
        if len(text) > 30:  # minimal panjang teks
            filtered.append(d)

    return filtered

def setup_rag():
    docs = load_documents()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
    )

    # split sambil mempertahankan metadata (page, dll)
    chunks = []
    for d in docs:
        pieces = splitter.split_text(d.page_content)
        for p in pieces:
            chunks.append(
                Document(
                    page_content=p,
                    metadata=d.metadata  # penting untuk info halaman
                )
            )

    embedding_model = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5"
    )

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        collection_name="prospektus_ali",
    )

    # retriever lebih ketat → kurangi chunk ngaco
    retriever = vectordb.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 6,
          #  "score_threshold": 0.3,  # tweak kalau perlu
        },
    )

    return retriever