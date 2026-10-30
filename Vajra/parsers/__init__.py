# VAJRA — Unified file reading interface.
# extract_text() returns the full plain text of any supported file.
# read_file() wraps it with context-window chunking for prompts.

from pathlib import Path
from parsers.chunker import chunk

# Legacy binary Office formats VAJRA cannot parse — tell the user how to convert.
LEGACY_FORMATS = {
    ".xls": "Legacy .xls is not supported. Re-save it as .xlsx or .csv and try again.",
    ".ppt": "Legacy .ppt is not supported. Re-save it as .pptx and try again.",
    ".doc": "Legacy .doc is not supported. Re-save it as .docx and try again.",
}


def extract_text(path) -> tuple:
    p   = Path(path)
    ext = p.suffix.lower()

    if not p.exists():
        return "", f"[ERROR] File not found: {p}"
    if not p.is_file():
        return "", f"[ERROR] Not a file: {p}"

    if ext in LEGACY_FORMATS:
        return "", f"[ERROR] {LEGACY_FORMATS[ext]}"

    if ext == ".pdf":
        from parsers.pdf import read_pdf
        content, err = read_pdf(p)
    elif ext == ".docx":
        from parsers.docx import read_docx
        content, err = read_docx(p)
    elif ext in (".xlsx", ".xlsm"):
        from parsers.xlsx import read_xlsx
        content, err = read_xlsx(p)
    elif ext == ".pptx":
        from parsers.pptx import read_pptx
        content, err = read_pptx(p)
    elif ext == ".ipynb":
        from parsers.notebook import read_notebook
        content, err = read_notebook(p)
    else:
        from parsers.text import read_text
        content, err = read_text(p)

    if err:
        return "", err
    if not content or not content.strip():
        return "", f"[ERROR] File is empty: {p.name}"
    return content, None


def read_file(path) -> tuple:
    p = Path(path)
    content, err = extract_text(p)
    if err:
        return "", err
    return chunk(content, p.name)


def read_files(paths: list) -> tuple:
    combined, statuses = [], []
    for p in paths:
        content, status = read_file(p)
        statuses.append(status)
        if content:
            combined.append(f"=== FILE: {Path(p).name} ===\n\n{content}")
    return "\n\n".join(combined), statuses
