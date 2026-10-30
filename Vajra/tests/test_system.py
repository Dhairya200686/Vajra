# VAJRA — System intelligence module unit tests.

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from system.info      import get_system_info
from system.resources import get_resources
from system.network   import get_network_info
from system.processes import top_processes


def test_system_info_returns_os():
    info, err = get_system_info()
    assert err is None
    assert "os" in info
    assert isinstance(info["os"], str) and len(info["os"]) > 0


def test_resources_returns_cpu_percent():
    res, err = get_resources()
    assert err is None
    assert "cpu_percent" in res
    assert isinstance(res["cpu_percent"], (int, float))


def test_resources_returns_disks_list():
    res, err = get_resources()
    assert err is None
    assert isinstance(res["disks"], list)


def test_network_returns_interfaces():
    net, err = get_network_info()
    assert err is None
    assert "interfaces" in net
    assert isinstance(net["interfaces"], dict)


def test_top_processes_returns_list():
    procs, err = top_processes(n=5)
    assert err is None
    assert isinstance(procs, list)
    assert len(procs) <= 5


def test_snapshot_to_context_produces_string():
    from system import get_full_snapshot, snapshot_to_context
    snap    = get_full_snapshot()
    context = snapshot_to_context(snap)
    assert isinstance(context, str)
    assert "SYSTEM INFORMATION" in context
