# VAJRA — Ollama HTTP client. Shows a live word-count spinner while
# generating, then renders the complete response as formatted markdown in
# a single pass once streaming finishes.
#
# An earlier version tried to live-render the growing markdown response as
# it streamed, using Rich's Live display. That caused a real bug: once a
# response grew taller than the terminal window, Rich's redraw-in-place
# logic started fighting with the terminal's own scrollback, producing
# duplicated or glitched output when scrolling up. The fix is to keep live
# redrawing confined to something that can never exceed one line (the
# spinner), and print the actual response once, in full, when it's ready.

import json
import requests
from core.logger import get_logger

logger      = get_logger("vajra.llm")
OLLAMA_URL  = "http://localhost:11434/api/chat"
TIMEOUT     = 120
MIN_WORDS   = 25
MAX_RETRIES = 2


def stream(messages: list, model: str = None, _retries: int = 0) -> str:
    from rich.console  import Console
    from rich.markdown import Markdown
    from core.config   import get_model
    console = Console()
    model   = model or get_model()

    payload = {
        "model":    model,
        "messages": messages,
        "stream":   True,
        "options":  {"num_predict": 3500, "temperature": 0.72},
    }
    full  = []
    count = 0

    try:
        with requests.post(OLLAMA_URL, json=payload,
                           stream=True, timeout=TIMEOUT) as r:
            if r.status_code != 200:
                logger.error("Ollama HTTP %s", r.status_code)
                console.print(f"\n  [red][ERROR] Ollama HTTP {r.status_code}[/red]\n")
                return ""

            with console.status("[dim]VAJRA is thinking...[/dim]", spinner="dots") as status:
                for line in r.iter_lines():
                    if not line:
                        continue
                    try:
                        data  = json.loads(line)
                        token = data.get("message", {}).get("content", "")
                        if token:
                            full.append(token)
                            count += 1
                            if count % 5 == 0:
                                wc = len("".join(full).split())
                                status.update(f"[dim]VAJRA is writing... ({wc} words)[/dim]")
                        if data.get("done"):
                            break
                    except Exception:
                        continue

    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to Ollama")
        console.print("\n  [red][ERROR] Cannot connect to Ollama.[/red]")
        console.print("  [dim]Run: ollama serve[/dim]\n")
        return ""
    except requests.exceptions.Timeout:
        logger.warning("Ollama request timed out")
        console.print("\n  [red][TIMEOUT] Try again or use a smaller model.[/red]\n")
        return ""
    except KeyboardInterrupt:
        console.print("\n\n  [yellow][STOPPED][/yellow]\n")
        return "".join(full)

    result = "".join(full)

    if len(result.split()) < MIN_WORDS and _retries < MAX_RETRIES:
        logger.debug("Response too short — retry %s/%s", _retries + 1, MAX_RETRIES)
        console.print(f"\n  [dim]Elaborating... ({_retries + 1}/{MAX_RETRIES})[/dim]\n")
        messages.append({"role": "assistant", "content": result})
        messages.append({"role": "user",
                         "content": "Please elaborate with significantly more depth and detail."})
        return stream(messages, model, _retries=_retries + 1)

    console.print()
    console.print(Markdown(result))

    return result
