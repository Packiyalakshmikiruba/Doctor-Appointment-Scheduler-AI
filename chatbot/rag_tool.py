import os

from django.conf import settings
from langchain.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter

KNOWLEDGE_TXT = os.path.join(
    settings.BASE_DIR,
    "chatbot",
    "data",
    "hospital_knowledge.txt"
)

INDEX_DIR = os.path.join(
    settings.BASE_DIR,
    "chatbot",
    "faiss_index"
)

_embeddings = None
_vectorstore = None


def get_embeddings():
    # Lazy-loaded: the embedding model only loads on first actual use,
    # not at import time -- keeps Django startup fast and avoids loading
    # it in processes that never touch the chatbot (e.g. migrations).
    global _embeddings

    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

    return _embeddings


def build_vectorstore():
    """Run this once (and again after build_knowledge_base) to (re)build the FAISS index."""

    with open(
        KNOWLEDGE_TXT,
        encoding="utf-8"
    ) as f:
        raw_text = f.read()

    splitter = CharacterTextSplitter(
        separator="\n\n",
        chunk_size=400,
        chunk_overlap=40
    )

    chunks = splitter.split_text(raw_text)

    vectorstore = FAISS.from_texts(
        chunks,
        get_embeddings()
    )

    vectorstore.save_local(INDEX_DIR)

    print(f"Vector store built with {len(chunks)} chunks -> {INDEX_DIR}")

    return vectorstore


def _load_vectorstore():
    global _vectorstore

    if _vectorstore is None:
        _vectorstore = FAISS.load_local(
            INDEX_DIR,
            get_embeddings(),
            allow_dangerous_deserialization=True
        )

    return _vectorstore


@tool
def hospital_info_search(query: str) -> str:
    """
    Search general hospital information: department details, doctor bios,
    OPD hours, cancellation policy, and other clinic FAQs.
    Use this for informational questions that are NOT about booking a
    specific appointment (use search_doctor / check_doctor_availability for that).

    Args:
        query: User question about hospital information.

    Returns:
        The most relevant hospital information.
    """

    if not os.path.exists(INDEX_DIR):
        return "Knowledge base not built yet. Run build_vectorstore() first."

    vectorstore = _load_vectorstore()

    results = vectorstore.similarity_search(query, k=1)

    if not results:
        return "No relevant information found."

    return "\n---\n".join(r.page_content for r in results)