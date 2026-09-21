# VAJRA Security Policy

## Data Handling
VAJRA is a local-only tool. All queries, responses, embeddings, and your
document library stay on your machine. No data is sent to any external
server. No telemetry. No cloud.

## Command Execution Policy
VAJRA can execute a command on your behalf ONLY through the explicit `run`
command — never automatically, and never by parsing its own AI responses
for commands to run. You always choose the exact command; VAJRA never
chooses it for you.

Every command is classified before it runs:
  - SAFE / READ-ONLY — runs immediately (e.g. ls, ps, df)
  - MODIFYING        — requires your explicit "y" confirmation, every time
  - DANGEROUS        — requires your explicit "y" confirmation, every time,
                        shown with a loud warning
  - BLOCKED          — refused outright, no override (e.g. rm -rf /, mkfs)

There is no "trust this session" or "always allow" setting for modifying or
dangerous commands. Every single one is shown and confirmed individually.

IMPORTANT: Pattern-based classification is a best-effort safety net, not a
guarantee. A sufficiently obscure or obfuscated command can bypass it. The
real safety mechanism is you: read the literal command VAJRA shows you
before you type "y". Never approve a command you do not understand.

## Credential Protection
VAJRA scans files for likely secrets (API keys, private keys, passwords,
tokens) before reading them into an AI prompt or adding them to your
library, and warns you before proceeding. Saved session logs have any
detected secrets automatically redacted before being written to disk.

This detection is regex-based and will not catch every possible secret
format. Do not rely on it as your only safeguard — avoid pointing VAJRA at
files you know contain live credentials.

## Audit Log
Every command VAJRA runs (or refuses to run) is logged locally to
vajra_audit.log — timestamp, command, classification, and your decision.
This file never leaves your machine. View it with: vajra audit

## Ethical Use
VAJRA is built for:
- Authorised penetration testing
- CTF competitions
- Bug bounty programmes (in-scope targets only)
- Security research and learning
- Personal productivity and technical work

VAJRA must NOT be used to attack systems without explicit written authorisation.

## Reporting Security Issues
If you discover a security issue in VAJRA itself, please open a GitHub issue
marked with [SECURITY] in the title.

## Sensitive Files — Never Commit These
- vajra_config.json   (model preferences)
- vajra_sessions/      (conversation history — secrets are redacted, review before sharing)
- vajra_library/       (your document library and embeddings)
- vajra_audit.log      (command execution history)
- vajra.log            (debug logs)
- Any PDF, DOCX, or credential file you have loaded into VAJRA

These are all excluded by .gitignore.
