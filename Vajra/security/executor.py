# VAJRA — The ONLY place in VAJRA that runs a shell command.
#
# Every command goes through: classify -> show the exact text -> per-command
# confirmation for modifying/dangerous tiers, every single time, with no
# "trust this session" bypass -> run -> audit log.
#
# VAJRA never auto-extracts a command from its own AI-generated text and
# offers to run it. `run` only ever executes the exact literal text the
# user typed themselves — the human always chooses the command.

import subprocess
from security.permissions import classify_command, TIER_INFO
from security.audit       import log_event

TIMEOUT = 30


def run_command(cmd: str, console) -> tuple:
    cmd = cmd.strip()
    if not cmd:
        return False, ""

    tier = classify_command(cmd)
    info = TIER_INFO[tier]

    console.print()
    console.print(f"  [bold {info['color']}]COMMAND [{info['label']}][/bold {info['color']}]")
    console.print(f"  [white]$ {cmd}[/white]")

    if tier == "blocked":
        console.print("  [red]VAJRA will not run this — it matches a blocked, "
                      "catastrophic pattern. No override.[/red]\n")
        log_event(cmd, tier, "blocked")
        return False, ""

    if info["needs_confirm"]:
        reason = "modifies system state" if tier == "modifying" else "is high-impact and hard to reverse"
        console.print(f"  [{info['color']}]This command {reason}.[/{info['color']}]")
        ans = input("  Run this exact command? [y/N] ").strip().lower()
        if ans != "y":
            console.print("  [dim]Not run.[/dim]\n")
            log_event(cmd, tier, "rejected")
            return False, ""

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=TIMEOUT)
        output = (result.stdout or "") + (result.stderr or "")
        if output.strip():
            console.print(f"\n  [dim]{output[:2000]}[/dim]\n")
        else:
            console.print("  [dim](no output)[/dim]\n")
        log_event(cmd, tier, "approved" if info["needs_confirm"] else "auto", output)
        return True, output
    except subprocess.TimeoutExpired:
        console.print(f"  [red]Command timed out after {TIMEOUT}s.[/red]\n")
        log_event(cmd, tier, "timeout")
        return False, ""
    except Exception as e:
        console.print(f"  [red]Execution failed: {e}[/red]\n")
        log_event(cmd, tier, "error", str(e))
        return False, ""
