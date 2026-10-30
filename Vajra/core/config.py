# VAJRA — Core configuration management.

import json
from pathlib import Path

VERSION = "2.4.1"

BASE_DIR    = Path(__file__).parent.parent
CONFIG_FILE = BASE_DIR / "vajra_config.json"
SESSION_DIR = BASE_DIR / "vajra_sessions"
SESSION_DIR.mkdir(exist_ok=True)

DEFAULT_CONFIG = {
    "model":   "gemma4:e4b",
    "version": VERSION,
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg: dict) -> None:
    tmp = CONFIG_FILE.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        tmp.replace(CONFIG_FILE)
    except Exception:
        pass


def get_model() -> str:
    return load_config().get("model", DEFAULT_CONFIG["model"])
