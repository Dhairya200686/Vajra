# VAJRA — Detects likely credentials/secrets in text, and redacts them before
# saving to disk. Regex-based, best-effort — see SECURITY.md for caveats.

import re
from pathlib import Path

SECRET_PATTERNS = [
    ("AWS Access Key",        r"AKIA[0-9A-Z]{16}"),
    ("AWS Secret Key",        r"(?i)aws_secret_access_key\s*=\s*['\"]?[A-Za-z0-9/+=]{40}"),
    ("Private Key Block",     r"-----BEGIN (RSA |EC |OPENSSH |DSA |)PRIVATE KEY-----"),
    ("GitHub Token",          r"gh[pousr]_[A-Za-z0-9]{20,}"),
    ("Slack Token",           r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    ("Generic API Key",       r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
    ("Generic Secret/Token",  r"(?i)(secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
    ("Password Assignment",   r"(?i)password\s*[:=]\s*['\"]?\S{6,}"),
    ("JWT Token",             r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ("Database URL w/ creds", r"(?i)(postgres|mysql|mongodb)(\+\w+)?://[^:\s]+:[^@\s]+@"),
]

SENSITIVE_FILENAMES = {
    ".env", "id_rsa", "id_ed25519", "id_ecdsa", "credentials",
    "secrets.yaml", "secrets.yml",
}


def scan_text(text: str) -> list:
    findings = []
    for label, pattern in SECRET_PATTERNS:
        matches = re.findall(pattern, text or "")
        if matches:
            findings.append((label, len(matches)))
    return findings


def is_sensitive_filename(path) -> bool:
    p    = Path(path)
    name = p.name.lower()
    if name in SENSITIVE_FILENAMES:
        return True
    if p.suffix.lower() in (".pem", ".key", ".pfx", ".p12"):
        return True
    if name.startswith("id_") and "pub" not in name:
        return True
    return False


# Scans the text VAJRA would actually read from the file. For PDF, DOCX,
# XLSX, PPTX, and IPYNB that means the extracted text — those are zipped or
# structured containers, so a regex over the raw bytes would never match.
def scan_file(path) -> tuple:
    p = Path(path)
    sensitive_name = is_sensitive_filename(p)
    findings = []
    try:
        from parsers import extract_text
        text, err = extract_text(p)
        if text:
            findings = scan_text(text)
    except Exception:
        pass
    return findings, sensitive_name


def redact(text: str) -> str:
    redacted = text or ""
    for label, pattern in SECRET_PATTERNS:
        redacted = re.sub(pattern, f"[REDACTED:{label}]", redacted)
    return redacted


def warn_if_sensitive(files: list, console) -> bool:
    any_flag = False
    for f in files:
        findings, sensitive_name = scan_file(f)
        if findings or sensitive_name:
            any_flag = True
            console.print(f"\n  [yellow][WARNING] Possible secrets in {Path(f).name}:[/yellow]")
            if sensitive_name:
                console.print("  [yellow]  - Filename pattern suggests credentials/keys[/yellow]")
            for label, count in findings:
                plural = "es" if count > 1 else ""
                console.print(f"  [yellow]  - {label} ({count} match{plural})[/yellow]")
    if any_flag:
        ans = input("\n  Continue anyway? [y/N] ").strip().lower()
        return ans == "y"
    return True
