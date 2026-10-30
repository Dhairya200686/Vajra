# VAJRA — Ollama model management, RAM validation, and model listing.

import sys
import requests
from core.config import get_model, load_config, save_config
from core.logger import get_logger

logger   = get_logger("vajra.models")
TAGS_URL = "http://localhost:11434/api/tags"

MODEL_RAM = {
    "1b":2,"1.5b":2,"2b":2,"3b":3,"4b":4,"7b":5,"8b":6,
    "9b":7,"11b":9,"13b":10,"14b":10,"20b":14,"22b":16,
    "32b":22,"34b":24,"40b":28,"70b":42,"72b":44,"90b":55,
}


def check_ollama() -> tuple:
    try:
        r = requests.get(TAGS_URL, timeout=5)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            return True, models
        return False, []
    except Exception:
        return False, []


def require_ollama(model: str = None) -> str:
    from rich.console import Console
    console   = Console()
    use_model = model or get_model()
    up, avail = check_ollama()
    if not up:
        console.print("\n  [red][ERROR] Ollama is not running.[/red]")
        console.print("  [dim]Run: ollama serve[/dim]\n")
        sys.exit(1)
    if not any(use_model in m for m in avail):
        console.print(f"\n  [red][ERROR] Model '{use_model}' not found in Ollama.[/red]")
        console.print(f"  [dim]Run: ollama pull {use_model}[/dim]\n")
        sys.exit(1)
    logger.info("Using model: %s", use_model)
    return use_model


def estimate_model_ram(name: str):
    n = name.lower()
    for k, gb in sorted(MODEL_RAM.items(),
                         key=lambda x: float(x[0].replace("b", "")), reverse=True):
        if k in n:
            return gb
    return None


def ram_warning(model_name: str):
    try:
        import psutil
        sys_ram = psutil.virtual_memory().total / (1024**3)
        needed  = estimate_model_ram(model_name)
        if needed and needed > sys_ram * 0.75:
            return (
                f"  RAM WARNING: '{model_name}' needs ~{needed}GB.\n"
                f"  Your system has {sys_ram:.1f}GB total.\n"
                f"  Performance may degrade or crash.\n"
                f"  Consider a smaller model."
            )
    except ImportError:
        pass
    return None


def confirm_ram_or_exit(model_name: str) -> bool:
    w = ram_warning(model_name)
    if w:
        from rich.console import Console
        Console().print(f"\n  [yellow]{w}[/yellow]")
        ans = input("  Continue anyway? [y/N] ").strip().lower()
        if ans != "y":
            print("  Aborted.")
            return False
    return True


def set_default_model(model_name: str) -> bool:
    up, avail = check_ollama()
    if not up or not any(model_name in m for m in avail):
        return False
    cfg = load_config()
    cfg["model"] = model_name
    save_config(cfg)
    return True


def list_models_display() -> None:
    from rich.console import Console
    from cli.display  import print_banner
    console = Console()
    print_banner()

    up, models = check_ollama()
    if not up:
        console.print("  [red][ERROR] Ollama is not running.[/red]\n")
        return

    current = get_model()
    console.print("  [bold color(214)]AVAILABLE MODELS IN OLLAMA[/bold color(214)]")
    console.print("  " + "─"*52)

    if not models:
        console.print("  [dim]No models. Pull one: ollama pull gemma4:e4b[/dim]\n")
        return

    sys_ram = None
    try:
        import psutil
        sys_ram = psutil.virtual_memory().total / (1024**3)
    except ImportError:
        pass

    for m in models:
        is_cur  = current in m
        cur_lbl = " [color(214)]★ default[/color(214)]" if is_cur else ""
        needed  = estimate_model_ram(m)
        lbl     = f"~{needed}GB" if needed else "unknown"
        if sys_ram and needed:
            rc = "red" if needed > sys_ram*0.75 else "yellow" if needed > sys_ram*0.5 else "green"
        else:
            rc = "dim"
        console.print(
            f"  [white]{m:<38}[/white][{rc}]{lbl:<10}[/{rc}]{cur_lbl}")

    if sys_ram:
        console.print(f"\n  [dim]Your system RAM: {sys_ram:.1f}GB[/dim]")

    console.print()
    console.print("  [bold color(214)]RECOMMENDED BY RAM[/bold color(214)]")
    console.print("  " + "─"*52)
    for ram, rec in [
        ("4-8GB",  "gemma4:e4b, phi3:mini, llama3.2:3b"),
        ("16GB",   "llama3.1:8b, mistral:7b, deepseek-r1:8b"),
        ("32GB+",  "llama3.3:70b, deepseek-r1:32b, qwen2.5:32b"),
        ("GPU",    "Any model — GPU-accelerated via Ollama"),
    ]:
        console.print(f"  [color(214)]{ram:<10}[/color(214)] [dim]{rec}[/dim]")

    console.print(f"\n  [dim]Set default : vajra --set-model <name>[/dim]")
    console.print(f"  [dim]Pull a model: ollama pull <name>[/dim]\n")
