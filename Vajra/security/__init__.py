# VAJRA — Security layer: classification, gated execution, secrets, audit log.

from security.permissions import classify_command, TIER_INFO
from security.executor    import run_command
from security.secrets     import scan_text, scan_file, is_sensitive_filename, redact, warn_if_sensitive
from security.audit       import log_event, read_recent
