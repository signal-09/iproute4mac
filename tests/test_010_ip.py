import iproute4mac


def test_ip_version(script_runner):
    for opt in ["--Version", "-Version", "-V"]:
        res = script_runner.run(["ip", opt])
        assert res.returncode == 0
        assert res.stderr == ""
        assert res.stdout == f"ip wrapper, iproute4mac-{iproute4mac.VERSION}\n"


def test_ip_help(script_runner):
    for opt in ["help", "--help", "-help", "-h"]:
        res = script_runner.run(["ip", opt])
        assert res.returncode == 255
        assert res.stderr.startswith("Usage:")


def test_ip_obj_help(script_runner):
    for obj in ["link", "address", "route", "neigh"]:
        res = script_runner.run(["ip", obj, "help"])
        assert res.returncode == 255
        assert res.stderr.startswith(f"Usage: ip {obj}")
