# VAJRA — Argument parser. No logic here, only structure.

import argparse
from llm.prompts import MODES

EPILOG = """
MODES:
  default     General technical assistant — Linux, Windows, Ubuntu
  linux       Linux/Ubuntu specialist — commands, scripting, distros
  dev         Developer — code review, debugging, refactoring
  sysadmin    SysAdmin/DevOps — logs, configs, servers, networking
  cyber       Cybersecurity — CTF, bug bounty, payload, recon, hardware
  doc         Document analyst — summarise, extract, question files

EXAMPLES:
  python vajra.py "how do I find files larger than 1GB in Linux"
  python vajra.py -m linux "set up a cron job every 5 minutes"
  python vajra.py -m dev "explain what a decorator does in Python"
  python vajra.py -m sysadmin "nginx keeps returning 502"
  python vajra.py -m cyber "what is blind SQL injection"
  python vajra.py read report.pdf "summarise the key findings"
  python vajra.py read scan_results.xlsx "what stands out?"
  python vajra.py read briefing.pptx "summarise this deck"
  python vajra.py read analysis.ipynb "review this notebook"
  python vajra.py sysinfo
  python vajra.py service nginx

  python vajra.py library add report.pdf
  python vajra.py library list
  python vajra.py ask "explain ARP spoofing"
  python vajra.py ask "question" --source-mode source-only

  python vajra.py run "ls -la"
  python vajra.py audit

  python vajra.py -s
  python vajra.py -s -m sysadmin
  python vajra.py -s --load report.pdf
  python vajra.py --model llama3.1:8b "explain kernel scheduling"
  python vajra.py --set-model llama3.1:8b
  python vajra.py --list-models
  python vajra.py -m dev read script.py -o review.txt

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  VAJRA — Local AI. No cloud. No key. Yours.
  The thunderbolt strikes with precision. — वज्र
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def build_parser() -> argparse.ArgumentParser:
    from core.config import VERSION
    parser = argparse.ArgumentParser(
        prog="vajra",
        description="VAJRA (वज्र) v2.4.1 — Universal Technical Intelligence CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG,
    )
    parser.add_argument("args",          nargs="*",
                        help="Query, or: read|sysinfo|service|library|ask|run|audit ...")
    parser.add_argument("-s","--session",action="store_true",
                        help="Start interactive session with memory")
    parser.add_argument("-m","--mode",   choices=list(MODES.keys()),
                        default="default", help="Set mode")
    parser.add_argument("--model",       metavar="MODEL",
                        help="Use specific model one-time")
    parser.add_argument("--set-model",   metavar="MODEL", dest="set_model",
                        help="Set default model permanently")
    parser.add_argument("--list-models", action="store_true", dest="list_models",
                        help="List all available Ollama models")
    parser.add_argument("--load",        metavar="FILE",
                        help="Load file into session at start (use with -s)")
    parser.add_argument("--source-mode", choices=["source-only","source-first","hybrid"],
                        default="hybrid", dest="source_mode",
                        help="How 'ask' uses your library: source-only|source-first|hybrid")
    parser.add_argument("-o","--output", metavar="FILE",
                        help="Save response to file")
    parser.add_argument("--version",     action="version",
                        version=f"VAJRA v{VERSION}")
    return parser
