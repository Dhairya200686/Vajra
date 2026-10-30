# VAJRA — CPU, RAM, swap, and disk usage. Cross-platform via psutil.


def get_resources() -> tuple:
    try:
        import psutil
    except ImportError:
        return {}, "[ERROR] psutil not installed. Run: pip install psutil"

    try:
        cpu_percent  = psutil.cpu_percent(interval=0.3)
        cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        vm   = psutil.virtual_memory()
        swap = psutil.swap_memory()

        disks = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "device":     part.device,
                    "mountpoint": part.mountpoint,
                    "fstype":     part.fstype,
                    "total_gb":   round(usage.total / (1024**3), 2),
                    "used_gb":    round(usage.used  / (1024**3), 2),
                    "free_gb":    round(usage.free  / (1024**3), 2),
                    "percent":    usage.percent,
                })
            except (PermissionError, OSError):
                continue

        return {
            "cpu_percent":   cpu_percent,
            "cpu_per_core":  cpu_per_core,
            "cpu_logical":   psutil.cpu_count(logical=True),
            "cpu_physical":  psutil.cpu_count(logical=False),
            "ram_total_gb":  round(vm.total / (1024**3), 2),
            "ram_used_gb":   round(vm.used  / (1024**3), 2),
            "ram_percent":   vm.percent,
            "swap_total_gb": round(swap.total / (1024**3), 2),
            "swap_used_gb":  round(swap.used  / (1024**3), 2),
            "swap_percent":  swap.percent,
            "disks":         disks,
        }, None
    except Exception as e:
        return {}, f"[ERROR] Could not gather resource info: {e}"
