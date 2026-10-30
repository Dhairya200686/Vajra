# VAJRA — Service status checks. Platform-specific backend, common interface.
# Read-only operations only — never starts, stops, or modifies a service.

import platform
import subprocess


def check_service(name: str) -> tuple:
    system = platform.system()
    try:
        if system == "Linux":
            return _check_linux(name)
        elif system == "Windows":
            return _check_windows(name)
        elif system == "Darwin":
            return _check_macos(name)
        else:
            return None, f"[ERROR] Unsupported platform: {system}"
    except Exception as e:
        return None, f"[ERROR] Could not check service: {e}"


def _check_linux(name: str) -> tuple:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", name],
            capture_output=True, text=True, timeout=5)
        status = result.stdout.strip() or "unknown"
        return {"name": name, "status": status, "platform": "linux"}, None
    except FileNotFoundError:
        return None, "[ERROR] systemctl not found on this system."
    except subprocess.TimeoutExpired:
        return None, "[ERROR] Service check timed out."


def _check_windows(name: str) -> tuple:
    try:
        result = subprocess.run(
            ["sc", "query", name],
            capture_output=True, text=True, timeout=5)
        output = result.stdout
        status = "unknown"
        if "RUNNING" in output: status = "running"
        elif "STOPPED" in output: status = "stopped"
        return {"name": name, "status": status, "platform": "windows"}, None
    except FileNotFoundError:
        return None, "[ERROR] sc command not found."
    except subprocess.TimeoutExpired:
        return None, "[ERROR] Service check timed out."


def _check_macos(name: str) -> tuple:
    try:
        result = subprocess.run(
            ["launchctl", "list", name],
            capture_output=True, text=True, timeout=5)
        status = "running" if result.returncode == 0 else "not found / stopped"
        return {"name": name, "status": status, "platform": "macos"}, None
    except FileNotFoundError:
        return None, "[ERROR] launchctl not found."
    except subprocess.TimeoutExpired:
        return None, "[ERROR] Service check timed out."
