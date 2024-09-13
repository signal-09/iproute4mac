import re

from os import system
from subprocess import check_output


_BRIDGE = None
_FETH = None


def shell(cmd):
    return check_output(cmd, shell=True).decode().rstrip()


def setup_module(module):
    """setup any state specific to the execution of the given module"""
    globals()["_BRIDGE"] = shell("ifconfig bridge create")
    globals()["_FETH"] = shell("ifconfig feth create")
    shell(f"ifconfig {_BRIDGE} addm {_FETH}")


def teardown_module(module):
    """teardown any state that was previously setup with a setup_module method"""
    if _FETH:
        shell(f"ifconfig {_FETH} destroy")
    if _BRIDGE:
        shell(f"ifconfig {_BRIDGE} destroy")


def test_bridge_link_show(script_runner):
    checks = (
        # command, res.returncode, res.stdout, res.stderr
        ("bridge link show", 0, f": {_FETH}:.* master {_BRIDGE} state", r"^$"),
        ("bridge -d link show", 0, f": {_BRIDGE}:.* master {_BRIDGE}\n", r"^$"),
    )
    for cmd, ret, out, err in checks:
        res = script_runner.run(cmd.split())
        assert res.returncode == ret
        assert re.search(out, res.stdout)
        assert re.search(err, res.stderr)
