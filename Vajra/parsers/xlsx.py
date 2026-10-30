# VAJRA — Excel (.xlsx / .xlsm) parser. Renders each sheet as a plain-text
# table. Prefers cached cell values (what Excel last calculated); if a file
# has none (for example, formulas written by a script and never opened in
# Excel) it falls back to showing the formulas themselves. Large sheets are
# capped so they cannot flood the model's context window.

from pathlib import Path

MAX_ROWS_PER_SHEET = 200    # rows shown per sheet
MAX_SCAN_ROWS      = 5000   # rows examined per sheet (guards huge empty ranges)
MAX_COLS           = 30
MAX_CELL_CHARS     = 80


def _fmt(value) -> str:
    if value is None:
        return ""
    text = str(value).replace("\n", " ").replace("\r", " ").strip()
    if len(text) > MAX_CELL_CHARS:
        text = text[:MAX_CELL_CHARS - 3] + "..."
    return text


def _render(path: Path, data_only: bool) -> str:
    import openpyxl
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=data_only)
    blocks = []
    try:
        for ws in wb.worksheets:
            lines, scanned, truncated = [], 0, False
            for row in ws.iter_rows(values_only=True):
                scanned += 1
                if scanned > MAX_SCAN_ROWS:
                    truncated = True
                    break
                cells = [_fmt(c) for c in row[:MAX_COLS]]
                while cells and not cells[-1]:
                    cells.pop()
                if not cells:
                    continue
                if len(lines) >= MAX_ROWS_PER_SHEET:
                    truncated = True
                    break
                lines.append(" | ".join(cells))
            if not lines:
                continue
            state = getattr(ws, "sheet_state", "visible")
            tag   = "" if state == "visible" else f" ({state})"
            head  = f"=== SHEET: {ws.title}{tag} ==="
            if truncated:
                lines.append("[... more rows not shown ...]")
            blocks.append(head + "\n" + "\n".join(lines))
    finally:
        wb.close()
    return "\n\n".join(blocks)


def read_xlsx(path: Path) -> tuple:
    try:
        import openpyxl
    except ImportError:
        return "", "[ERROR] openpyxl not installed. Run: pip install openpyxl"
    try:
        content = _render(path, data_only=True)
        if not content.strip():
            content = _render(path, data_only=False)
        return content, None
    except Exception as e:
        return "", f"[ERROR] Could not read workbook (corrupt or password-protected?): {e}"
