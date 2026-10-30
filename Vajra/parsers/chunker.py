# VAJRA — Smart chunking for files that exceed the context window.

MAX_WORDS = 5500


def chunk(content: str, filename: str = "") -> tuple:
    words = content.split()
    total = len(words)

    if total <= MAX_WORDS:
        return content, f"Read: {filename} ({total} words — complete)"

    head_words = int(MAX_WORDS * 0.9)
    tail_words = 200
    head       = " ".join(words[:head_words])
    tail       = " ".join(words[-tail_words:])
    omit       = total - head_words - tail_words
    truncated  = (
        f"{head}\n\n"
        f"[... {omit} words omitted — document truncated for context window ...]\n\n"
        f"{tail}"
    )
    status = (
        f"Read: {filename} ({total} words total — "
        f"showing first {head_words} + last {tail_words} words)"
    )
    return truncated, status
