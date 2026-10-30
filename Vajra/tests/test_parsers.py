# VAJRA — Parser module unit tests.

import json
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from parsers import read_file
from parsers.chunker import chunk, MAX_WORDS


def test_read_nonexistent_file():
    content, status = read_file(Path("does_not_exist.txt"))
    assert content == ""
    assert "[ERROR]" in status


def test_read_empty_file():
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w",
                                     delete=False, encoding="utf-8") as f:
        f.write("   ")
        name = f.name
    content, status = read_file(Path(name))
    assert content == ""
    assert "[ERROR]" in status


def test_read_text_file():
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w",
                                     delete=False, encoding="utf-8") as f:
        f.write("Hello VAJRA test content here.")
        name = f.name
    content, status = read_file(Path(name))
    assert "Hello VAJRA" in content
    assert "[ERROR]" not in status


def test_binary_file_is_rejected(tmp_path):
    p = tmp_path / "blob.bin"
    p.write_bytes(b"MZ\x00\x01\x02\x00\xff" * 50)
    content, status = read_file(p)
    assert content == ""
    assert "binary" in status.lower()


def test_utf16_file_with_bom_reads_correctly(tmp_path):
    p = tmp_path / "ps_output.txt"
    p.write_bytes("Hello VAJRA from PowerShell".encode("utf-16"))
    content, status = read_file(p)
    assert "Hello VAJRA from PowerShell" in content


def test_legacy_office_formats_give_a_clear_message(tmp_path):
    for name in ("old.xls", "old.ppt", "old.doc"):
        p = tmp_path / name
        p.write_bytes(b"not a real office file")
        content, status = read_file(p)
        assert content == ""
        assert "not supported" in status


def test_read_notebook(tmp_path):
    nb = {"cells": [
        {"cell_type": "markdown", "source": ["# Recon notes\n", "Target is internal."]},
        {"cell_type": "code", "source": ["print('scan done')"],
         "outputs": [
             {"output_type": "stream", "name": "stdout", "text": ["scan done\n"]},
             {"output_type": "display_data",
              "data": {"image/png": "iVBORw0KGgoAAAANSUhEUg",
                       "text/plain": ["<Figure size 640x480>"]}},
         ]},
    ]}
    p = tmp_path / "notes.ipynb"
    p.write_text(json.dumps(nb), encoding="utf-8")
    content, status = read_file(p)
    assert "Recon notes" in content
    assert "print('scan done')" in content
    assert "<Figure size 640x480>" in content
    assert "iVBORw0KGgo" not in content


def test_read_xlsx(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Scan"
    ws.append(["host", "port"])
    ws.append(["10.0.0.5", 443])
    p = tmp_path / "scan.xlsx"
    wb.save(str(p))
    content, status = read_file(p)
    assert "SHEET: Scan" in content
    assert "10.0.0.5 | 443" in content


def test_read_pptx(tmp_path):
    pytest.importorskip("pptx")
    from pptx import Presentation
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Quarterly Findings"
    slide.placeholders[1].text = "Three critical issues"
    p = tmp_path / "deck.pptx"
    prs.save(str(p))
    content, status = read_file(p)
    assert "SLIDE 1" in content
    assert "Quarterly Findings" in content


def test_secret_scanner_reads_inside_xlsx(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    from security.secrets import scan_file
    wb = openpyxl.Workbook()
    wb.active.append(["service", "key"])
    wb.active.append(["aws", "AKIAABCDEFGHIJKLMNOP"])
    p = tmp_path / "creds.xlsx"
    wb.save(str(p))
    findings, sensitive_name = scan_file(p)
    assert any("AWS" in label for label, _ in findings)


def test_chunker_small_file():
    text    = "word " * 100
    result, status = chunk(text, "test.txt")
    assert "complete" in status
    assert "word" in result


def test_chunker_large_file():
    text   = "word " * (MAX_WORDS + 1000)
    result, status = chunk(text, "big.txt")
    assert "omitted" in result
    assert "total" in status
