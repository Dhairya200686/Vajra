# VAJRA — PDF file parser.

from pathlib import Path


def read_pdf(path: Path) -> tuple:
    try:
        import pypdf
    except ImportError:
        return "", "[ERROR] pypdf not installed. Run: pip install pypdf"
    try:
        reader  = pypdf.PdfReader(str(path))
        pages   = [p.extract_text() for p in reader.pages if p.extract_text()]
        content = "\n\n".join(pages)
        if not content.strip():
            return "", "[ERROR] PDF appears image-based — no text could be extracted."
        return content, None
    except Exception as e:
        return "", f"[ERROR] Could not read PDF: {e}"
