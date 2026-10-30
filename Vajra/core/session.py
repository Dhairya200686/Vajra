# VAJRA — Session class and conversation memory management.
# Saved session files have detected secrets redacted before being written to disk.

from datetime import datetime
from pathlib  import Path
from core.config import SESSION_DIR


class Session:
    def __init__(self, mode: str = "default", model: str = None,
                 fc: str = "", fn: str = ""):
        from core.config  import get_model
        from llm.prompts  import MODES
        self._MODES  = MODES
        self.mode    = mode
        self.model   = model or get_model()
        self.history = []
        self.log     = []
        self.start   = datetime.now()
        self.count   = 0
        self.fc      = fc
        self.fn      = fn

    def messages(self, query: str) -> list:
        from llm.prompts import PROMPTS
        sys_p = PROMPTS[self.mode]
        if self.fc:
            sys_p += (
                f"\n\nLOADED FILE: {self.fn}\n{'─'*50}\n"
                f"{self.fc}\n{'─'*50}\n"
                f"Answer questions using this file's content."
            )
        msgs = [{"role": "system", "content": sys_p}]
        msgs += self.history
        msgs.append({"role": "user", "content": query})
        return msgs

    def add(self, query: str, response: str) -> None:
        self.history += [
            {"role": "user",      "content": query},
            {"role": "assistant", "content": response},
        ]
        if len(self.history) > 40:
            self.history = self.history[-40:]
        self.log.append({
            "time":  datetime.now().strftime("%H:%M:%S"),
            "mode":  self._MODES[self.mode]["label"],
            "model": self.model,
            "q":     query,
            "r":     response,
        })
        self.count += 1

    def save(self) -> Path:
        from security.secrets import redact
        ts   = self.start.strftime("%Y%m%d_%H%M%S")
        path = SESSION_DIR / f"session_{ts}.txt"
        lines = [
            "="*58,
            "  VAJRA (वज्र) v2.4.1 — Session Log",
            "="*58,
            f"  Started   : {self.start.strftime('%A, %d %B %Y at %H:%M:%S')}",
            f"  Ended     : {datetime.now().strftime('%H:%M:%S')}",
            f"  Exchanges : {self.count}",
            f"  Mode      : {self._MODES[self.mode]['label']}",
            f"  Model     : {self.model}",
        ]
        if self.fn:
            lines.append(f"  File      : {self.fn}")
        lines += ["="*58, ""]
        for i, e in enumerate(self.log, 1):
            lines += [
                f"[{i:02d}]  {e['time']}  {e['mode']}  {e['model']}",
                "-"*58,
                f"YOU   : {redact(e['q'])}", "",
                f"VAJRA : {redact(e['r'])}", "",
                "="*58, "",
            ]
        path.write_text("\n".join(lines), encoding="utf-8")
        return path
