# VAJRA — Semantic retrieval, citation formatting, and RAG prompt construction.

SOURCE_MODES = ("source-only", "source-first", "hybrid")


def retrieve(query_text: str, n_results: int = 5) -> tuple:
    from rag.embedder import embed_text
    from rag.store     import query as store_query

    vec, err = embed_text(query_text)
    if err:
        return [], err

    hits, err = store_query(vec, n_results=n_results)
    if err:
        return [], err

    return hits, None


def format_context(hits: list) -> str:
    if not hits:
        return ""
    blocks = []
    for h in hits:
        meta  = h.get("meta", {}) or {}
        src   = meta.get("source", "unknown")
        page  = meta.get("page")
        label = src + (f", page {page}" if page else "")
        blocks.append(f"[SOURCE: {label}]\n{h['text']}")
    return "\n\n".join(blocks)


def format_citations(hits: list) -> str:
    if not hits:
        return ""
    seen, labels = set(), []
    for h in hits:
        meta  = h.get("meta", {}) or {}
        src   = meta.get("source", "unknown")
        page  = meta.get("page")
        label = src + (f" (page {page})" if page else "")
        if label not in seen:
            seen.add(label)
            labels.append(label)
    return " · ".join(labels)


def build_rag_prompt(question: str, hits: list, source_mode: str = "hybrid") -> str:
    context = format_context(hits)

    if source_mode == "source-only":
        instruction = (
            "Answer ONLY using the LIBRARY EVIDENCE below. Do not use general "
            "knowledge. If the evidence does not contain the answer, say clearly: "
            "'My library does not contain information to answer this.'"
        )
    elif source_mode == "source-first":
        instruction = (
            "Prefer the LIBRARY EVIDENCE below. You may supplement with general "
            "knowledge only where the library is silent, and you MUST clearly "
            "label which parts come from the library versus general knowledge."
        )
    else:
        instruction = (
            "Use the LIBRARY EVIDENCE below where relevant, citing it clearly. "
            "You may also use general knowledge to complete the answer."
        )

    if not context:
        return (
            f"{question}\n\n"
            f"(No relevant library evidence was found for this question. "
            f"Answer from general knowledge, and mention that nothing relevant "
            f"was found in the local library.)"
        )

    return (
        f"LIBRARY EVIDENCE:\n{'─'*50}\n{context}\n{'─'*50}\n\n"
        f"INSTRUCTION: {instruction}\n\n"
        f"QUESTION: {question}\n\n"
        f"Always cite the source file (and page, if given) for any fact you "
        f"draw from the library evidence, in the form (source: filename, page X)."
    )
