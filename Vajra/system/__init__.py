# VAJRA — System intelligence dispatcher and context formatter.

from system.info      import get_system_info
from system.resources import get_resources
from system.network   import get_network_info
from system.processes import top_processes


def get_full_snapshot() -> dict:
    info,  e1 = get_system_info()
    res,   e2 = get_resources()
    net,   e3 = get_network_info()
    procs, e4 = top_processes(n=8, by="cpu")
    return {
        "info":          info,
        "resources":     res,
        "network":       net,
        "top_processes": procs,
        "errors":        [e for e in (e1, e2, e3, e4) if e],
    }


def snapshot_to_context(snapshot: dict) -> str:
    lines = []
    info = snapshot.get("info", {}) or {}
    lines.append("SYSTEM INFORMATION:")
    lines.append(f"  OS: {info.get('os','?')} {info.get('os_release','')} "
                f"({info.get('architecture','?')})")
    lines.append(f"  Hostname: {info.get('hostname','?')}")
    lines.append(f"  Uptime: {info.get('uptime','?')} "
                f"(booted {info.get('boot_time','?')})")
    lines.append("")

    res = snapshot.get("resources", {}) or {}
    lines.append("RESOURCES:")
    lines.append(f"  CPU: {res.get('cpu_percent','?')}% used "
                f"({res.get('cpu_physical','?')} physical / "
                f"{res.get('cpu_logical','?')} logical cores)")
    lines.append(f"  RAM: {res.get('ram_used_gb','?')}GB / "
                f"{res.get('ram_total_gb','?')}GB ({res.get('ram_percent','?')}%)")
    lines.append(f"  Swap: {res.get('swap_used_gb','?')}GB / "
                f"{res.get('swap_total_gb','?')}GB ({res.get('swap_percent','?')}%)")
    for d in res.get("disks", []) or []:
        lines.append(f"  Disk {d['mountpoint']}: {d['used_gb']}GB / "
                    f"{d['total_gb']}GB ({d['percent']}%)")
    lines.append("")

    net = snapshot.get("network", {}) or {}
    lines.append("NETWORK:")
    for iface, data in (net.get("interfaces", {}) or {}).items():
        status = "up" if data.get("up") else "down"
        ips    = ", ".join(data.get("ips", [])) or "no IP"
        lines.append(f"  {iface} ({status}): {ips}")
    lp = net.get("listening_ports")
    if lp:
        addrs = ", ".join(p["addr"] for p in lp[:15])
        lines.append(f"  Listening ports: {addrs}")
    elif lp is None:
        lines.append("  Listening ports: unavailable (needs elevated permission)")
    lines.append("")

    lines.append("TOP PROCESSES (by CPU):")
    for p in snapshot.get("top_processes", []) or []:
        lines.append(f"  PID {p['pid']:<7} {p['name']:<25} "
                    f"CPU {p['cpu']:.1f}%  MEM {p['mem']:.1f}%")

    if snapshot.get("errors"):
        lines.append("")
        lines.append("NOTE: Some data unavailable:")
        for e in snapshot["errors"]:
            lines.append(f"  {e}")

    return "\n".join(lines)
