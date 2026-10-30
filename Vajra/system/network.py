# VAJRA — Network interfaces, IPs, and listening ports. Cross-platform via psutil.


def get_network_info() -> tuple:
    try:
        import psutil
    except ImportError:
        return {}, "[ERROR] psutil not installed. Run: pip install psutil"

    try:
        info = {"interfaces": {}, "listening_ports": None}

        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        for iface, addr_list in addrs.items():
            ips = [a.address for a in addr_list
                  if a.family.name in ("AF_INET", "AF_INET6")]
            up  = stats[iface].isup if iface in stats else None
            info["interfaces"][iface] = {"ips": ips, "up": up}

        try:
            conns     = psutil.net_connections(kind="inet")
            listening = []
            for c in conns:
                if c.status == psutil.CONN_LISTEN:
                    laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "?"
                    listening.append({"addr": laddr, "pid": c.pid})
            info["listening_ports"] = listening
        except Exception:
            info["listening_ports"] = None

        return info, None
    except Exception as e:
        return {}, f"[ERROR] Could not gather network info: {e}"
