# VAJRA — Talks to Ollama's embedding endpoint. Same raw-HTTP pattern as llm/client.py.
# Uses the batch /api/embed endpoint for fast ingestion, with a legacy fallback
# for older Ollama versions that only support /api/embeddings (one text at a time).

import requests

OLLAMA_EMBED_URL        = "http://localhost:11434/api/embed"
OLLAMA_EMBED_LEGACY_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL              = "nomic-embed-text"
TIMEOUT                  = 60
BATCH_SIZE               = 32


# Embeds multiple texts in ONE request via Ollama's batch endpoint.
# Returns (vectors, error) — vectors is a list the same length as texts,
# with None in place of any text that failed to embed.
def embed_batch(texts: list, model: str = None) -> tuple:
    model = model or EMBED_MODEL
    if not texts:
        return [], None
    try:
        r = requests.post(
            OLLAMA_EMBED_URL,
            json={"model": model, "input": texts},
            timeout=TIMEOUT)
        if r.status_code == 404:
            return _embed_batch_legacy(texts, model)
        if r.status_code != 200:
            return [None] * len(texts), f"[ERROR] Ollama embedding HTTP {r.status_code}"
        vecs = r.json().get("embeddings")
        if not vecs or len(vecs) != len(texts):
            return [None] * len(texts), "[ERROR] Unexpected embedding response shape."
        return vecs, None
    except requests.exceptions.ConnectionError:
        return [None] * len(texts), "[ERROR] Cannot connect to Ollama. Run: ollama serve"
    except requests.exceptions.Timeout:
        return [None] * len(texts), "[ERROR] Embedding request timed out."
    except Exception as e:
        return [None] * len(texts), f"[ERROR] Embedding failed: {e}"


# Fallback for older Ollama versions without /api/embed — one call per text.
def _embed_batch_legacy(texts: list, model: str) -> tuple:
    vecs = []
    for t in texts:
        try:
            r = requests.post(
                OLLAMA_EMBED_LEGACY_URL,
                json={"model": model, "prompt": t}, timeout=TIMEOUT)
            vecs.append(r.json().get("embedding") if r.status_code == 200 else None)
        except Exception:
            vecs.append(None)
    return vecs, None


# Embeds a large list of texts, sending them in batches for speed.
def embed_many(texts: list, model: str = None, batch_size: int = BATCH_SIZE,
              progress_cb=None) -> tuple:
    all_vecs, errors = [], []
    done, total = 0, len(texts)
    for i in range(0, total, batch_size):
        chunk = texts[i:i + batch_size]
        vecs, err = embed_batch(chunk, model)
        if err:
            errors.append(err)
        all_vecs.extend(vecs)
        done += len(chunk)
        if progress_cb:
            progress_cb(done, total)
    return all_vecs, errors


# Embeds a single piece of text — used for embedding a query at ask-time.
def embed_text(text: str, model: str = None) -> tuple:
    vecs, err = embed_batch([text], model)
    if err:
        return None, err
    return vecs[0], None


def check_embed_model(model: str = None) -> bool:
    model = model or EMBED_MODEL
    try:
        from llm.models import check_ollama
        up, models = check_ollama()
        if not up:
            return False
        return any(model in m for m in models)
    except Exception:
        return False
