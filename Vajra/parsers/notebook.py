# VAJRA — Jupyter notebook (.ipynb) parser. Pulls out markdown and code
# cells in order, plus short text outputs and error summaries. Image and
# HTML outputs (often megabytes of base64) are skipped on purpose.

import json
from pathlib import Path

MAX_OUTPUT_CHARS = 1500


def _join(source) -> str:
    # Notebook "source" fields are either a list of lines or one string.
    if isinstance(source, list):
        return "".join(source)
    return str(source or "")


def _output_text(out: dict) -> str:
    kind = out.get("output_type")
    if kind == "stream":
        return _join(out.get("text", ""))
    if kind in ("execute_result", "display_data"):
        data = out.get("data", {}) or {}
        return _join(data.get("text/plain", ""))
    if kind == "error":
        return f"{out.get('ename', 'Error')}: {out.get('evalue', '')}"
    return ""


def read_notebook(path: Path) -> tuple:
    try:
        nb = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as e:
        return "", f"[ERROR] Could not parse notebook: {e}"

    cells = nb.get("cells")
    if not isinstance(cells, list):
        return "", "[ERROR] Unsupported notebook format (no cells found)."

    blocks = []
    for i, cell in enumerate(cells, 1):
        kind  = cell.get("cell_type", "raw")
        src   = _join(cell.get("source", "")).strip()
        parts = []
        if src:
            parts.append(f"[Cell {i} - {kind}]\n{src}")
        if kind == "code":
            outs = []
            for out in cell.get("outputs", []) or []:
                text = _output_text(out).strip()
                if text:
                    outs.append(text)
            if outs:
                joined = "\n".join(outs)
                if len(joined) > MAX_OUTPUT_CHARS:
                    joined = joined[:MAX_OUTPUT_CHARS] + "\n[... output truncated ...]"
                parts.append(f"[Output]\n{joined}")
        if parts:
            blocks.append("\n".join(parts))

    return "\n\n".join(blocks), None
