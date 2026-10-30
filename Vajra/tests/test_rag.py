# VAJRA — RAG system unit tests. Pure-logic only — no live Ollama/chromadb required.

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.chunker import split_text


def test_short_text_single_chunk():
    text = "This is a short piece of text."
    chunks = split_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_long_text_multiple_chunks():
    text = "This is a sentence that repeats. " * 200
    chunks = split_text(text)
    assert len(chunks) > 1


def test_empty_text_returns_empty():
    assert split_text("") == []
    assert split_text("   ") == []


def test_paragraph_splitting_preserves_content():
    text = "Paragraph one.\n\n" + ("Word " * 500) + "\n\nParagraph three."
    chunks = split_text(text)
    combined = " ".join(chunks)
    assert "Paragraph one." in combined
    assert "Paragraph three." in combined


def test_retriever_prompt_no_hits():
    from rag.retriever import build_rag_prompt
    prompt = build_rag_prompt("what is X", [], "hybrid")
    assert "No relevant library evidence" in prompt


def test_retriever_prompt_with_hits():
    from rag.retriever import build_rag_prompt
    hits = [{"text": "sample content",
            "meta": {"source": "test.pdf", "page": 3}, "distance": 0.1}]
    prompt = build_rag_prompt("what is X", hits, "source-only")
    assert "test.pdf" in prompt
    assert "page 3" in prompt


def test_format_citations_dedupes():
    from rag.retriever import format_citations
    hits = [
        {"text": "a", "meta": {"source": "doc1.pdf", "page": 1}},
        {"text": "b", "meta": {"source": "doc1.pdf", "page": 1}},
        {"text": "c", "meta": {"source": "doc2.md",  "page": None}},
    ]
    result = format_citations(hits)
    assert "doc1.pdf" in result
    assert "doc2.md" in result
    assert result.count("doc1.pdf") == 1
