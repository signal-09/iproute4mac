_OUT = None
_HOST = None
_DEV = None


def setup_module(module):
    """setup any state specific to the execution of the given module"""
    # How to create a STALE or FAILED ARP entry?
    pass


def teardown_module(module):
    """teardown any state that was previously setup with a setup_module method"""
    pass


def test_ip_neigh_show_unused(script_runner):
    # FIXME: how to be shure to find an unused entry?
    res = script_runner.run("ip neigh show unused".split())
    assert res.returncode == 0
    assert res.stderr == ""
    if res.stdout:
        globals()["_OUT"] = res.stdout.split("\n")[0]
        globals()["_HOST"] = _OUT.split()[0]
        globals()["_DEV"] = _OUT.split()[2]


def test_ip_neigh_delete(script_runner):
    if _HOST and _DEV:
        res = script_runner.run(f"ip neigh delete {_HOST} dev {_DEV}".split())
        assert res.returncode == 0
        assert res.stdout == ""
        assert res.stderr == ""


def test_ip_neigh_show_nud_reachable(script_runner):
    res = script_runner.run("ip neigh show nud reachable".split())
    assert res.returncode == 0
    assert res.stdout != ""
    assert res.stderr == ""
    globals()["_OUT"] = res.stdout.split("\n")[0]
    globals()["_HOST"] = _OUT.split()[0]
    globals()["_DEV"] = _OUT.split()[2]


def test_ip_neigh_get(script_runner):
    res = script_runner.run(f"ip neigh get {_HOST} dev {_DEV}".split())
    assert res.returncode == 0
    assert res.stdout == f"{_OUT}\n"
    assert res.stderr == ""
