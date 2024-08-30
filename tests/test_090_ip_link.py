import re

from os import system
from subprocess import check_output


_BRIDGE = None
_BOND = None
_PREFIX = "198.18.1.1/24"


def shell(cmd):
    return check_output(cmd, shell=True).decode().rstrip()


def setup_module(module):
    """setup any state specific to the execution of the given module"""
    globals()["_BRIDGE"] = shell("ifconfig bridge create")
    globals()["_BOND"] = shell("ifconfig bond create")


def teardown_module(module):
    """teardown any state that was previously setup with a setup_module method"""
    if _BRIDGE:
        shell(f"ifconfig {_BRIDGE} destroy")
    if _BOND:
        shell(f"ifconfig {_BOND} destroy")


def test_ip_link_show(script_runner):
    checks = (
        # command, res.returncode, res.stdout, res.stderr
        ("ip link show", 0, r"link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00", r"^$"),
        ("ip link show dev lo0", 0, r"^1: lo0", r"^$"),
        ("ip link show type bridge", 0, rf": {_BRIDGE}:", r"^$"),
        ("ip link show type bond", 0, rf": {_BOND}:", r"^$"),
    )
    for cmd, ret, out, err in checks:
        res = script_runner.run(cmd.split())
        assert res.returncode == ret
        assert re.search(out, res.stdout)
        assert re.search(err, res.stderr)
