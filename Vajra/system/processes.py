# VAJRA — Running process inspection. Cross-platform via psutil.

import time


def top_processes(n: int = 10, by: str = "cpu") -> tuple:
    try:
        import psutil
    except ImportError:
        return [], "[ERROR] psutil not installed. Run: pip install psutil"

    try:
        procs = list(psutil.process_iter(["pid", "name"]))
        for p in procs:
            try:
                p.cpu_percent(None)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        time.sleep(0.3)

        results = []
        for p in procs:
            try:
                results.append({
                    "pid":  p.pid,
                    "name": p.name(),
                    "cpu":  p.cpu_percent(None),
                    "mem":  round(p.memory_percent(), 2),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        key = "cpu" if by == "cpu" else "mem"
        results.sort(key=lambda x: x[key], reverse=True)
        return results[:n], None
    except Exception as e:
        return [], f"[ERROR] Could not list processes: {e}"


def find_process(name_query: str) -> tuple:
    try:
        import psutil
    except ImportError:
        return [], "[ERROR] psutil not installed. Run: pip install psutil"

    try:
        matches = []
        for p in psutil.process_iter(["pid", "name"]):
            try:
                if name_query.lower() in (p.info["name"] or "").lower():
                    matches.append({"pid": p.pid, "name": p.info["name"]})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return matches, None
    except Exception as e:
        return [], f"[ERROR] Could not search processes: {e}"
