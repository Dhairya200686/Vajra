# VAJRA — Local audit log of every command proposed, approved/rejected, and its result.

import json
from pathlib  import Path
from datetime import datetime
from core.config import BASE_DIR

AUDIT_FILE = BASE_DIR / "vajra_audit.log"


def log_event(command: str, tier: str, decision: str, result: str = "") -> None:
    entry = {
        "time":     datetime.now().isoformat(),
        "command":  command,
        "tier":     tier,
        "decision": decision,
        "result":   (result or "")[:200],
    }
    try:
        with open(AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def read_recent(n: int = 25) -> list:
    if not AUDIT_FILE.exists():
        return []
    try:
        lines   = AUDIT_FILE.read_text(encoding="utf-8").strip().split("\n")
        entries = []
        for line in lines[-n:]:
            if not line.strip():
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                continue
        return entries
    except Exception:
        return []
