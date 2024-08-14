from os import system
from subprocess import check_output


_BOND = False
_BOND_ID = 777
_FETH1 = None
_FETH2 = None


def shell(cmd):
    return check_output(cmd, shell=True).decode().rstrip()


def setup_module(module):
    """setup any state specific to the execution of the given module"""
    globals()["_FETH1"] = check_output("sudo ifconfig feth create", shell=True).decode().rstrip()
    globals()["_FETH2"] = check_output("sudo ifconfig feth create", shell=True).decode().rstrip()
    pass


def teardown_module(module):
    """teardown any state that was previously setup with a setup_module method"""
    if _BOND:
        system(f"sudo ifconfig bridge{_BOND_ID} destroy")
    if _FETH1:
        system(f"sudo ifconfig {_FETH1} destroy")
    if _FETH2:
        system(f"sudo ifconfig {_FETH2} destroy")


def test_ip_link_add_bridge(script_runner):
    res = script_runner.run(f"sudo ip link add name bridge{_BOND_ID} type bridge".split())
    globals()["_BOND"] = res.returncode == 0
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""


def test_ip_link_set_master(script_runner):
    res = script_runner.run(f"sudo ip link set {_FETH1} master bridge{_BOND_ID}".split())
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""

    res = script_runner.run(f"sudo ip link set {_FETH2} master bridge{_BOND_ID}".split())
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""


def test_ip_link_set_nomaster(script_runner):
    res = script_runner.run(f"sudo ip link set {_FETH1} nomaster".split())
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""

    res = script_runner.run(f"sudo ip link set {_FETH2} nomaster".split())
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""


def test_ip_link_del_bridge(script_runner):
    res = script_runner.run(f"sudo ip link del bridge{_BOND_ID}".split())
    globals()["_BOND"] = not (res.returncode == 0)
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""
