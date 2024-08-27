from os import system


_LAN = "198.18.0.0/15"
_FETH1 = None
_FETH2 = None
_FETH1_IP = "198.18.0.1/15"
_FETH2_IP = "198.18.0.2/15"


def setup_module(module):
    """setup any state specific to the execution of the given module"""
    pass


def teardown_module(module):
    """teardown any state that was previously setup with a setup_module method"""
    if _FETH1:
        system(f"ifconfig {_FETH1} destroy")
    if _FETH2:
        system(f"ifconfig {_FETH2} destroy")


def test_ip_link_add_feth(script_runner):
    res = script_runner.run("ip link add type feth".split())
    globals()["_FETH1"] = res.stdout.rstrip()
    assert res.returncode == 0
    assert res.stdout.startswith(_FETH1)
    assert res.stderr == ""

    res = script_runner.run(f"ip addr add {_FETH1_IP} brd + dev {_FETH1}".split())
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""

    res = script_runner.run("ip link add type feth".split())
    globals()["_FETH2"] = res.stdout.rstrip()
    assert res.returncode == 0
    assert res.stdout.startswith(_FETH2)
    assert res.stderr == ""

    res = script_runner.run(f"ip addr add {_FETH2_IP} brd + dev {_FETH2}".split())
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""

    res = script_runner.run(f"ip link add name {_FETH1} type feth".split())
    # assert res.returncode == 2
    assert res.returncode == 1
    assert res.stdout == ""
    # assert res.stderr == 'RTNETLINK answers: File exists\n'
    assert res.stderr == "ifconfig: SIOCIFCREATE2: File exists\n"


def test_ip_link_del_feth(script_runner):
    res = script_runner.run(f"ip link del {_FETH1}".split())
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""

    res = script_runner.run(f"ip link del {_FETH2}".split())
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""


def test_ip_link_peer_feth(script_runner):
    res = script_runner.run(f"ip link add name {_FETH1} type feth peer {_FETH2}".split())
    assert res.returncode == 0
    assert res.stdout == ""
    assert res.stderr == ""
