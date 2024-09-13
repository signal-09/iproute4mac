import re

from os import system
from subprocess import check_output


_BRIDGE = None
_FETH = None
_LLADDR = "f0:e1:d2:c3:b4:a5"


def shell(cmd):
    return check_output(cmd, shell=True).decode().rstrip()


def setup_module(module):
    """setup any state specific to the execution of the given module"""
    globals()["_BRIDGE"] = shell("ifconfig bridge create")
    globals()["_FETH"] = shell("ifconfig feth create")
    shell(f"ifconfig {_BRIDGE} addm {_FETH}")
    shell(f"ifconfig {_BRIDGE} static {_FETH} {_LLADDR}")


def teardown_module(module):
    """teardown any state that was previously setup with a setup_module method"""
    if _FETH:
        shell(f"ifconfig {_FETH} destroy")
    if _BRIDGE:
        shell(f"ifconfig {_BRIDGE} destroy")


def test_bridge_fdb_show(script_runner):
    checks = (
        # command, res.returncode, res.stdout, res.stderr
        ("bridge fdb show", 0, f"{_LLADDR} dev {_FETH}", r"^$"),
    )
    for cmd, ret, out, err in checks:
        res = script_runner.run(cmd.split())
        assert res.returncode == ret
        assert re.search(out, res.stdout)
        assert re.search(err, res.stderr)
