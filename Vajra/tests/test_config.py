# VAJRA — Config module unit tests.

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import load_config, get_model, DEFAULT_CONFIG


def test_load_config_returns_dict():
    cfg = load_config()
    assert isinstance(cfg, dict)


def test_default_model_is_string():
    model = get_model()
    assert isinstance(model, str)
    assert len(model) > 0


def test_default_config_has_required_keys():
    assert "model" in DEFAULT_CONFIG
    assert "version" in DEFAULT_CONFIG
