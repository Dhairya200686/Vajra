# VAJRA — Microsoft Word (.docx) file parser.

from pathlib import Path


def read_docx(path: Path) -> tuple:
    try:
        import docx
    except ImportError:
        return "", "[ERROR] python-docx not installed. Run: pip install python-docx"
    try:
        doc     = docx.Document(str(path))
        paras   = [p.text for p in doc.paragraphs if p.text.strip()]
        content = "\n\n".join(paras)
        if not content.strip():
            return "", "[ERROR] DOCX file appears to be empty."
        return content, None
    except Exception as e:
        return "", f"[ERROR] Could not read DOCX: {e}"
