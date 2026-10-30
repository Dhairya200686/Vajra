# VAJRA — High-level library operations: add, list, remove, clear.
# Ingestion embeds all chunks of a document in batches (rag/embedder.embed_many)
# instead of one HTTP call per chunk. Non-PDF formats go through the shared
# parsers.extract_text(), so every format VAJRA can read can also be indexed.

import json
from pathlib  import Path
from datetime import datetime
from core.config import BASE_DIR

MANIFEST_FILE = BASE_DIR / "vajra_library" / "manifest.json"
MANIFEST_FILE.parent.mkdir(exist_ok=True)


def load_manifest() -> dict:
    if MANIFEST_FILE.exists():
        try:
            return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"documents": {}}


def save_manifest(m: dict) -> None:
    tmp = MANIFEST_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(m, indent=2), encoding="utf-8")
    tmp.replace(MANIFEST_FILE)


def add_document(path, progress_cb=None) -> tuple:
    from parsers       import extract_text
    from rag.chunker   import split_text
    from rag.embedder  import embed_many, check_embed_model
    from rag.store     import add_chunks

    p = Path(path)
    if not p.exists():
        return 0, f"[ERROR] File not found: {p}"

    if not check_embed_model():
        return 0, "[ERROR] nomic-embed-text not found. Run: ollama pull nomic-embed-text"

    ext   = p.suffix.lower()
    pages = []

    if ext == ".pdf":
        # Read page-by-page (not via the shared extractor) so each chunk
        # keeps a page number for citations.
        try:
            import pypdf
            reader = pypdf.PdfReader(str(p))
            for i, pg in enumerate(reader.pages, 1):
                txt = pg.extract_text() or ""
                if txt.strip():
                    pages.append((i, txt))
            if not pages:
                return 0, "[ERROR] PDF appears image-based — no text extracted."
        except ImportError:
            return 0, "[ERROR] pypdf not installed. Run: pip install pypdf"
        except Exception as e:
            return 0, f"[ERROR] Could not read PDF: {e}"
    else:
        content, err = extract_text(p)
        if err: return 0, err
        pages = [(None, content)]

    flat = []
    for page_num, page_text in pages:
        for idx, chunk in enumerate(split_text(page_text)):
            flat.append((page_num, idx, chunk))

    if not flat:
        return 0, "[ERROR] No chunks could be produced from this file."

    texts = [c for _, _, c in flat]
    vectors, batch_errors = embed_many(texts, progress_cb=progress_cb)

    ids, embeddings, documents, metadatas = [], [], [], []
    for (page_num, idx, chunk), vec in zip(flat, vectors):
        if vec is None:
            continue
        ids.append(f"{p.name}::p{page_num or 0}::c{idx}")
        embeddings.append(vec)
        documents.append(chunk)
        metadatas.append({
            "source": p.name,
            "page":   page_num or 0,
            "chunk":  idx,
            "added":  datetime.now().isoformat(),
        })

    if not ids:
        return 0, "[ERROR] No chunks could be embedded from this file."

    added, err = add_chunks(ids, embeddings, documents, metadatas)
    if err and added == 0:
        return 0, err

    if batch_errors and not err:
        err = f"[WARNING] {len(batch_errors)} embedding batch(es) had issues — some chunks may be missing."

    manifest = load_manifest()
    manifest["documents"][p.name] = {
        "path":       str(p.resolve()),
        "chunks":     added,
        "pages":      len(pages) if ext == ".pdf" else None,
        "added":      datetime.now().isoformat(),
        "size_bytes": p.stat().st_size,
    }
    save_manifest(manifest)

    return added, err


def list_documents() -> list:
    manifest = load_manifest()
    return [{"name": name, **info} for name, info in manifest["documents"].items()]


def remove_document(name: str) -> tuple:
    from rag.store import delete_by_source
    manifest = load_manifest()
    matched  = None
    for doc_name in manifest["documents"]:
        if name.lower() in doc_name.lower():
            matched = doc_name
            break
    if not matched:
        return 0, f"[ERROR] No document matching '{name}' in library."

    removed, err = delete_by_source(matched)
    if err:
        return 0, err
    del manifest["documents"][matched]
    save_manifest(manifest)
    return removed, None


def clear_library() -> tuple:
    from rag.store import clear_all
    ok, err = clear_all()
    if not ok:
        return False, err
    save_manifest({"documents": {}})
    return True, None
