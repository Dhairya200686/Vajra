# VAJRA — Model management unit tests.

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.models import estimate_model_ram, ram_warning


def test_estimate_known_size():
    assert estimate_model_ram("llama3.1:8b") == 6
    assert estimate_model_ram("llama3.3:70b") == 42
    assert estimate_model_ram("gemma4:e4b") == 4


def test_estimate_unknown_model():
    result = estimate_model_ram("unknown-model-xyz")
    assert result is None


def test_ram_warning_returns_string_or_none():
    result = ram_warning("llama3.1:8b")
    assert result is None or isinstance(result, str)
