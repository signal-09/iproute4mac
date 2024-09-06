import json
import re

from os import system
from subprocess import check_output


_EN = None
_GW = None
_NET = "198.18.0.0/15"
_ROOT = "198.0.0.0/8"
_MATCH = "198.18.1.0/24"


def shell(cmd):
    return check_output(cmd, shell=True).decode().rstrip()


def setup_module(module):
    """setup any state specific to the execution of the given module"""
    globals()["_EN"] = shell("netstat -nr | awk '/^default/{ print $4 }' | head -1")
    globals()["_GW"] = shell("netstat -nr | awk '/^default/{ print $2 }' | head -1")
    shell(f"route add {_NET} -interface lo0")


def teardown_module(module):
    """teardown any state that was previously setup with a setup_module method"""
    shell(f"route delete {_NET} -interface lo0")


def test_ip_route_show(script_runner):
    checks = (
        # command, res.returncode, res.stdout, res.stderr
        ("ip route show", 0, r"\n", r"^$"),
        ("ip route show table all", 0, "default", r"Hint:"),
        ("ip -6 route show", 0, "fe80::/64", r"^$"),
        (f"ip route show dev {_EN}", 0, r"\n", r"^$"),
        ("ip route show src 127.0.0.1", 0, "127.0.0.0/8 via 127.0.0.1 dev lo0 proto static", r"^$"),
        (
            "ip route show src 127.0.0.0/8",
            0,
            "127.0.0.0/8 via 127.0.0.1 dev lo0 proto static src 127.0.0.1",
            r"^$",
        ),
        ("ip route show to default", 0, f"^default via .* dev {_EN}", r"^$"),
        (f"ip route show to root {_ROOT}", 0, f"{_NET} dev lo0", r"^$"),
        (f"ip route show to match {_MATCH}", 0, f"{_NET} dev lo0", r"^$"),
    )
    for cmd, ret, out, err in checks:
        res = script_runner.run(cmd.split())
        assert res.returncode == ret
        assert re.search(out, res.stdout)
        assert re.search(err, res.stderr)


def test_ip_route_modify(script_runner):
    checks = (
        # command, res.returncode, res.stdout, res.stderr
        (f"ip route add {_MATCH} dev lo0", 0, "^$", r"^$"),
        (f"ip route show to exact {_MATCH}", 0, f"^{_MATCH}", r"^$"),
        (f"ip route del {_MATCH} dev lo0", 0, "^$", r"^$"),
        (f"ip route add blackhole {_MATCH}", 0, "^$", r"^$"),
        ("ip route show type blackhole", 0, f"blackhole {_MATCH}", r"^$"),
        (f"ip route del blackhole {_MATCH}", 0, "^$", r"^$"),
    )
    for cmd, ret, out, err in checks:
        res = script_runner.run(cmd.split())
        assert res.returncode == ret
        assert re.search(out, res.stdout)
        assert re.search(err, res.stderr)
