# VAJRA — Recursive chunking: paragraph -> sentence -> hard cut, with overlap.

import re

CHUNK_CHARS   = 1800
OVERLAP_CHARS = 250


def split_text(text: str, chunk_chars: int = CHUNK_CHARS,
               overlap_chars: int = OVERLAP_CHARS) -> list:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= chunk_chars:
        return [text]

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    chunks, current = [], ""

    for para in paragraphs:
        if len(para) > chunk_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_long_paragraph(para, chunk_chars))
            continue

        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= chunk_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = para

    if current:
        chunks.append(current)

    return _add_overlap(chunks, overlap_chars)


def _split_long_paragraph(para: str, chunk_chars: int) -> list:
    sentences = re.split(r"(?<=[.!?])\s+", para)
    chunks, current = [], ""
    for sent in sentences:
        if len(sent) > chunk_chars:
            if current:
                chunks.append(current)
                current = ""
            for i in range(0, len(sent), chunk_chars):
                chunks.append(sent[i:i + chunk_chars])
            continue
        candidate = f"{current} {sent}" if current else sent
        if len(candidate) <= chunk_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = sent
    if current:
        chunks.append(current)
    return chunks


def _add_overlap(chunks: list, overlap_chars: int) -> list:
    if len(chunks) <= 1 or overlap_chars <= 0:
        return chunks
    result = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tail = chunks[i - 1][-overlap_chars:]
        result.append(f"{prev_tail}\n\n{chunks[i]}")
    return result
