# VAJRA — Single query, file query, sysinfo, service, library, ask, run, and audit handlers.
# stream() shows its own thinking spinner and prints the formatted markdown
# response, so these handlers no longer call a separate thinking() step.

from rich.console import Console
from rich.rule    import Rule
from llm.models   import require_ollama, confirm_ram_or_exit
from llm.client   import stream
from llm.prompts  import PROMPTS, MODES
from parsers      import read_files
from cli.display  import (print_banner, res_header, save_to_file,
                          print_snapshot, show_audit)
from pathlib      import Path

console = Console()

SYS_KEYWORDS = {
    "ram","memory","cpu","disk","storage","space","network","port",
    "process","running","service","uptime","load","performance",
    "slow","usage","utilization","utilisation","bandwidth","interface",
    "crash","crashed","freeze","freezing","high","consuming","hang",
}


def _needs_system_context(mode: str, query: str) -> bool:
    if mode not in ("sysadmin", "linux"):
        return False
    q = query.lower()
    return any(kw in q for kw in SYS_KEYWORDS)


def _gather_system_context() -> str:
    from system import get_full_snapshot, snapshot_to_context
    snap = get_full_snapshot()
    return snapshot_to_context(snap)


def handle_query(query: str, mode: str = "default",
                 model: str = None, outfile: str = None) -> None:
    model = require_ollama(model)
    if not confirm_ram_or_exit(model): return

    print_banner()
    cfg = MODES[mode]
    console.print(f"  [{cfg['color']}]{cfg['icon']}  Mode: {cfg['label']}[/{cfg['color']}]  [dim]{model}[/dim]")
    console.print(f"  [dim]{query[:80]}{'...' if len(query)>80 else ''}[/dim]\n")
    console.print(Rule(style="color(202)"))

    full_query = query
    if _needs_system_context(mode, query):
        console.print("  [dim]◉ Gathering live system context...[/dim]")
        context    = _gather_system_context()
        full_query = f"{query}\n\nLIVE SYSTEM SNAPSHOT:\n{'─'*50}\n{context}\n{'─'*50}"

    msgs   = [{"role":"system","content":PROMPTS[mode]},
              {"role":"user",  "content":full_query}]
    res_header(mode, model)
    result = stream(msgs, model)
    console.print()
    console.print(Rule(style="color(202)"))
    console.print(f"\n  [dim color(214)]वज्र: Sharp. Precise. Unstoppable.[/dim color(214)]\n")

    if outfile and result:
        save_to_file(outfile, cfg["label"], model, query, result)


def handle_file_query(fargs: list, mode: str = "default",
                      model: str = None, outfile: str = None) -> None:
    from security.secrets import warn_if_sensitive
    model = require_ollama(model)

    def is_file(s): return Path(s).exists()

    if not fargs:
        console.print("  [red][ERROR] No files specified.[/red]")
        console.print("  [dim]Usage: vajra read report.pdf \"question\"[/dim]\n")
        return

    if len(fargs) == 1:
        files = [fargs[0]]; q = "Provide a comprehensive summary of this document."
    elif is_file(fargs[-1]):
        files = list(fargs); q = "Provide a comprehensive summary of these documents."
    else:
        files = list(fargs[:-1]); q = fargs[-1]

    print_banner()
    cfg = MODES[mode]
    console.print(f"  [{cfg['color']}]{cfg['icon']}  Mode: {cfg['label']}[/{cfg['color']}]  [dim]{model}[/dim]\n")

    if not warn_if_sensitive(files, console):
        console.print("  [dim]Cancelled.[/dim]\n")
        return

    content, statuses = read_files(files)
    for s in statuses:
        col = "red" if s.startswith("[ERROR]") else "color(214)"
        console.print(f"  [{col}]{s}[/{col}]")

    if not content.strip():
        console.print("  [red]No content could be read. Aborting.[/red]\n"); return

    console.print(f"  [dim]Question: {q[:72]}{'...' if len(q)>72 else ''}[/dim]\n")
    console.print(Rule(style="color(202)"))
    if not confirm_ram_or_exit(model): return

    user_msg = f"FILE CONTENT:\n{'─'*50}\n{content}\n{'─'*50}\n\nQUESTION: {q}"
    msgs     = [{"role":"system","content":PROMPTS[mode]},
                {"role":"user",  "content":user_msg}]
    res_header(mode, model)
    result = stream(msgs, model)
    console.print()
    console.print(Rule(style="color(202)"))
    console.print(f"\n  [dim color(214)]वज्र: Sharp. Precise. Unstoppable.[/dim color(214)]\n")

    if outfile and result:
        save_to_file(outfile, cfg["label"], model, q, result)


def handle_set_model(model_name: str) -> None:
    from llm.models import check_ollama, confirm_ram_or_exit, set_default_model
    print_banner()
    up, avail = check_ollama()
    if not up:
        console.print("\n  [red][ERROR] Ollama is not running.[/red]\n"); return
    if not any(model_name in m for m in avail):
        console.print(f"\n  [red]Model '{model_name}' not found.[/red]")
        console.print(f"  [dim]Pull: ollama pull {model_name}[/dim]\n"); return
    if not confirm_ram_or_exit(model_name): return
    if set_default_model(model_name):
        console.print(f"\n  [color(214)]◉ Default model set to: {model_name}[/color(214)]")
        console.print(f"  [dim]Saved to vajra_config.json[/dim]\n")


def handle_list_models() -> None:
    from llm.models import list_models_display
    list_models_display()


def handle_sysinfo(question: str = None, model: str = None) -> None:
    from system import get_full_snapshot, snapshot_to_context

    print_banner()
    console.print("  [color(214)]◉ Gathering system information...[/color(214)]\n")

    snap    = get_full_snapshot()
    context = snapshot_to_context(snap)

    console.print(Rule(style="color(202)"))
    print_snapshot(context)
    console.print(Rule(style="color(202)"))
    console.print()

    if not question:
        return

    model = require_ollama(model)
    if not confirm_ram_or_exit(model): return

    user_msg = (
        f"LIVE SYSTEM SNAPSHOT:\n{'─'*50}\n{context}\n{'─'*50}\n\n"
        f"QUESTION: {question}"
    )
    msgs   = [{"role":"system","content":PROMPTS["sysadmin"]},
              {"role":"user",  "content":user_msg}]
    res_header("sysadmin", model)
    result = stream(msgs, model)
    console.print()
    console.print(Rule(style="color(202)"))
    console.print(f"\n  [dim color(214)]वज्र: Sharp. Precise. Unstoppable.[/dim color(214)]\n")


def handle_service(name: str) -> None:
    from system.services import check_service
    print_banner()
    console.print(f"  [dim]Checking service: {name}...[/dim]\n")

    result, err = check_service(name)
    if err:
        console.print(f"  [red]{err}[/red]\n")
        return

    status     = result["status"]
    ok_states  = ("active", "running")
    bad_states = ("inactive", "stopped", "failed", "not found / stopped")
    col = "green" if status in ok_states else "red" if status in bad_states else "yellow"

    console.print(f"  Service  : [white]{result['name']}[/white]")
    console.print(f"  Status   : [{col}]{status}[/{col}]")
    console.print(f"  Platform : [dim]{result['platform']}[/dim]\n")


def _progress_context():
    from rich.progress import Progress, BarColumn, TextColumn
    return Progress(
        TextColumn("  [dim]{task.description}[/dim]"),
        BarColumn(bar_width=30),
        TextColumn("[dim]{task.completed}/{task.total}[/dim]"),
        console=console, transient=True,
    )


def handle_library(sub_args: list) -> None:
    if not sub_args:
        print_banner()
        console.print("  Usage: vajra library <add|list|remove|clear> [args]\n")
        return
    sub, rest = sub_args[0].lower(), sub_args[1:]
    if sub == "add":
        _handle_library_add(rest)
    elif sub == "list":
        _handle_library_list()
    elif sub == "remove":
        _handle_library_remove(" ".join(rest))
    elif sub == "clear":
        _handle_library_clear()
    else:
        print_banner()
        console.print(f"  [red]Unknown library command: {sub}[/red]")
        console.print("  [dim]Usage: vajra library <add|list|remove|clear>[/dim]\n")


def _handle_library_add(files: list) -> None:
    from rag.library import add_document
    from security.secrets import warn_if_sensitive

    print_banner()
    if not files:
        console.print("  [red][ERROR] No files specified.[/red]")
        console.print("  [dim]Usage: vajra library add report.pdf[/dim]\n")
        return

    console.print("  [color(214)]📚  VAJRA LIBRARY — Ingesting[/color(214)]\n")

    if not warn_if_sensitive(files, console):
        console.print("  [dim]Cancelled.[/dim]\n")
        return

    for f in files:
        console.print(f"  [white]{f}[/white]")
        with _progress_context() as progress:
            task = progress.add_task("Embedding...", total=1)
            def cb(done, total): progress.update(task, completed=done, total=total)
            count, err = add_document(f, progress_cb=cb)

        if err and count == 0:
            console.print(f"  [red]{err}[/red]\n")
        else:
            if err:
                console.print(f"  [yellow]{err}[/yellow]")
            console.print(f"  [green]◉ Added {count} chunks from {Path(f).name}[/green]\n")

    console.print("  [dim]Run: vajra library list — to see your full library[/dim]\n")


def _handle_library_list() -> None:
    from rag.library import list_documents
    from rag.store    import total_chunks

    print_banner()
    docs = list_documents()
    if not docs:
        console.print("  [dim]Your library is empty.[/dim]")
        console.print("  [dim]Add a document: vajra library add <file>[/dim]\n")
        return

    console.print(f"  [bold color(214)]VAJRA LIBRARY — {len(docs)} document(s), "
                  f"{total_chunks()} chunks total[/bold color(214)]")
    console.print("  " + "─"*56)
    for d in docs:
        pages = f", {d['pages']} pages" if d.get("pages") else ""
        added = d["added"][:10]
        console.print(f"  [white]{d['name']:<40}[/white] "
                      f"[dim]{d['chunks']} chunks{pages}  added {added}[/dim]")
    console.print()


def _handle_library_remove(name: str) -> None:
    from rag.library import remove_document
    print_banner()
    if not name:
        console.print("  [red]Usage: vajra library remove <name>[/red]\n"); return
    removed, err = remove_document(name)
    if err:
        console.print(f"  [red]{err}[/red]\n")
    else:
        console.print(f"  [green]◉ Removed {removed} chunks matching '{name}'[/green]\n")


def _handle_library_clear() -> None:
    from rag.library import clear_library
    print_banner()
    ans = input("  Clear the ENTIRE library? This cannot be undone. [y/N] ").strip().lower()
    if ans != "y":
        console.print("  [dim]Cancelled.[/dim]\n")
        return
    ok, err = clear_library()
    if ok:
        console.print("  [green]◉ Library cleared.[/green]\n")
    else:
        console.print(f"  [red]{err}[/red]\n")


def handle_ask(question: str, source_mode: str = "hybrid",
              model: str = None, outfile: str = None) -> None:
    from rag.retriever import retrieve, build_rag_prompt, format_citations
    from rag.library    import list_documents

    if not question:
        console.print("  [red]Usage: vajra ask \"question\"[/red]\n"); return

    model = require_ollama(model)
    if not confirm_ram_or_exit(model): return

    print_banner()
    console.print(f"  [color(214)]📚  Mode: LIBRARY ASK[/color(214)]  [dim]{model} · {source_mode}[/dim]")
    console.print(f"  [dim]{question[:80]}{'...' if len(question)>80 else ''}[/dim]\n")

    if not list_documents():
        console.print("  [yellow]Your library is empty. Add documents first:[/yellow]")
        console.print("  [dim]vajra library add <file>[/dim]\n")
        return

    console.print(Rule(style="color(202)"))
    console.print("  [dim]◉ Searching your library...[/dim]")

    hits, err = retrieve(question)
    if err:
        console.print(f"  [red]{err}[/red]\n")
        return

    if hits:
        console.print(f"  [dim]◉ Found: {format_citations(hits)}[/dim]")
    else:
        console.print("  [dim]◉ No closely matching passages found.[/dim]")

    prompt = build_rag_prompt(question, hits, source_mode)
    msgs = [{"role":"system","content":PROMPTS["doc"]},
            {"role":"user",  "content":prompt}]
    res_header("doc", model)
    result = stream(msgs, model)
    console.print()
    console.print(Rule(style="color(202)"))
    if hits:
        console.print(f"\n  [color(214)]SOURCES: {format_citations(hits)}[/color(214)]")
    console.print(f"\n  [dim color(214)]वज्र: Sharp. Precise. Unstoppable.[/dim color(214)]\n")

    if outfile and result:
        save_to_file(outfile, "LIBRARY ASK", model, question, result)


def handle_run(cmd: str) -> None:
    from security.executor import run_command
    print_banner()
    if not cmd:
        console.print("  [red]Usage: vajra run \"<command>\"[/red]\n")
        return
    run_command(cmd, console)


def handle_audit() -> None:
    from security.audit import read_recent
    print_banner()
    show_audit(read_recent(25))
