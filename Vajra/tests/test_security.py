# VAJRA — Security module unit tests. Pure logic — nothing is ever executed.

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security.permissions import classify_command
from security.secrets     import scan_text, is_sensitive_filename, redact


def test_safe_command():
    assert classify_command("ls -la") == "safe"
    assert classify_command("df -h") == "safe"
    assert classify_command("ps aux") == "safe"


def test_modifying_command():
    assert classify_command("mkdir test") == "modifying"
    assert classify_command("apt install nmap") == "modifying"


def test_dangerous_command():
    assert classify_command("rm -rf ./build") == "dangerous"
    assert classify_command("git reset --hard") == "dangerous"
    assert classify_command("shutdown now") == "dangerous"


def test_blocked_command():
    assert classify_command("rm -rf /") == "blocked"
    assert classify_command("mkfs.ext4 /dev/sda1") == "blocked"


def test_empty_command_is_safe():
    assert classify_command("") == "safe"
    assert classify_command("   ") == "safe"


def test_secret_scan_detects_aws_key():
    text = "aws_key = AKIAABCDEFGHIJKLMNOP"
    findings = scan_text(text)
    assert any("AWS" in label for label, _ in findings)


def test_secret_scan_detects_private_key():
    text = "-----BEGIN RSA PRIVATE KEY-----\nMIIExyz\n-----END RSA PRIVATE KEY-----"
    findings = scan_text(text)
    assert any("Private Key" in label for label, _ in findings)


def test_secret_scan_clean_text():
    text = "This is just a normal paragraph about networking concepts."
    findings = scan_text(text)
    assert findings == []


def test_sensitive_filename_detection():
    assert is_sensitive_filename(".env") is True
    assert is_sensitive_filename("id_rsa") is True
    assert is_sensitive_filename("notes.txt") is False


def test_redact_removes_secret():
    text = "api_key = supersecretvalue123456"
    redacted = redact(text)
    assert "supersecretvalue123456" not in redacted
    assert "REDACTED" in redacted
