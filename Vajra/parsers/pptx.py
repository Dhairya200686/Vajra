# VAJRA — PowerPoint (.pptx) parser. Extracts text slide by slide: titles,
# text boxes, tables, grouped shapes, and speaker notes.

from pathlib import Path


def _collect(shape, out: list) -> None:
    try:
        if getattr(shape, "has_text_frame", False) and shape.has_text_frame:
            text = shape.text_frame.text.strip()
            if text:
                out.append(text)
        if getattr(shape, "has_table", False) and shape.has_table:
            for row in shape.table.rows:
                cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                if any(cells):
                    out.append(" | ".join(cells))
        inner = getattr(shape, "shapes", None)
        if inner is not None:
            for sub in inner:
                _collect(sub, out)
    except Exception:
        pass


def read_pptx(path: Path) -> tuple:
    try:
        from pptx import Presentation
    except ImportError:
        return "", "[ERROR] python-pptx not installed. Run: pip install python-pptx"
    try:
        prs = Presentation(str(path))
    except Exception as e:
        return "", f"[ERROR] Could not open presentation (corrupt or password-protected?): {e}"

    blocks = []
    for i, slide in enumerate(prs.slides, 1):
        parts = []
        for shape in slide.shapes:
            _collect(shape, parts)

        notes = ""
        try:
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None:
                notes = slide.notes_slide.notes_text_frame.text.strip()
        except Exception:
            notes = ""

        if not parts and not notes:
            continue
        block = [f"=== SLIDE {i} ==="] + parts
        if notes:
            block.append(f"[Speaker notes] {notes}")
        blocks.append("\n".join(block))

    return "\n\n".join(blocks), None
