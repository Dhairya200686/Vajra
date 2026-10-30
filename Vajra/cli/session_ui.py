# VAJRA — Interactive session loop: mode/model switching, files, system tools,
# library/RAG, and gated command execution. stream() shows its own thinking
# spinner and prints the formatted markdown response, so these branches no
# longer call a separate thinking() step.

from pathlib      import Path
from rich.console import Console
from rich.rule    import Rule
from core.session import Session
from llm.models   import require_ollama, confirm_ram_or_exit, check_ollama
from llm.client   import stream
from llm.prompts  import MODES, PROMPTS
from parsers      import read_file, read_files
from cli.display  import (session_header, session_help, show_history,
                          res_header, print_snapshot, show_audit)

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


def _progress_context():
    from rich.progress import Progress, BarColumn, TextColumn
    return Progress(
        TextColumn("  [dim]{task.description}[/dim]"),
        BarColumn(bar_width=30),
        TextColumn("[dim]{task.completed}/{task.total}[/dim]"),
        console=console, transient=True,
    )


def run_session(mode: str = "default", model: str = None,
                load_file: str = None) -> None:
    model = require_ollama(model)
    if not confirm_ram_or_exit(model): return

    fc, fn = "", ""
    if load_file:
        lp = Path(load_file)
        content, status = read_file(lp)
        fc  = content or ""
        fn  = lp.name if content else ""
        col = "color(214)" if content else "red"
        console.print(f"  [{col}]{status}[/{col}]")

    s = Session(mode, model, fc, fn)
    state = {"source_mode": "hybrid"}
    session_header(s)

    def farewell():
        console.print()
        path = s.save()
        console.print(f"  [color(214)]◉ Session saved: {path}[/color(214)]")
        from datetime import datetime
        dur = (datetime.now() - s.start).seconds // 60
        console.print(f"  [dim]Exchanges: {s.count}  |  Duration: {dur} min[/dim]")
        console.print(f"\n  [bold color(202)]VAJRA offline. Stay sharp.[/bold color(202)]\n")

    while True:
        try:
            cfg = MODES[s.mode]
            console.print(
                f"  [{cfg['color']}]VAJRA [{cfg['label']}] >[/{cfg['color']}] ",
                end="")
            raw = input("").strip()
            if not raw: continue
            cmd = raw.lower()

            if cmd in ("exit","quit","q"):
                farewell(); break

            elif cmd == "help":
                session_help()

            elif cmd == "clear":
                session_header(s)

            elif cmd == "history":
                show_history(s)

            elif cmd == "save":
                path = s.save()
                console.print(f"\n  [green]◉ Saved: {path}[/green]\n")

            elif cmd == "reset":
                s.history, s.log, s.count, s.fc, s.fn = [], [], 0, "", ""
                console.print(f"\n  [yellow]◉ Memory and loaded file cleared.[/yellow]\n")

            elif cmd == "sysinfo" or cmd.startswith("sysinfo "):
                from system import get_full_snapshot, snapshot_to_context
                console.print("\n  [dim]◉ Gathering system information...[/dim]\n")
                snap    = get_full_snapshot()
                context = snapshot_to_context(snap)
                print_snapshot(context)
                console.print()

                question = raw[len("sysinfo"):].strip()
                if question:
                    um = (f"LIVE SYSTEM SNAPSHOT:\n{'─'*50}\n{context}\n{'─'*50}\n\n"
                         f"QUESTION: {question}")
                    msgs = [{"role":"system","content":PROMPTS["sysadmin"]}]
                    msgs += s.history
                    msgs.append({"role":"user","content":um})
                    res_header("sysadmin", s.model)
                    result = stream(msgs, s.model)
                    console.print()
                    console.print(Rule(style="dim"))
                    console.print()
                    if result:
                        s.add(f"[SYSINFO] {question}", result)

            elif cmd.startswith("service "):
                name = raw.split(None, 1)[1].strip()
                from system.services import check_service
                result, err = check_service(name)
                if err:
                    console.print(f"\n  [red]{err}[/red]\n")
                else:
                    status = result["status"]
                    ok  = ("active","running")
                    bad = ("inactive","stopped","failed","not found / stopped")
                    col = "green" if status in ok else "red" if status in bad else "yellow"
                    console.print(f"\n  Service: [white]{result['name']}[/white]  "
                                 f"Status: [{col}]{status}[/{col}]\n")

            elif cmd == "library" or cmd.startswith("library "):
                parts = raw.split()[1:]
                if not parts:
                    console.print("\n  [red]Usage: library <add|list|remove|clear> [args][/red]\n")
                else:
                    sub, rest = parts[0].lower(), parts[1:]

                    if sub == "add":
                        from rag.library import add_document
                        from security.secrets import warn_if_sensitive
                        if not rest:
                            console.print("\n  [red]Usage: library add <file>[/red]\n")
                        elif not warn_if_sensitive(rest, console):
                            console.print("  [dim]Cancelled.[/dim]\n")
                        else:
                            for f in rest:
                                console.print(f"\n  [white]{f}[/white]")
                                with _progress_context() as progress:
                                    task = progress.add_task("Embedding...", total=1)
                                    def cb(done, total): progress.update(task, completed=done, total=total)
                                    count, err = add_document(f, progress_cb=cb)
                                if err and count == 0:
                                    console.print(f"  [red]{err}[/red]\n")
                                else:
                                    if err: console.print(f"  [yellow]{err}[/yellow]")
                                    console.print(f"  [green]◉ Added {count} chunks "
                                                 f"from {Path(f).name}[/green]\n")

                    elif sub == "list":
                        from rag.library import list_documents
                        from rag.store    import total_chunks
                        docs = list_documents()
                        console.print()
                        if not docs:
                            console.print("  [dim]Your library is empty.[/dim]\n")
                        else:
                            console.print(f"  [bold color(214)]LIBRARY — {len(docs)} "
                                         f"document(s), {total_chunks()} chunks[/bold color(214)]")
                            for d in docs:
                                console.print(f"  [white]{d['name']:<40}[/white] "
                                             f"[dim]{d['chunks']} chunks[/dim]")
                            console.print()

                    elif sub == "remove":
                        from rag.library import remove_document
                        name = " ".join(rest)
                        removed, err = remove_document(name)
                        if err:
                            console.print(f"\n  [red]{err}[/red]\n")
                        else:
                            console.print(f"\n  [green]◉ Removed {removed} chunks "
                                         f"matching '{name}'[/green]\n")

                    elif sub == "clear":
                        from rag.library import clear_library
                        ans = input("\n  Clear entire library? [y/N] ").strip().lower()
                        if ans == "y":
                            ok, err = clear_library()
                            if ok:
                                console.print("  [green]◉ Library cleared.[/green]\n")
                            else:
                                console.print(f"  [red]{err}[/red]\n")
                        else:
                            console.print("  [dim]Cancelled.[/dim]\n")

                    else:
                        console.print(f"\n  [red]Unknown: library {sub}[/red]\n")

            elif cmd.startswith("sourcemode "):
                new_mode = cmd.split("sourcemode ", 1)[1].strip()
                if new_mode in ("source-only","source-first","hybrid"):
                    state["source_mode"] = new_mode
                    console.print(f"\n  [color(214)]◉ Source mode: {new_mode}[/color(214)]\n")
                else:
                    console.print("\n  [red]Options: source-only | source-first | hybrid[/red]\n")

            elif cmd == "ask" or cmd.startswith("ask "):
                question = raw[len("ask"):].strip()
                if not question:
                    console.print("\n  [red]Usage: ask <question>[/red]\n")
                else:
                    from rag.retriever import retrieve, build_rag_prompt, format_citations
                    from rag.library    import list_documents
                    if not list_documents():
                        console.print("\n  [yellow]Library is empty. "
                                     "Add documents: library add <file>[/yellow]\n")
                    else:
                        console.print("\n  [dim]◉ Searching your library...[/dim]")
                        hits, err = retrieve(question)
                        if err:
                            console.print(f"  [red]{err}[/red]\n")
                        else:
                            if hits:
                                console.print(f"  [dim]◉ Found: {format_citations(hits)}[/dim]")
                            else:
                                console.print("  [dim]◉ No closely matching passages found.[/dim]")
                            prompt = build_rag_prompt(question, hits, state["source_mode"])
                            msgs = [{"role":"system","content":PROMPTS["doc"]}]
                            msgs.append({"role":"user","content":prompt})
                            res_header("doc", s.model)
                            result = stream(msgs, s.model)
                            console.print()
                            if hits:
                                console.print(f"  [color(214)]SOURCES: "
                                             f"{format_citations(hits)}[/color(214)]")
                            console.print(Rule(style="dim"))
                            console.print()
                            if result:
                                s.add(f"[ASK] {question}", result)

            elif cmd.startswith("run "):
                from security.executor import run_command
                run_command(raw[len("run "):].strip(), console)

            elif cmd == "audit":
                from security.audit import read_recent
                show_audit(read_recent(25))

            elif cmd.startswith("mode "):
                new = cmd.split("mode ", 1)[1].strip()
                if new in MODES:
                    note = ""
                    if new != s.mode and s.history:
                        s.history = []
                        note = "  [dim](conversation memory cleared for the new persona)[/dim]"
                    s.mode = new
                    c = MODES[new]
                    console.print(f"\n  [{c['color']}]{c['icon']}  Switched to: {c['label']}[/{c['color']}]{note}\n")
                else:
                    console.print(f"\n  [red]Unknown mode '{new}'.[/red]")
                    console.print("  [dim]Options: default|linux|dev|sysadmin|cyber|doc[/dim]\n")

            elif cmd.startswith("setmodel "):
                nm = raw.split("setmodel ", 1)[1].strip()
                _, avail = check_ollama()
                if any(nm in m for m in avail):
                    if not confirm_ram_or_exit(nm): continue
                    s.model = nm
                    console.print(f"\n  [color(214)]◉ Model switched to: {nm}[/color(214)]\n")
                else:
                    console.print(f"\n  [red]Model '{nm}' not found in Ollama.[/red]")
                    console.print(f"  [dim]Pull: ollama pull {nm}[/dim]\n")

            elif cmd.startswith("read "):
                parts = raw.split()[1:]
                if not parts:
                    console.print("\n  [red]Usage: read <file> [question][/red]\n"); continue

                file_parts, q_parts = [], []
                for p in parts:
                    if Path(p).exists() and not q_parts:
                        file_parts.append(p)
                    else:
                        q_parts.append(p)

                if not file_parts:
                    console.print(f"\n  [red]File not found: {parts[0]}[/red]\n"); continue

                from security.secrets import warn_if_sensitive
                if not warn_if_sensitive(file_parts, console):
                    console.print("  [dim]Cancelled.[/dim]\n"); continue

                fc2, sts = read_files([Path(f) for f in file_parts])
                for st in sts:
                    col = "red" if st.startswith("[ERROR]") else "color(214)"
                    console.print(f"\n  [{col}]{st}[/{col}]")

                if not fc2: continue
                question = " ".join(q_parts) if q_parts else None

                if not question:
                    s.fc = fc2
                    s.fn = ", ".join(file_parts)
                    console.print("  [color(214)]◉ File loaded. Ask questions about it.[/color(214)]\n")
                else:
                    um   = f"FILE CONTENT:\n{'─'*50}\n{fc2}\n{'─'*50}\n\nQUESTION: {question}"
                    msgs = [{"role":"system","content":PROMPTS[s.mode]}]
                    msgs += s.history
                    msgs.append({"role":"user","content":um})
                    res_header(s.mode, s.model)
                    result = stream(msgs, s.model)
                    console.print()
                    console.print(Rule(style="dim"))
                    console.print()
                    if result:
                        s.add(f"[FILE:{', '.join(file_parts)}] {question}", result)

            else:
                query = raw
                if _needs_system_context(s.mode, raw):
                    console.print("\n  [dim]◉ Gathering live system context...[/dim]")
                    from system import get_full_snapshot, snapshot_to_context
                    snap    = get_full_snapshot()
                    context = snapshot_to_context(snap)
                    query   = f"{raw}\n\nLIVE SYSTEM SNAPSHOT:\n{'─'*50}\n{context}\n{'─'*50}"

                msgs   = s.messages(query)
                res_header(s.mode, s.model)
                result = stream(msgs, s.model)
                console.print()
                console.print(Rule(style="dim"))
                console.print()
                if result:
                    s.add(raw, result)

        except (KeyboardInterrupt, EOFError):
            farewell(); break
