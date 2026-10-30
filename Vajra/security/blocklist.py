# VAJRA — Hard-denied catastrophic command patterns. No override, ever.

import re

BLOCKED_PATTERNS = [
    r"\brm\s+-[a-z]*r[a-z]*f\s+/\s*$",
    r"\brm\s+-[a-z]*r[a-z]*f\s+/\*",
    r"\brm\s+-[a-z]*f[a-z]*r\s+/\s*$",
    r":\(\)\s*\{\s*:\|:&\s*\}\s*;\s*:",
    r"\bmkfs\.",
    r"\bdd\s+.*of=/dev/(sd|nvme|hd)",
    r"\bformat\s+[a-zA-Z]:\s*(/y)?\s*$",
    r"\bdel\s+/f\s+/s\s+/q\s+[a-zA-Z]:\\?\s*$",
    r">\s*/dev/sd[a-z]\b",
    r"\bshred\b.*-{1,2}remove\b.*/\s*$",
]


def is_blocked(cmd: str) -> bool:
    c = cmd.strip().lower()
    return any(re.search(p, c) for p in BLOCKED_PATTERNS)
