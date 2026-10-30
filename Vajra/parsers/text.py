# VAJRA — Plain text, code, log, and config file parser.
# Rejects genuinely binary files with a clear error instead of feeding
# replacement-character garbage into the model's context window, and decodes
# UTF-16 / UTF-8-with-BOM correctly (PowerShell redirects often write UTF-16).

from pathlib import Path

SNIFF_BYTES = 8192
BOM_UTF16   = (b"\xff\xfe", b"\xfe\xff")
BOM_UTF8    = b"\xef\xbb\xbf"


def _looks_binary(sample: bytes) -> bool:
    # UTF-16 text legitimately contains NUL bytes — a BOM means it is text.
    if sample.startswith(BOM_UTF16) or sample.startswith(BOM_UTF8):
        return False
    return b"\x00" in sample


def read_text(path: Path) -> tuple:
    try:
        raw = path.read_bytes()
    except Exception as e:
        return "", f"[ERROR] Could not read file: {e}"

    if _looks_binary(raw[:SNIFF_BYTES]):
        return "", (f"[ERROR] {path.name} looks like a binary file, not text. "
                    f"VAJRA reads text, code, configs, PDF, DOCX, XLSX, PPTX, and IPYNB files.")

    if raw.startswith(BOM_UTF16):
        encoding = "utf-16"
    elif raw.startswith(BOM_UTF8):
        encoding = "utf-8-sig"
    else:
        encoding = "utf-8"

    return raw.decode(encoding, errors="replace"), None
