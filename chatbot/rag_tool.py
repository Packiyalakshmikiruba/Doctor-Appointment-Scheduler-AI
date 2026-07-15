"""
chatbot/rag_tool.py
RAG pipeline for hospital FAQ / general info, using:
    - Hugging Face embeddings (sentence-transformers, free & local)
    - FAISS vector store (local, no external DB needed)

This becomes the 5th tool for the LangChain agent, so it can answer
questions like "What are your OPD hours?" or "What's your cancellation
policy?" grounded in real clinic data instead of hallucinating.

Build the index first:
    python manage.py build_knowledge_base
    python manage.py shell -c "from chatbot.rag_tool import build_vectorstore; build_vectorstore()"
"""

import os

from django.conf import settings
from langchain.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter

KNOWLEDGE_TXT = os.path.join(settings.BASE_DIR, "chatbot", "data", "hospital_knowledge.txt")
INDEX_DIR = os.path.join(settings.BASE_DIR, "chatbot", "faiss_index")

# Free, local Hugging Face embedding model — no API key needed.
_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def build_vectorstore():
    """Run this once (and again after build_knowledge_base) to (re)build the FAISS index."""
    with open(KNOWLEDGE_TXT, encoding="utf-8") as f:
        raw_text = f.read()

    splitter = CharacterTextSplitter(separator="\n\n", chunk_size=400, chunk_overlap=40)
    chunks = splitter.split_text(raw_text)

    vectorstore = FAISS.from_texts(chunks, _embeddings)
    vectorstore.save_local(INDEX_DIR)
    print(f"Vector store built with {len(chunks)} chunks -> {INDEX_DIR}")
    return vectorstore


def _load_vectorstore():
    return FAISS.load_local(
        INDEX_DIR, _embeddings, allow_dangerous_deserialization=True
    )


@tool
def hospital_info_search(query: str) -> str:
    """
    Search general hospital information: department details, doctor bios,
    OPD hours, cancellation policy, and other clinic FAQs.
    Use this for informational questions that are NOT about booking a
    specific appointment (use search_doctor / check_doctor_availability for that).
    """
    if not os.path.exists(INDEX_DIR):
        return "Knowledge base not built yet. Run build_vectorstore() first."

    vectorstore = _load_vectorstore()
    results = vectorstore.similarity_search(query, k=3)

    if not results:
        return "No relevant information found."

    return "\n---\n".join(r.page_content for r in results)
