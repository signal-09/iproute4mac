from os import system
from subprocess import check_output


_EN = None
_VLAN = None
_VLAN_ID = 777
_VLAN_IP = "10.7.7.7"


def shell(cmd):
    return check_output(cmd, shell=True).decode().rstrip()


def setup_module(module):
    """setup any state specific to the execution of the given module"""
    globals()["_EN"] = shell("netstat -nr -f inet | awk '/default/{ print $4 }' | head -1")


def teardown_module(module):
    """teardown any state that was previously setup with a setup_module method"""
    if _VLAN:
        system(f"ifconfig {_VLAN} destroy")


def test_ip_link_add_vlan(script_runner):
    res = script_runner.run(f"ip link add link {_EN} type vlan id {_VLAN_ID}".split())
    globals()["_VLAN"] = res.stdout.rstrip()
    assert res.returncode == 0
    assert res.stdout.startswith("vlan")
    assert res.stderr == ""

    res = script_runner.run(f"ip link add link {_EN} name {_VLAN} type vlan id {_VLAN_ID}".split())
    # assert res.returncode == 2
    assert res.returncode == 1
    assert res.stdout == ""
    # assert res.stderr == "RTNETLINK answers: File exists\n"
    assert res.stderr == "ifconfig: SIOCIFCREATE2: File exists\n"


def test_ip_addr_add(script_runner):
    res = script_runner.run(f"ip addr add {_VLAN_IP}/24 brd + dev {_VLAN}".split())
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""

    res = script_runner.run(f"ip addr add {_VLAN_IP}/24 brd + dev {_VLAN}".split())
    # assert res.returncode == 2
    assert res.returncode == 0
    assert res.stdout == ""
    # assert res.stderr == "RTNETLINK answers: File exists\n"
    assert res.stderr == ""


def test_ip_link_del_vlan(script_runner):
    res = script_runner.run(f"ip link del {_VLAN}".split())
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""

    res = script_runner.run(f"ip link del {_VLAN}".split())
    assert res.returncode == 1
    assert res.stdout == ""
    assert res.stderr == f'Cannot find device "{_VLAN}"\n'
    globals()["_VLAN"] = None
