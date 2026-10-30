# VAJRA — All terminal output, Rich formatting, colours, and display helpers.
# The "thinking" spinner lives inside llm/client.py's stream() function,
# since it needs to transition into the printed markdown response.

from rich.console import Console
from rich.rule    import Rule
from llm.prompts  import MODES

console = Console()

BANNER = r"""
 ██╗   ██╗ █████╗      ██╗██████╗  █████╗
 ██║   ██║██╔══██╗     ██║██╔══██╗██╔══██╗
 ██║   ██║███████║     ██║██████╔╝███████║
 ╚██╗ ██╔╝██╔══██║██   ██║██╔══██╗██╔══██║
  ╚████╔╝ ██║  ██║╚█████╔╝██║  ██║██║  ██║
   ╚═══╝  ╚═╝  ╚═╝ ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝"""


def print_banner() -> None:
    from core.config import get_model, VERSION
    console.print(BANNER, style="bold color(202)")
    console.print(
        f"  [color(214)]वज्र[/color(214)]  "
        f"[dim]Universal Technical Intelligence CLI[/dim]  "
        f"[dim]v{VERSION}[/dim]  "
        f"[dim]Model: {get_model()}[/dim]"
    )
    console.print()


def res_header(mode: str, model: str) -> None:
    cfg = MODES[mode]
    console.print(f"\n  [{cfg['color']}]{'─'*56}[/{cfg['color']}]")
    console.print(f"  [{cfg['color']}]{cfg['icon']}  VAJRA [{cfg['label']}]  ·  {model}[/{cfg['color']}]")
    console.print(f"  [{cfg['color']}]{'─'*56}[/{cfg['color']}]\n")


def divider() -> None:
    console.print(Rule(style="dim"))
    console.print()


def print_snapshot(context: str) -> None:
    headers = ("SYSTEM INFORMATION:", "RESOURCES:", "NETWORK:",
              "TOP PROCESSES", "NOTE:")
    for line in context.split("\n"):
        if line.startswith(headers):
            console.print(f"\n  [bold color(214)]{line}[/bold color(214)]")
        elif line.strip():
            console.print(f"  [white]{line}[/white]")
        else:
            console.print()


def session_header(session) -> None:
    console.clear()
    print_banner()
    console.print(Rule(style="color(202)"))
    cfg = MODES[session.mode]
    console.print(
        f"  [{cfg['color']}]{cfg['icon']}  Mode: {cfg['label']}[/{cfg['color']}]  "
        f"[dim]|[/dim]  [dim]Model: {session.model}[/dim]  "
        f"[dim]|[/dim]  [dim]Memory: ON[/dim]"
    )
    if session.fn:
        console.print(f"  [color(214)]📄  Loaded: {session.fn}[/color(214)]")
    console.print(Rule(style="color(202)"))
    console.print()
    console.print(
        "  [dim]Commands: [white]mode[/white] · [white]setmodel[/white] · "
        "[white]read[/white] · [white]sysinfo[/white] · [white]service[/white] · "
        "[white]library[/white] · [white]ask[/white] · [white]sourcemode[/white] · "
        "[white]run[/white] · [white]audit[/white] · "
        "[white]history[/white] · [white]clear[/white] · "
        "[white]save[/white] · [white]reset[/white] · [white]help[/white] · "
        "[white]exit[/white][/dim]"
    )
    console.print()


def session_help() -> None:
    console.print()
    for cmd, desc in [
        ("mode <name>",     "Switch: default|linux|dev|sysadmin|cyber|doc"),
        ("setmodel <name>", "Switch AI model for this session"),
        ("read <file>",     "Load a file into session memory"),
        ("read <f> <q>",    "Load file and ask question immediately"),
        ("sysinfo",         "Show live system snapshot"),
        ("sysinfo <q>",     "Show snapshot + AI health analysis"),
        ("service <name>",  "Check if a service is running"),
        ("library add <f>", "Add a file to your local knowledge library"),
        ("library list",    "Show documents in your library"),
        ("library remove <n>","Remove a document from the library"),
        ("library clear",   "Wipe the entire library"),
        ("ask <question>",  "Ask, grounded in your library (with citations)"),
        ("sourcemode <m>",  "source-only | source-first | hybrid"),
        ("run <command>",   "Run a command — classified and confirmed first"),
        ("audit",           "Show recent command execution history"),
        ("history",         "Show all exchanges this session"),
        ("clear",            "Clear the screen"),
        ("save",            "Save session to file now"),
        ("reset",           "Clear all memory and loaded file"),
        ("help",            "Show these commands"),
        ("exit / quit",     "Exit and auto-save session"),
    ]:
        console.print(f"  [white]{cmd:<22}[/white] [dim]{desc}[/dim]")
    console.print()


def show_history(session) -> None:
    console.print()
    console.print(f"  [bold color(214)]HISTORY — {session.count} exchanges[/bold color(214)]")
    console.print("  " + "─"*52)
    if not session.log:
        console.print("  [dim]No exchanges yet.[/dim]\n")
        return
    for i, e in enumerate(session.log, 1):
        cfg = MODES.get(
            e["mode"].lower().replace(" ","").replace("bugbounty","cyber"),
            MODES["default"])
        console.print(
            f"  [dim]{i:02d}[/dim]  [color(214)]{e['time']}[/color(214)]  "
            f"[{cfg['color']}]{e['mode']}[/{cfg['color']}]  [dim]{e['model']}[/dim]")
        q = e["q"]
        console.print(f"  [dim]    {q[:72]}{'...' if len(q)>72 else ''}[/dim]")
        console.print()
    console.print()


def show_audit(entries: list) -> None:
    console.print()
    if not entries:
        console.print("  [dim]No audit history yet.[/dim]\n")
        return
    console.print(f"  [bold color(214)]AUDIT LOG — last {len(entries)} events[/bold color(214)]")
    console.print("  " + "─"*56)
    tier_col = {"safe":"green","modifying":"yellow","dangerous":"red","blocked":"red"}
    for e in entries:
        col = tier_col.get(e.get("tier"), "white")
        console.print(
            f"  [dim]{e.get('time','')[:19]}[/dim]  "
            f"[{col}]{e.get('tier',''):<10}[/{col}]  "
            f"[white]{e.get('decision',''):<10}[/white]  "
            f"[dim]{e.get('command','')[:50]}[/dim]")
    console.print()


def save_to_file(path: str, label: str, model: str, query: str, result: str) -> None:
    from pathlib import Path
    from datetime import datetime
    from security.secrets import redact
    try:
        Path(path).write_text(
            f"VAJRA v2 Output\nMode : {label}\nModel: {model}\n"
            f"Query: {query}\nTime : {datetime.now()}\n{'='*60}\n\n{redact(result)}",
            encoding="utf-8")
        console.print(f"  [green]◉ Saved: {path}[/green]\n")
    except Exception as e:
        console.print(f"  [red]◉ Save failed: {e}[/red]\n")
