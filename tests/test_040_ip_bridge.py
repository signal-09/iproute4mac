from os import system
from subprocess import check_output


_BRIDGE = None
_FETH1 = None
_FETH2 = None


def shell(cmd):
    return check_output(cmd, shell=True).decode().rstrip()


def setup_module(module):
    """setup any state specific to the execution of the given module"""
    globals()["_FETH1"] = shell("ifconfig feth create")
    globals()["_FETH2"] = shell("ifconfig feth create")


def teardown_module(module):
    """teardown any state that was previously setup with a setup_module method"""
    if _BRIDGE:
        system(f"ifconfig {_BRIDGE} destroy")
    if _FETH1:
        system(f"ifconfig {_FETH1} destroy")
    if _FETH2:
        system(f"ifconfig {_FETH2} destroy")


def test_ip_link_add_bridge(script_runner):
    res = script_runner.run("ip link add type bridge".split())
    globals()["_BRIDGE"] = res.stdout.rstrip()
    assert res.returncode == 0
    assert res.stdout.startswith(_BRIDGE)
    assert res.stderr == ""


def test_ip_link_set_master(script_runner):
    res = script_runner.run(f"ip link set {_FETH1} master {_BRIDGE}".split())
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""

    res = script_runner.run(f"ip link set {_FETH2} master {_BRIDGE}".split())
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""


def test_ip_link_set_nomaster(script_runner):
    res = script_runner.run(f"ip link set {_FETH1} nomaster".split())
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""

    res = script_runner.run(f"ip link set {_FETH2} nomaster".split())
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""


def test_ip_link_del_bridge(script_runner):
    res = script_runner.run(f"ip link del {_BRIDGE}".split())
    if res.returncode == 0:
        globals()["_BRIDGE"] = None
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""