# VAJRA — Command classification: safe / modifying / dangerous / blocked.
# Best-effort safety net, not a complete defense — see SECURITY.md.

import re
from security.blocklist import is_blocked

DANGEROUS_PATTERNS = [
    r"\brm\s+-[a-z]*r",
    r"\bdel\s+/s\b",
    r"\bdrop\s+table\b",
    r"\bdrop\s+database\b",
    r"\btruncate\s+table\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bsystemctl\s+(stop|disable|mask)\b",
    r"\bnet\s+stop\b",
    r"\biptables\s+-F\b",
    r"\bufw\s+disable\b",
    r"\bchmod\s+-R\s+777\b",
    r"\bchown\s+-R\b",
    r"\bgit\s+push\s+.*--force\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bdocker\s+system\s+prune\b",
    r"\bkill\s+-9\s+1\b",
]

MODIFYING_PATTERNS = [
    r"\bmkdir\b", r"\btouch\b", r"\bmv\b", r"\bcp\b",
    r"\bapt(-get)?\s+(install|remove|upgrade)\b",
    r"\bdnf\s+(install|remove)\b", r"\bpacman\s+-S\b",
    r"\bpip3?\s+install\b", r"\bnpm\s+install\b",
    r"\bsystemctl\s+(start|restart|enable)\b",
    r"\bgit\s+(add|commit|pull|checkout|branch)\b",
    r"\bsc\s+start\b", r"\bnet\s+start\b",
]

TIER_INFO = {
    "safe":      {"label": "SAFE / READ-ONLY", "color": "green",  "needs_confirm": False},
    "modifying": {"label": "MODIFYING",         "color": "yellow", "needs_confirm": True},
    "dangerous": {"label": "DANGEROUS",         "color": "red",    "needs_confirm": True},
    "blocked":   {"label": "BLOCKED",           "color": "red",    "needs_confirm": None},
}


def classify_command(cmd: str) -> str:
    c = cmd.strip().lower()
    if not c:
        return "safe"
    if is_blocked(c):
        return "blocked"
    for pat in DANGEROUS_PATTERNS:
        if re.search(pat, c):
            return "dangerous"
    for pat in MODIFYING_PATTERNS:
        if re.search(pat, c):
            return "modifying"
    return "safe"
