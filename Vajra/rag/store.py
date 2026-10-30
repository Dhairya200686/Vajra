# VAJRA — ChromaDB wrapper. Persistent, local, no server or Docker required.

from core.config import BASE_DIR

LIBRARY_DIR = BASE_DIR / "vajra_library"
CHROMA_DIR  = LIBRARY_DIR / "chroma_db"
LIBRARY_DIR.mkdir(exist_ok=True)

_client     = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection, None
    try:
        import chromadb
    except ImportError:
        return None, "[ERROR] chromadb not installed. Run: pip install chromadb"
    try:
        _client     = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_or_create_collection(
            name="vajra_library", metadata={"hnsw:space": "cosine"})
        return _collection, None
    except Exception as e:
        return None, f"[ERROR] Could not open library store: {e}"


def add_chunks(ids: list, embeddings: list, documents: list, metadatas: list) -> tuple:
    coll, err = _get_collection()
    if err:
        return 0, err
    try:
        before = coll.count()
        coll.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
        after  = coll.count()
        added  = after - before
        if added != len(ids):
            return added, (f"[WARNING] Expected to add {len(ids)} chunks, "
                          f"store increased by {added}. Verify with library list.")
        return added, None
    except Exception as e:
        return 0, f"[ERROR] Could not store chunks: {e}"


def query(embedding: list, n_results: int = 5) -> tuple:
    coll, err = _get_collection()
    if err:
        return [], err
    try:
        result = coll.query(query_embeddings=[embedding], n_results=n_results)
        hits  = []
        docs  = result.get("documents",  [[]])[0]
        metas = result.get("metadatas",  [[]])[0]
        dists = result.get("distances",  [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            hits.append({"text": doc, "meta": meta, "distance": dist})
        return hits, None
    except Exception as e:
        return [], f"[ERROR] Could not query library: {e}"


def delete_by_source(source: str) -> tuple:
    coll, err = _get_collection()
    if err:
        return 0, err
    try:
        before = coll.count()
        coll.delete(where={"source": source})
        after = coll.count()
        return before - after, None
    except Exception as e:
        return 0, f"[ERROR] Could not remove document: {e}"


def clear_all() -> tuple:
    global _collection
    coll, err = _get_collection()
    if err:
        return False, err
    try:
        _client.delete_collection("vajra_library")
        _collection = None
        _get_collection()
        return True, None
    except Exception as e:
        return False, f"[ERROR] Could not clear library: {e}"


def total_chunks() -> int:
    coll, err = _get_collection()
    if err:
        return 0
    try:
        return coll.count()
    except Exception:
        return 0
