# VAJRA — Cross-platform system identity information.

import platform
import socket
from datetime import datetime


def get_system_info() -> tuple:
    try:
        boot_time_str, uptime_str = _boot_and_uptime()
        info = {
            "os":             platform.system(),
            "os_release":     platform.release(),
            "os_version":     platform.version(),
            "architecture":   platform.machine(),
            "hostname":       socket.gethostname(),
            "python_version": platform.python_version(),
            "boot_time":      boot_time_str,
            "uptime":         uptime_str,
        }
        return info, None
    except Exception as e:
        return {}, f"[ERROR] Could not gather system info: {e}"


def _boot_and_uptime() -> tuple:
    try:
        import psutil
        boot_ts  = psutil.boot_time()
        boot_str = datetime.fromtimestamp(boot_ts).strftime("%Y-%m-%d %H:%M:%S")
        seconds  = datetime.now().timestamp() - boot_ts
        return boot_str, _format_uptime(seconds)
    except Exception:
        return "unknown", "unknown"


def _format_uptime(seconds: float) -> str:
    seconds     = max(0, int(seconds))
    days, rem   = divmod(seconds, 86400)
    hours, rem  = divmod(rem, 3600)
    minutes, _  = divmod(rem, 60)
    parts = []
    if days:  parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)
