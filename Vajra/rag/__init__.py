# VAJRA — Local RAG: library, chunking, embeddings, retrieval, citations.

from rag.library   import add_document, list_documents, remove_document, clear_library
from rag.retriever import retrieve, build_rag_prompt, format_citations, SOURCE_MODES
